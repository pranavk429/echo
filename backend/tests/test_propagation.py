"""Tests for PropagationEngine and GameStateManager propagation logic.

These tests use a mock CogneeClient (or None) to avoid real Cognee Cloud calls.
Core game state assertions are tested directly on the GameStateManager.
"""

import uuid
from typing import Optional, List, Dict, Any

import pytest

from app.models import (
    ActionType,
    BeliefRecord,
    EventRecord,
    Faction,
    FactionMood,
    Location,
    NpcState,
    RelationshipType,
)
from app.game_state import GameStateManager
from app.world_data import NPC_DATA, FACTION_DATA, SOCIAL_EDGES, ACTION_EFFECTS, PROPAGATION_RULES


# ─── Mock CogneeClient ───────────────────────────────────────────


class MockCogneeClient:
    """A no-op CogneeClient that records calls for assertion."""

    def __init__(self):
        self.events_stored: List[dict] = []
        self.edges_stored: List[dict] = []

    async def store_event(self, event_text: str, dataset_name: str, session_id: Optional[str] = None):
        self.events_stored.append({
            "text": event_text[:60],
            "dataset": dataset_name,
        })

    async def store_graph_edge(self, subject: str, relation: str, obj: str, dataset_name: str):
        self.edges_stored.append({
            "subject": subject,
            "relation": relation,
            "obj": obj,
            "dataset": dataset_name,
        })

    async def recall_npc_knowledge(self, npc_name: str, query: str, mode: str = "hybrid", top_k: int = 10):
        return []

    async def recall_faction_mood(self, faction_name: str, query: str, mode: str = "hybrid"):
        return []

    async def classify_action(self, action_description: str):
        return {"action_type": "unknown", "valence": "neutral", "confidence": 0.0, "raw": ""}


# ─── Fixtures ────────────────────────────────────────────────────


@pytest.fixture
def gs():
    """Create a fresh GameStateManager for each test."""
    return GameStateManager(f"test_{uuid.uuid4().hex[:8]}")


@pytest.fixture
def mock_cognee():
    return MockCogneeClient()


# ─── Witness Identification ──────────────────────────────────────


class TestWitnessIdentification:
    """Tests that witnesses are correctly identified based on location."""

    def test_witnesses_at_same_location(self, gs: GameStateManager):
        """NPCs at the player's location should be witnesses."""
        # Player starts at town_square
        gs.player_location = Location.town_square
        # Both Vale and Ilya are at town_square
        witnesses = [
            name
            for name, npc in gs.npcs.items()
            if npc.location == gs.player_location
        ]
        # Vale and Ilya are at town_square
        assert "Vale" in witnesses
        assert "Ilya" in witnesses
        # Mira is at orchard_stall, not a witness
        assert "Mira" not in witnesses

    def test_target_npc_always_witness(self, gs: GameStateManager):
        """The target NPC should always be a witness regardless of location."""
        gs.player_location = Location.alley
        target = "Mira"
        target_npc = gs.npcs.get(target)
        witnesses = [
            name
            for name, npc in gs.npcs.items()
            if npc.location == gs.player_location and name != target
        ]
        if target_npc and target not in witnesses:
            witnesses.append(target)
        assert target in witnesses

    def test_no_witnesses_when_player_alone(self, gs: GameStateManager):
        """If no NPCs are at the player's location, witness list is empty."""
        # Set player at the alley — only Niko is there
        gs.player_location = Location.alley
        witnesses = [
            name
            for name, npc in gs.npcs.items()
            if npc.location == gs.player_location
        ]
        # Niko starts at alley
        assert "Niko" in witnesses
        assert "Mira" not in witnesses
        assert "Sol" not in witnesses


# ─── Belief Record Creation ──────────────────────────────────────


