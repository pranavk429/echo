import logging
from typing import List, Dict, Tuple, Optional

from app.models import EventRecord, BeliefRecord, NpcState, MemoryMode, ActionType, Faction
from app.game_state import GameStateManager
from app.cognee_client import CogneeClient

logger = logging.getLogger(__name__)


class DialogueComposer:
    """Generates grounded NPC dialogue from Cognee memory.

    CRITICAL RULE: The LLM only PHRASES the response. It never invents facts.
    All facts come from:
    1. The NPC's known events (from Cognee recall)
    2. The NPC's current emotional state (trust/fear/respect/anger)
    3. The NPC's faction affiliation

    If the NPC doesn't know about an event, the dialogue MUST NOT reference it.
    This is enforced by checking local beliefs before composing.
    """

    def __init__(self, game_state: GameStateManager, cognee: CogneeClient):
        self.gs = game_state
        self.cognee = cognee

    async def generate_reaction(
        self, npc_name: str, event: EventRecord, mode: str = "hybrid"
    ) -> str:
        """Generate an NPC's reaction to an event.

        This is called immediately after an action to give the player
        instant feedback. The reaction uses the NPC's LOCAL state ONLY
        (beliefs already processed locally). No Cognee recall here —
        it's too slow for the game loop (10-15s). Cognee recall is
        used only in the explicit /api/dialogue endpoint.

        Args:
            npc_name: The NPC to generate dialogue for
            event: The event that just happened
            mode: "graph", "vector", or "hybrid"

        Returns:
            A dialogue string
        """
        npc = self.gs.npcs.get(npc_name)
        if not npc:
            return ""

        # Check if this NPC knows about the event
        knows = self.gs._npc_knows_event(npc_name, event.event_id)

        if not knows:
            # NPC doesn't know — they should not reference the event
            return self._neutral_greeting(npc)

        # Build a grounded reaction from local state only (no Cognee recall)
        return self._compose_reaction(npc, event, "", knows, mode)

    def _compose_reaction(
        self,
        npc: NpcState,
        event: EventRecord,
        cognee_context: str,
        knows: bool,
        mode: str,
    ) -> str:
        """Compose a reaction string from grounded data.

        This uses a template-based approach for reliability, with Cognee
        context providing tone and nuance. The templates ensure the NPC
        never hallucinates facts — they only reference what they know.
        """
        dominant = self._dominant_emotion(npc)
        action_label = event.action_type.value.replace("_", " ")
        action_val = event.action_type.value

        if dominant == "anger":
            if npc.anger > 50:
                if action_val == "steal":
                    return (
                        f"You think you can just steal from us?"
                        f" I saw what you did."
                    )
                elif action_val == "threaten":
                    return (
                        f"Threats won't work on me. I remember your kind."
                    )
                elif action_val == "lie":
                    return (
                        f"Lies have a way of surfacing. I know the truth."
                    )
                else:
                    return f"I haven't forgotten what happened."
            else:
                return f"I'm not pleased about what happened, but I'm listening."

        elif npc.trust < 30 and dominant != "respect":
            if action_val == "apologize":
                return (
                    f"An apology doesn't undo what was done."
                    f" But I'm listening."
                )
            elif action_val == "return_item":
                return (
                    f"Returning what you took is a start."
                    f" Trust takes longer."
                )
            else:
                return (
                    f"I don't trust you. The memory of what you did is fresh."
                )

        elif npc.trust > 70:
            if action_val == "gift":
                return (
                    f"That's kind of you."
                    f" Not everyone passing through shows such generosity."
                )
            elif action_val == "help" or action_val == "help_":
                return (
                    f"You've proven yourself helpful."
                    f" Word travels in this village."
                )
            else:
                return (
                    f"Good to see you again."
                    f" The village remembers its friends."
                )

        else:
            if knows:
                return (
                    f"I know about the {action_label}."
                    f" It's noted. Actions have weight here."
                )
            else:
                return self._neutral_greeting(npc)

    def _dominant_emotion(self, npc: NpcState) -> str:
        """Determine the NPC's dominant emotion based on their state."""
        negatives = npc.anger + npc.fear
        positives = npc.trust + npc.respect

        if negatives > positives * 1.5:
            if npc.anger > npc.fear:
                return "anger"
            return "fear"
        if positives > negatives * 1.5:
            if npc.trust > npc.respect:
                return "trust"
            return "respect"
        return "neutral"

    def _neutral_greeting(self, npc: NpcState) -> str:
        """A neutral greeting for NPCs who don't know about recent events."""
        if npc.faction:
            if npc.trust > 60:
                return f"Greetings, friend. The {npc.faction.value} welcomes you."
            elif npc.trust < 30:
                return f"You're back. I'm watching."
            else:
                return f"Hello there. Lumen Market has a peaceful rhythm today."
        else:
            return f"Hello. The road brought you here, as it brings many."

    async def generate_open_dialogue(
        self, npc_name: str, mode: str = "hybrid"
    ) -> Tuple[str, List[Dict]]:
        """Generate an NPC's response when the player just talks to them
        (no recent action). This is a general dialogue that reflects the
        NPC's current memory of the player.

        Returns:
            Tuple of (dialogue_text, provenance_data)
        """
        npc = self.gs.npcs.get(npc_name)
        if not npc:
            return "I don't know you.", []

        provenance = []

        # Get NPC's known events from Cognee
        try:
            known = await self.cognee.recall_npc_knowledge(
                npc_name=npc_name,
                query="What do I know about the player and recent events?",
                mode=mode,
                top_k=5,
            )
            if known:
                provenance.append(
                    {
                        "source": "cognee_recall",
                        "mode": mode,
                        "summary": " ".join(known)[:200],
                    }
                )
        except Exception as e:
            logger.warning(f"Recall failed for open dialogue: {e}")

        # Check local beliefs
        local_beliefs = self.gs.beliefs.get(npc_name, [])
        if local_beliefs:
            provenance.append(
                {
                    "source": "local_beliefs",
                    "count": len(local_beliefs),
                    "events": [b.event_id for b in local_beliefs],
                }
            )

        # Generate dialogue based on available knowledge
        if not local_beliefs:
            # NPC knows nothing about the player
            if npc.faction:
                return (
                    f"I sense you're new to Lumen Market."
                    f" The {npc.faction.value} keeps careful watch.",
                    provenance,
                )
            return (
                f"First time in Lumen Market?"
                f" Take care — memories live long here.",
                provenance,
            )

        # NPC has some knowledge
        dominant = self._dominant_emotion(npc)
        if dominant == "anger":
            return (
                f"I know what you did."
                f" The village remembers, even if you wish it didn't.",
                provenance,
            )
        elif dominant == "fear":
            return (
                f"You've made an impression."
                f" Not all of it good. Be careful how you tread.",
                provenance,
            )
        elif dominant == "trust":
            return (
                f"Good to see you. Your actions have spoken well of you.",
                provenance,
            )
        else:
            return (
                f"I remember you. The market has eyes everywhere.",
                provenance,
            )
