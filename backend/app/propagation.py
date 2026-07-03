import asyncio
import logging
from typing import List, Dict, Optional, Tuple

from app.models import (
    EventRecord,
    BeliefRecord,
    NpcState,
    FactionMood,
    Location,
    Faction,
    ActionType,
    RelationshipType,
)
from app.game_state import GameStateManager
from app.cognee_client import CogneeClient
from app.world_data import PROPAGATION_RULES, ACTION_EFFECTS

logger = logging.getLogger(__name__)


class PropagationEngine:
    """Determines how memory spreads through the social graph.

    When an NPC witnesses an event, this engine:
    1. Determines who that NPC talks to (based on social edges)
    2. Creates belief records for each informed NPC
    3. Updates NPC sentiment based on the event type
    4. Writes propagation edges to Cognee
    5. Updates faction moods

    The propagation is EXPLICIT and TRACEABLE — every belief has a source
    and certainty value. No magical memory.
    """

    def __init__(self, game_state: GameStateManager, cognee: CogneeClient):
        self.gs = game_state
        self.cognee = cognee

    async def propagate_event(self, event: EventRecord):
        """Propagate an event through the social graph.

        This method:
        1. Records the event in public and per-NPC Cognee datasets
        2. Propagates through social edges to connected NPCs
        3. Updates NPC sentiment (trust/fear/respect/anger)
        4. Updates faction moods
        5. Stores propagation edges in Cognee for traceability

        All Cognee calls are async and non-blocking for the game loop.
        """
        # Step 1: Store event in public dataset (canonical record)
        event_text = self._event_to_text(event)
        await self.cognee.store_event(
            event_text,
            dataset_name="echo_public",
            session_id=self.gs.session_id,
        )

        # Step 2: Store event in each witness's personal dataset
        for witness_name in event.witnesses:
            await self._store_event_for_npc(event, witness_name, "witnessed")
            await self._store_graph_provenance(witness_name, event, "witnessed")

            # Create belief record for the witness
            witness_belief = BeliefRecord(
                npc_name=witness_name,
                event_id=event.event_id,
                certainty=1.0,
                source="witnessed",
                heard_from=None,
            )
            self.gs.add_belief(witness_name, witness_belief)

            # Step 3: Propagate from witness to connected NPCs
            connected = self.gs.get_npcs_for_propagation(witness_name, event.event_id)
            for connected_npc in connected:
                await self._propagate_to_npc(event, witness_name, connected_npc)

        # Step 4: Update NPC sentiment based on event type
        self._update_npc_sentiment(event)

        # Step 5: Update faction moods
        self._update_faction_moods(event)

    async def _store_event_for_npc(
        self, event: EventRecord, npc_name: str, source: str
    ):
        """Store an event in a specific NPC's Cognee dataset.

        The event text includes the NPC's perspective so Cognee's LLM extraction
        can create the correct graph nodes and edges for this NPC's knowledge.
        """
        dataset = f"echo_{npc_name.lower()}"
        perspective_text = self._event_from_perspective(event, npc_name, source)
        await self.cognee.store_event(perspective_text, dataset_name=dataset)

        # Also create a structured belief edge
        summary = self._event_summary(event)
        certainty_label = "high" if source == "witnessed" else "medium"
        belief_text = (
            f"[BELIEF] {npc_name} "
            f"{'saw' if source == 'witnessed' else 'was told by ' + source} "
            f"that {summary}. Certainty: {certainty_label}."
        )
        await self.cognee.store_event(belief_text, dataset_name=dataset)

    async def _store_graph_provenance(
        self, npc_name: str, event: EventRecord, source: str
    ):
        """Store a structured graph edge in Cognee for the visualization panel.

        These edges power the 'who knows what and why' visualization.
        """
        await self.cognee.store_graph_edge(
            npc_name,
            source,
            event.event_id,
            dataset_name=f"echo_{npc_name.lower()}",
        )

    async def _propagate_to_npc(
        self, event: EventRecord, from_npc: str, to_npc: str
    ):
        """Propagate an event from one NPC to another through a social edge.

        The propagated belief has:
        - Lower certainty than the original witness (hearsay)
        - Source set to the NPC who told them
        - Emotional impact scaled by the relationship trust level
        """
        # Find the relationship between the two NPCs
        rel_type: Optional[RelationshipType] = None
        trust = 0
        for connected, rt, tl in self.gs.get_connected_npcs(from_npc):
            if connected == to_npc:
                rel_type = rt
                trust = tl
                break

        if rel_type is None:
            return

        # Apply propagation rules
        rules = PROPAGATION_RULES.get(rel_type)
        if rules is None:
            # Rivals do not propagate — no rules defined for them
            return

        # Calculate certainty based on relationship trust and propagation rules
        certainty = (trust / 100.0) * rules["certainty_multiplier"]
        if rel_type == RelationshipType.ally:
            certainty = max(certainty, 0.5)

        # Create belief record
        belief = BeliefRecord(
            npc_name=to_npc,
            event_id=event.event_id,
            certainty=round(certainty, 2),
            source="told",
            heard_from=from_npc,
        )
        self.gs.add_belief(to_npc, belief)

        # Store in Cognee
        await self._store_event_for_npc(event, to_npc, from_npc)
        await self._store_graph_provenance(to_npc, event, f"told_by_{from_npc}")

        # Scale emotional impact based on relationship trust
        self._apply_hearsay_sentiment(event, to_npc, certainty, trust)

        logger.info(
            f"Propagated {event.event_id} from {from_npc} to {to_npc} "
            f"(certainty={certainty}, trust={trust})"
        )

    def _update_npc_sentiment(self, event: EventRecord):
        """Update NPC emotional states based on the event.

        Witnesses feel the full effect. Non-witnesses who were told feel a
        scaled effect based on their certainty and relationship trust.
        """
        effects = ACTION_EFFECTS.get(event.action_type.value, {})
        if not effects:
            return

        for npc_name in event.witnesses:
            npc = self.gs.npcs.get(npc_name)
            if npc:
                self._apply_sentiment_change(npc, effects, scale=1.0)

    def _apply_hearsay_sentiment(
        self, event: EventRecord, npc_name: str, certainty: float, trust: int
    ):
        """Apply a scaled sentiment change for hearsay knowledge.

        An NPC who was told about an event feels less strongly than one who
        witnessed it. The emotional impact is scaled by:
        - certainty (how sure they are the event happened)
        - trust (how much they trust the source)
        """
        effects = ACTION_EFFECTS.get(event.action_type.value, {})
        if not effects:
            return

        npc = self.gs.npcs.get(npc_name)
        if npc:
            scale = certainty * (trust / 100.0)
            self._apply_sentiment_change(npc, effects, scale=scale)

    def _apply_sentiment_change(self, npc: NpcState, effects: dict, scale: float):
        """Apply sentiment changes to an NPC, clamped to 0-100."""
        npc.trust = max(0, min(100, npc.trust + int(effects.get("trust", 0) * scale)))
        npc.fear = max(0, min(100, npc.fear + int(effects.get("fear", 0) * scale)))
        npc.respect = max(
            0, min(100, npc.respect + int(effects.get("respect", 0) * scale))
        )
        npc.anger = max(
            0, min(100, npc.anger + int(effects.get("anger", 0) * scale))
        )

    def _update_faction_moods(self, event: EventRecord):
        """Update faction aggregate moods based on the event.

        Faction moods are calculated as the average of all members' sentiments.
        """
        for faction_name, mood in self.gs.factions.items():
            try:
                faction = Faction(faction_name)
            except ValueError:
                continue

            members = [
                n for n, s in self.gs.npcs.items() if s.faction == faction
            ]

            if not members:
                continue

            # Calculate average sentiment of faction members
            avg_trust = sum(self.gs.npcs[m].trust for m in members) / len(members)
            avg_fear = sum(self.gs.npcs[m].fear for m in members) / len(members)
            avg_respect = sum(self.gs.npcs[m].respect for m in members) / len(members)
            avg_anger = sum(self.gs.npcs[m].anger for m in members) / len(members)

            mood.trust = round(avg_trust)
            mood.fear = round(avg_fear)
            mood.respect = round(avg_respect)
            mood.anger = round(avg_anger)
            mood.last_event = event.event_id

    def _event_to_text(self, event: EventRecord) -> str:
        """Convert an event to a natural language sentence for Cognee ingestion.

        Cognee's cognify pipeline will extract (subject, relation, object)
        triplets from this text and create graph nodes+edges automatically.
        """
        item_part = f" {event.item}" if event.item else ""
        desc_part = f" {event.description}" if event.description else ""
        return (
            f"[EVENT {event.event_id}] The player performed '{event.action_type.value}'"
            f" targeting {event.target_npc}{item_part} at {event.location.value}."
            f" Witnesses: {', '.join(event.witnesses)}.{desc_part}"
        )

    def _event_from_perspective(
        self, event: EventRecord, npc_name: str, source: str
    ) -> str:
        """Describe an event from a specific NPC's perspective.

        This creates a more natural memory for the NPC, including their
        relationship to the event and their level of certainty.
        """
        item_part = f" {event.item}" if event.item else ""
        if source == "witnessed":
            return (
                f"[EVENT {event.event_id}] I saw the player {event.action_type.value}"
                f"{item_part}"
                f" involving {event.target_npc} at {event.location.value}."
                f" I am certain about what I saw."
            )
        else:
            return (
                f"[EVENT {event.event_id}] I heard from {source} that the player"
                f" {event.action_type.value}"
                f"{item_part}"
                f" involving {event.target_npc}. I am less certain since I did not see it."
            )

    def _event_summary(self, event: EventRecord) -> str:
        item_part = f" {event.item}" if event.item else ""
        return (
            f"the player {event.action_type.value}"
            f"{item_part} involving {event.target_npc}"
        )
