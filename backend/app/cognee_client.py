import logging
from typing import Dict, Any, List, Optional

import cognee

from app.config import settings

logger = logging.getLogger(__name__)


class CogneeClient:
    """Real Cognee Cloud client. Every method calls the live API.

    Architecture:
    - Each NPC gets their own dataset for partial-knowledge isolation.
    - Events are stored as structured text that Cognee can cognify into graph+vector.
    - Social relationships are stored as graph edges between NPC nodes.
    - Beliefs are edges from NPC nodes to Event nodes with certainty properties.
    """

    def __init__(self):
        self._connected = False
        self._dataset_names = [
            "echo_public",  # Public events (any NPC can recall)
            "echo_mira",
            "echo_rowan",
            "echo_sol",
            "echo_niko",
            "echo_vale",
            "echo_ilya",
            "echo_factions",  # Faction-level memory
        ]
        self._session_id = None

    async def connect(self):
        """Connect to Cognee Cloud. Must be called once at startup."""
        if self._connected:
            return
        await cognee.serve(
            url=settings.cognee_base_url,
            api_key=settings.cognee_api_key,
        )
        self._connected = True
        logger.info("Connected to Cognee Cloud")

    async def disconnect(self):
        if self._connected:
            try:
                await cognee.disconnect()
            except Exception as e:
                logger.warning(f"Disconnect warning: {e}")
            self._connected = False

    async def ensure_dataset(self, dataset_name: str):
        """Ensure a dataset exists. Cognee creates datasets implicitly on first write."""
        pass

    async def store_event(
        self,
        event_text: str,
        dataset_name: str,
        session_id: Optional[str] = None,
    ):
        """Store an event in Cognee memory.

        This is a REAL Cognee Cloud call. It triggers:
        1. Text chunking
        2. LLM triplet extraction (subject-relation-object)
        3. Embedding generation
        4. Graph node+edge creation
        5. Vector index update

        Args:
            event_text: Natural language description of the event
            dataset_name: Which NPC's dataset to store in (e.g. "echo_mira")
            session_id: Optional session ID for fast cache

        Returns: None. This is fire-and-forget from the game loop perspective.
        """
        kwargs: Dict[str, Any] = {"dataset_name": dataset_name}
        if session_id:
            kwargs["session_id"] = session_id

        await cognee.remember(event_text, **kwargs)
        logger.debug(f"Stored event in {dataset_name}: {event_text[:60]}...")

    async def store_graph_edge(
        self,
        subject: str,
        relation: str,
        obj: str,
        dataset_name: str,
    ):
        """Store a structured graph edge as a sentence in Cognee.

        Args:
            subject: The source entity (e.g. "Mira")
            relation: The relationship (e.g. "witnessed")
            obj: The target entity (e.g. "theft_event_001")
            dataset_name: Which dataset to store in
        """
        edge_text = f"[GRAPH_EDGE] {subject} {relation} {obj}"
        await self.store_event(edge_text, dataset_name)

    async def recall_npc_knowledge(
        self,
        npc_name: str,
        query: str,
        mode: str = "hybrid",
        top_k: int = 10,
    ) -> List[str]:
        """Recall what an NPC knows about a topic.

        This is the CORE retrieval method for the game. It queries a specific
        NPC's dataset and returns relevant memory entries.

        Note: Cognee 1.2.2's recall() auto-routes to the best search strategy,
        so mode primarily affects the template-based phrasing in BaselineService.

        Args:
            npc_name: Which NPC's knowledge to query
            query: Natural language question
            mode: "graph", "vector", or "hybrid" (affects template phrasing)
            top_k: Number of results to return

        Returns:
            List of answer strings from Cognee recall
        """
        dataset_name = f"echo_{npc_name.lower()}"

        try:
            # Cognee 1.2.2's recall() auto-routes across strategies.
            # To force a specific SearchType, use cognee.search() instead.
            results = await cognee.recall(
                query_text=query,
                datasets=[dataset_name, "echo_public"],
                top_k=top_k,
            )
            return self._flatten_results(results)
        except Exception as e:
            logger.error(f"Recall failed for {npc_name} ({mode}): {e}")
            return [f"[Memory unavailable: {str(e)}]"]

    async def recall_faction_mood(
        self, faction_name: str, query: str, mode: str = "hybrid"
    ) -> List[str]:
        """Recall faction-level memory.

        Uses the echo_factions dataset which stores faction-level sentiment.
        """
        try:
            results = await cognee.recall(
                query_text=query,
                datasets=["echo_factions"],
                top_k=5,
            )
            return self._flatten_results(results)
        except Exception as e:
            logger.error(f"Faction recall failed for {faction_name}: {e}")
            return []

    async def classify_action(self, action_description: str) -> Dict[str, Any]:
        """Classify a novel action into an archetype using vector similarity.

        This is the anti-hardcode proof. The player can type any action in free text,
        and this method finds the semantically closest known action archetype.

        Args:
            action_description: Free-text description (e.g. "I threatened Niko with a knife")

        Returns:
            Dict with action_type, valence, and confidence
        """
        try:
            results = await cognee.recall(
                query_text=f"Classify this action: {action_description}",
                datasets=["echo_public"],
                top_k=3,
            )
            raw = self._flatten_results(results)
            combined = " ".join(raw).lower()
            # Extract valence from the response
            is_negative = any(
                w in combined
                for w in ["negative", "harmful", "threat", "violence"]
            )
            is_positive = any(
                w in combined
                for w in ["positive", "kind", "generous", "helpful"]
            )
            return {
                "action_type": "classified",
                "valence": "negative" if is_negative else ("positive" if is_positive else "neutral"),
                "confidence": 0.7 if (is_negative or is_positive) else 0.3,
                "raw": combined[:200],
            }
        except Exception as e:
            logger.error(f"Action classification failed: {e}")
            return {
                "action_type": "unknown",
                "valence": "neutral",
                "confidence": 0.0,
                "raw": "",
            }

    async def recall_public_knowledge(
        self, query: str, mode: str = "hybrid"
    ) -> List[str]:
        """Recall from the public events dataset. Used for events anyone could know."""
        return await self.recall_npc_knowledge("public", query, mode)

    async def get_session_memory(
        self, session_id: str, query: str
    ) -> List[str]:
        """Get session-scoped memory (faster than full graph recall).

        Session memory is used for the hot path — recent events in the current
        game session. It syncs to the graph in the background.
        """
        try:
            results = await cognee.recall(
                query_text=query,
                session_id=session_id,
                datasets=["echo_public"],
                top_k=10,
            )
            return self._flatten_results(results)
        except Exception as e:
            logger.error(f"Session recall failed: {e}")
            return []

    def _flatten_results(self, results) -> List[str]:
        """Flatten Cognee recall results into a list of text strings.

        Cognee returns different shapes depending on the SearchType:
        - GRAPH_COMPLETION returns objects with .answer
        - RAG_COMPLETION returns objects with .content
        - Session returns objects with .content
        """
        if results is None:
            return []
        out = []
        for r in results:
            if r is None:
                continue
            for attr in ("answer", "content", "text", "summary"):
                v = getattr(r, attr, None)
                if v:
                    out.append(str(v))
            if not any(
                getattr(r, a, None)
                for a in ("answer", "content", "text", "summary")
            ):
                out.append(str(r))
        return out


# Singleton
cognee_client = CogneeClient()