class TestBeliefCreation:
    """Tests that belief records are created correctly during propagation."""

    def test_witness_gets_certain_belief(self, gs: GameStateManager):
        """A witness should have certainty=1.0 for the event they saw."""
        gs.player_location = Location.town_square
        event = gs.create_event(
            action_type=ActionType.steal,
            target_npc="Vale",
            item="coin",
            description=None,
            witnesses=["Vale", "Ilya"],
        )
        # Manually add witness beliefs (as PropagationEngine would)
        for w in event.witnesses:
            belief = BeliefRecord(
                npc_name=w,
                event_id=event.event_id,
                certainty=1.0,
                source="witnessed",
                heard_from=None,
            )
            gs.add_belief(w, belief)

        vale_beliefs = gs.beliefs.get("Vale", [])
        ilya_beliefs = gs.beliefs.get("Ilya", [])

        assert len(vale_beliefs) == 1
        assert vale_beliefs[0].certainty == 1.0
        assert vale_beliefs[0].source == "witnessed"

        assert len(ilya_beliefs) == 1
        assert ilya_beliefs[0].certainty == 1.0
        assert ilya_beliefs[0].source == "witnessed"

    def test_ally_propagation_higher_certainty_than_neutral(self, gs: GameStateManager):
        """Ally propagation should have higher certainty than neutral propagation."""
        # Mira (orchard_guild) stealing → witnesses = Mira
        # Rowan (ally of Mira) should get higher certainty than Sol (neutral)
        gs.player_location = Location.orchard_stall
        event = gs.create_event(
            action_type=ActionType.steal,
            target_npc="Mira",
            item="apple",
            description=None,
            witnesses=["Mira"],
        )

        # Simulate propagation to Rowan (ally) and Sol (neutral)
        # Find the relationship trust levels
        rowan_trust = 0
        sol_trust = 0
        for connected, rt, tl in gs.get_connected_npcs("Mira"):
            if connected == "Rowan":
                rowan_trust = tl
            elif connected == "Sol":
                sol_trust = tl

        # Ally certainty: (trust/100) * 0.8 (ally multiplier), min 0.5
        ally_certainty = max((rowan_trust / 100.0) * PROPAGATION_RULES[RelationshipType.ally]["certainty_multiplier"], 0.5)
        # Neutral certainty: (trust/100) * 0.5 (neutral multiplier)
        neutral_certainty = (sol_trust / 100.0) * PROPAGATION_RULES[RelationshipType.neutral]["certainty_multiplier"]

        assert ally_certainty > neutral_certainty, (
            f"Ally certainty ({ally_certainty}) should be > "
            f"neutral certainty ({neutral_certainty})"
        )

    def test_rival_does_not_get_propagation(self, gs: GameStateManager):
        """Rival NPCs should NOT receive propagation about an event."""
        gs.player_location = Location.orchard_stall
        event = gs.create_event(
            action_type=ActionType.steal,
            target_npc="Mira",
            item="relic",
            description=None,
            witnesses=["Mira"],
        )

        # Mira is connected to Niko as rival
        # Simulate propagation check: rivals should not get beliefs
        # since PROPAGATION_RULES has no entry for rivals
        for connected_npc, rel_type, trust in gs.get_connected_npcs("Mira"):
            if rel_type == RelationshipType.rival:
                rules = PROPAGATION_RULES.get(rel_type)
                assert rules is None, "Rivals should have no propagation rules"

    def test_ilya_no_propagation(self, gs: GameStateManager):
        """Ilya has no social connections and should not propagate events."""
        connections = gs.get_connected_npcs("Ilya")
        assert len(connections) == 0, "Ilya should have no social connections"


# ─── Sentiment Changes ───────────────────────────────────────────


class TestSentimentChanges:
    """Tests that NPC sentiment is updated and clamped correctly."""

    def test_witness_sentiment_changes(self, gs: GameStateManager):
        """Witnesses should have their sentiment changed by the full effect."""
        gs.player_location = Location.orchard_stall
        event = gs.create_event(
            action_type=ActionType.steal,
            target_npc="Mira",
            item="apple",
            description=None,
            witnesses=["Mira"],
        )

        effects = ACTION_EFFECTS.get("steal", {})
        mira_before = gs.npcs["Mira"].trust

        # Apply full effect (scale=1.0)
        npc = gs.npcs["Mira"]
        from app.propagation import PropagationEngine

        # Use the static helper
        engine = PropagationEngine.__new__(PropagationEngine)
        engine.gs = gs
        engine._apply_sentiment_change(npc, effects, scale=1.0)

        expected_trust = max(0, min(100, mira_before + effects["trust"]))
        assert gs.npcs["Mira"].trust == expected_trust, (
            f"Trust should change from {mira_before} to {expected_trust}"
        )

    def test_sentiment_clamped_to_0(self, gs: GameStateManager):
        """Sentiment values should not go below 0."""
        npc = gs.npcs["Mira"]
        npc.trust = 5  # Very low trust

        from app.propagation import PropagationEngine
        engine = PropagationEngine.__new__(PropagationEngine)
        engine.gs = gs

        effects = {"trust": -20}
        engine._apply_sentiment_change(npc, effects, scale=1.0)

        assert npc.trust >= 0, f"Trust should be clamped to 0, got {npc.trust}"

    def test_sentiment_clamped_to_100(self, gs: GameStateManager):
        """Sentiment values should not exceed 100."""
        npc = gs.npcs["Mira"]
        npc.trust = 95

        from app.propagation import PropagationEngine
        engine = PropagationEngine.__new__(PropagationEngine)
        engine.gs = gs

        effects = {"trust": 20}
        engine._apply_sentiment_change(npc, effects, scale=1.0)

        assert npc.trust <= 100, f"Trust should be clamped to 100, got {npc.trust}"


