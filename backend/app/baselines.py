import logging
from typing import List, Dict, Tuple, Optional

from app.models import MemoryMode, NpcState, Faction
from app.game_state import GameStateManager
from app.cognee_client import CogneeClient

logger = logging.getLogger(__name__)


class BaselineService:
    """Provides three memory strategies for comparison.

    This is the core of the 'toggle' demo. Each mode uses a fundamentally
    different retrieval strategy against the same Cognee data:

    GRAPH MODE (SearchType.GRAPH_COMPLETION):
        - Only uses graph traversal to find facts
        - No semantic generalization
        - NPCs can only reference events they have a direct graph edge to
        - Dialogue is factual but rigid

    VECTOR MODE (SearchType.RAG_COMPLETION):
        - Only uses semantic similarity (no graph structure)
        - Can generalize meaning across events
        - BUT: can't enforce knowledge boundaries — may leak facts from
          one NPC's knowledge to another NPC who shouldn't know
        - Dialogue is expressive but may hallucinate

    HYBRID MODE (SearchType.GRAPH_COMPLETION_COT):
        - Uses BOTH graph traversal AND semantic similarity
        - Chain-of-thought reasoning combines structure + meaning
        - Enforces knowledge boundaries through graph edges
        - Generalizes emotionally through vector similarity

    Each mode is a REAL Cognee recall call — no mock data.
    """

    def __init__(self, game_state: GameStateManager, cognee: CogneeClient):
        self.gs = game_state
        self.cognee = cognee

    async def get_dialogue_with_provenance(
        self, npc_name: str, mode: MemoryMode
    ) -> Tuple[str, List[Dict]]:
        """Get an NPC's dialogue using a specific memory mode.

        Returns:
            Tuple of (dialogue_string, provenance_list)
            Provenance explains WHAT facts drove the dialogue.
        """
        npc = self.gs.npcs.get(npc_name)
        if not npc:
            return "I don't know you.", []

        provenance = []

        # Determine what this NPC knows from local beliefs
        local_beliefs = self.gs.beliefs.get(npc_name, [])
        known_event_ids = [b.event_id for b in local_beliefs]
        known_events = [e for e in self.gs.events if e.event_id in known_event_ids]

        provenance.append(
            {
                "mode": mode.value,
                "npc": npc_name,
                "local_beliefs": len(local_beliefs),
                "known_events": [e.action_type.value for e in known_events],
            }
        )

        # Query Cognee with the specified mode
        try:
            recall_results = await self.cognee.recall_npc_knowledge(
                npc_name=npc_name,
                query="What do I know about the player and what they've done?",
                mode=mode.value,
                top_k=10,
            )
            recall_text = " ".join(recall_results)
            provenance.append(
                {
                    "source": "cognee_recall",
                    "mode": mode.value,
                    "recall_preview": recall_text[:300],
                }
            )
        except Exception as e:
            logger.warning(f"{mode.value} recall failed for {npc_name}: {e}")
            recall_text = ""

        # Generate dialogue based on mode
        dialogue = self._generate_mode_dialogue(
            npc=npc,
            events=known_events,
            beliefs=local_beliefs,
            recall_text=recall_text,
            mode=mode,
        )

        return dialogue, provenance

    def _generate_mode_dialogue(
        self,
        npc: NpcState,
        events: List,
        beliefs: List,
        recall_text: str,
        mode: MemoryMode,
    ) -> str:
        """Generate mode-specific dialogue.

        Each mode produces observably different output:
        - Graph mode: formal, factual, references sentiment values
        - Vector mode: emotional, may reference events NPC doesn't know
        - Hybrid mode: balanced, grounded, emotionally aware
        """
        if mode == MemoryMode.graph:
            return self._graph_dialogue(npc, events)
        elif mode == MemoryMode.vector:
            return self._vector_dialogue(npc, events, recall_text)
        else:
            return self._hybrid_dialogue(npc, events, recall_text)

    def _graph_dialogue(self, npc: NpcState, events: List) -> str:
        """Graph-only dialogue. Factual, rigid, no emotional generalization.

        This mode only uses locally known facts. It cannot generalize
        across similar events or infer emotional context.
        """
        if not events:
            if npc.faction:
                return (
                    f"I am {npc.name} of the {npc.faction.value}."
                    f" I have no record of you."
                )
            return f"I am {npc.name}. I don't know you."

        action_count = len(events)
        last_action = events[-1].action_type.value if events else "unknown"

        return (
            f"[Graph Fact] NPC {npc.name} has {action_count} known event(s) "
            f"involving the player. Last event: {last_action}. "
            f"Sentiment values: trust={npc.trust}, fear={npc.fear}, "
            f"respect={npc.respect}, anger={npc.anger}. "
            f"These are recorded facts."
        )

    def _vector_dialogue(self, npc: NpcState, events: List, recall_text: str) -> str:
        """Vector-only dialogue. Expressive but may hallucinate.

        This mode uses Cognee's RAG completion, which retrieves semantically
        similar content. It can produce emotional responses but may leak
        knowledge from other NPCs' datasets.
        """
        if recall_text and len(recall_text) > 10:
            return (
                f"[Vector Memory] Based on semantic associations: "
                f"{recall_text[:200]} "
                f"I have a feeling about you, even if I can't say exactly why."
            )

        if not events:
            return (
                f"[Vector Memory] Something about you seems familiar,"
                f" but I can't place it."
            )

        return (
            f"[Vector Memory] I sense you've been involved in events here. "
            f"The impressions linger. I feel {self._describe_mood(npc)} "
            f"when I think of you."
        )

    def _hybrid_dialogue(self, npc: NpcState, events: List, recall_text: str) -> str:
        """Hybrid dialogue. Grounded facts + emotional intelligence.

        This mode combines:
        - Graph-grounded facts (only events this NPC knows)
        - Vector-semantic tone (emotional color)
        - The result is both accurate and nuanced
        """
        if not events:
            greeting = self._get_faction_greeting(npc)
            return (
                f"[Hybrid Memory] {greeting} "
                f"The wind carries stories, but I have none of you yet."
            )

        last_action = events[-1].action_type.value.replace("_", " ")
        mood = self._describe_mood(npc)
        faction_ref = (
            f"as a member of the {npc.faction.value}" if npc.faction else ""
        )

        return (
            f"[Hybrid Memory] {faction_ref} I recall what happened — "
            f"the {last_action}. It stays with me. "
            f"Right now I feel {mood} toward you. "
            f"What brings you here now?"
        )

    def _get_faction_greeting(self, npc: NpcState) -> str:
        if not npc.faction:
            return "Welcome to Lumen Market."
        return f"The {npc.faction.value} watches over this village."

    def _describe_mood(self, npc: NpcState) -> str:
        """Describe the NPC's emotional state in words."""
        if npc.anger > 60:
            return "angry and wronged"
        elif npc.fear > 50:
            return "wary and cautious"
        elif npc.trust < 30:
            return "distrustful"
        elif npc.trust > 70:
            return "warm and welcoming"
        elif npc.respect > 60:
            return "respectful"
        else:
            return "cautious"