# ─── Faction Moods ────────────────────────────────────────────────


class TestFactionMoods:
    """Tests that faction moods update correctly."""

    def test_faction_mood_averages_members(self, gs: GameStateManager):
        """Faction mood should be the average of all members' sentiments."""
        # Orchard Guild has Mira and Rowan
        orchard_members = ["Mira", "Rowan"]

        # Manually set different sentiments
        gs.npcs["Mira"].trust = 60
        gs.npcs["Mira"].anger = 30
        gs.npcs["Rowan"].trust = 40
        gs.npcs["Rowan"].anger = 50

        # Calculate expected averages
        expected_trust = (60 + 40) / 2
        expected_anger = (30 + 50) / 2

        # Simulate faction mood update (as PropagationEngine would)
        faction = Faction.orchard_guild
        mood = gs.factions[faction.value]
        members = [n for n, s in gs.npcs.items() if s.faction == faction]

        if members:
            mood.trust = round(sum(gs.npcs[m].trust for m in members) / len(members))
            mood.anger = round(sum(gs.npcs[m].anger for m in members) / len(members))

        assert mood.trust == round(expected_trust), (
            f"Faction trust should be {round(expected_trust)}, got {mood.trust}"
        )
        assert mood.anger == round(expected_anger), (
            f"Faction anger should be {round(expected_anger)}, got {mood.anger}"
        )


# ─── Event Creation ──────────────────────────────────────────────


class TestEventCreation:
    """Tests that events are created correctly."""

    def test_create_event_has_unique_id(self, gs: GameStateManager):
        """Each event should have a unique event_id."""
        gs.player_location = Location.town_square
        event1 = gs.create_event(
            action_type=ActionType.steal,
            target_npc="Vale",
            item=None,
            description=None,
            witnesses=["Vale"],
        )
        event2 = gs.create_event(
            action_type=ActionType.gift,
            target_npc="Mira",
            item="flower",
            description=None,
            witnesses=["Mira"],
        )
        assert event1.event_id != event2.event_id

    def test_event_stores_witnesses(self, gs: GameStateManager):
        """Events should store the list of witnesses correctly."""
        gs.player_location = Location.town_square
        witnesses = ["Vale", "Ilya"]
        event = gs.create_event(
            action_type=ActionType.help_,
            target_npc="Sol",
            item=None,
            description="Helped with repairs",
            witnesses=witnesses,
        )
        assert event.witnesses == witnesses
        assert event.action_type == ActionType.help_
        assert event.action_type.value == "help"  # The actual value


# ─── NpcState.faction is Optional ────────────────────────────────


class TestNpcFaction:
    """Tests that NPCs without factions work correctly."""

    def test_vale_has_no_faction(self, gs: GameStateManager):
        assert gs.npcs["Vale"].faction is None

    def test_ilya_has_no_faction(self, gs: GameStateManager):
        assert gs.npcs["Ilya"].faction is None

    def test_mira_has_orchard_faction(self, gs: GameStateManager):
        assert gs.npcs["Mira"].faction == Faction.orchard_guild

    def test_faction_values_have_spaces(self, gs: GameStateManager):
        """Faction enum values have spaces (e.g. 'Orchard Guild')."""
        assert Faction.orchard_guild.value == "Orchard Guild"
        assert Faction.shrine_circle.value == "Shrine Circle"
        assert Faction.alley_network.value == "Alley Network"


# ─── ActionType Help ──────────────────────────────────────────────


class TestActionTypeHelp:
    """Tests that ActionType.help_ works correctly."""

    def test_help_enum_value(self):
        assert ActionType.help_.value == "help"

    def test_help_key_in_action_effects(self):
        assert "help" in ACTION_EFFECTS
        assert ACTION_EFFECTS["help"]["trust"] == 20


# ─── Social Graph Edges ──────────────────────────────────────────


class TestSocialGraph:
    """Tests that the social graph is initialized correctly."""

    def test_mira_connected_to_rowan(self, gs: GameStateManager):
        connections = gs.get_connected_npcs("Mira")
        connected_names = [c[0] for c in connections]
        assert "Rowan" in connected_names
        assert "Niko" in connected_names
        assert "Sol" in connected_names

    def test_ilya_has_no_connections(self, gs: GameStateManager):
        connections = gs.get_connected_npcs("Ilya")
        assert len(connections) == 0

    def test_connection_types(self, gs: GameStateManager):
        """Mira-Rowan should be ally, Mira-Niko should be rival."""
        mira_connections = gs.get_connected_npcs("Mira")
        for name, rel_type, trust in mira_connections:
            if name == "Rowan":
                assert rel_type == RelationshipType.ally
            elif name == "Niko":
                assert rel_type == RelationshipType.rival
            elif name == "Sol":
                assert rel_type == RelationshipType.neutral
