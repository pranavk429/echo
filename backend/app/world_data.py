from app.models import Location, Faction, RelationshipType

# ─── The 6 NPCs ──────────────────────────────────────────────────

NPC_DATA = {
    "Mira": {
        "display_name": "Mira",
        "location": Location.orchard_stall,
        "faction": Faction.orchard_guild,
        "role": "orchard merchant",
        "initial_trust": 50,
        "initial_fear": 20,
        "initial_respect": 40,
        "initial_anger": 10,
        "description": "Tends the orchard stall in Lumen Market. Friendly but watchful.",
    },
    "Rowan": {
        "display_name": "Rowan",
        "location": Location.guild_hall,
        "faction": Faction.orchard_guild,
        "role": "guild guard",
        "initial_trust": 40,
        "initial_fear": 30,
        "initial_respect": 50,
        "initial_anger": 15,
        "description": "Guild guard who watches over the market. Loyal to Mira.",
    },
    "Sol": {
        "display_name": "Sol",
        "location": Location.shrine,
        "faction": Faction.shrine_circle,
        "role": "shrine keeper",
        "initial_trust": 60,
        "initial_fear": 5,
        "initial_respect": 70,
        "initial_anger": 5,
        "description": "Keeper of the shrine. Neutral, wise, observant.",
    },
    "Niko": {
        "display_name": "Niko",
        "location": Location.alley,
        "faction": Faction.alley_network,
        "role": "alley broker",
        "initial_trust": 30,
        "initial_fear": 40,
        "initial_respect": 20,
        "initial_anger": 25,
        "description": "Operates from the alley. Deals in secrets and contraband.",
    },
    "Vale": {
        "display_name": "Vale",
        "location": Location.town_square,
        "faction": None,  # No faction — independent
        "role": "town crier",
        "initial_trust": 45,
        "initial_fear": 15,
        "initial_respect": 35,
        "initial_anger": 10,
        "description": "The town crier. Gossip spreads fast through Vale.",
    },
    "Ilya": {
        "display_name": "Ilya",
        "location": Location.town_square,
        "faction": None,  # Outsider — no faction
        "role": "outsider traveler",
        "initial_trust": 50,
        "initial_fear": 25,
        "initial_respect": 30,
        "initial_anger": 10,
        "description": "A traveler passing through. Knows nobody when they arrive.",
    },
}

# ─── The 3 Factions ──────────────────────────────────────────────

FACTION_DATA = {
    Faction.orchard_guild: {
        "display_name": "Orchard Guild",
        "members": ["Mira", "Rowan"],
        "initial_trust": 50,
        "initial_fear": 20,
        "initial_respect": 40,
        "initial_anger": 10,
    },
    Faction.shrine_circle: {
        "display_name": "Shrine Circle",
        "members": ["Sol"],
        "initial_trust": 60,
        "initial_fear": 5,
        "initial_respect": 70,
        "initial_anger": 5,
    },
    Faction.alley_network: {
        "display_name": "Alley Network",
        "members": ["Niko"],
        "initial_trust": 30,
        "initial_fear": 40,
        "initial_respect": 20,
        "initial_anger": 25,
    },
}

# ─── Social Graph Edges ──────────────────────────────────────────

# Format: (npc1, npc2, relationship_type, trust_level 0-100)
SOCIAL_EDGES = [
    ("Mira", "Rowan", RelationshipType.ally, 85),
    ("Rowan", "Mira", RelationshipType.ally, 90),
    ("Mira", "Sol", RelationshipType.neutral, 50),
    ("Sol", "Mira", RelationshipType.neutral, 55),
    ("Rowan", "Sol", RelationshipType.neutral, 40),
    ("Sol", "Rowan", RelationshipType.neutral, 45),
    ("Mira", "Niko", RelationshipType.rival, 15),
    ("Niko", "Mira", RelationshipType.rival, 10),
    ("Rowan", "Niko", RelationshipType.rival, 10),
    ("Niko", "Rowan", RelationshipType.rival, 15),
    ("Vale", "Mira", RelationshipType.neutral, 60),
    ("Vale", "Rowan", RelationshipType.neutral, 55),
    ("Vale", "Sol", RelationshipType.neutral, 65),
    ("Vale", "Niko", RelationshipType.neutral, 45),
    ("Ilya",),  # Ilya knows nobody initially — tuple with just one name
]

# ─── Propagation Rules ───────────────────────────────────────────

# Which relationships cause memory propagation, and with what probability
PROPAGATION_RULES = {
    RelationshipType.ally: {
        "spread_chance": 0.9,
        "max_hops": 2,
        "certainty_multiplier": 0.8,
    },
    RelationshipType.neutral: {
        "spread_chance": 0.3,
        "max_hops": 1,
        "certainty_multiplier": 0.5,
    },
    # Rivals do NOT spread memory to each other
}

# ─── Locations Map ───────────────────────────────────────────────

LOCATION_DATA = {
    Location.orchard_stall: {
        "display_name": "Orchard Stall",
        "x": 150,
        "y": 100,  # Pixel coordinates on the 2D map
        "description": "A wooden stall piled with ripe fruit and woven baskets.",
    },
    Location.guild_hall: {
        "display_name": "Guild Hall",
        "x": 400,
        "y": 80,
        "description": "A sturdy stone building with the Orchard Guild crest above the door.",
    },
    Location.shrine: {
        "display_name": "Shrine",
        "x": 300,
        "y": 250,
        "description": "A quiet shrine with a small fountain. Sol tends the candles here.",
    },
    Location.alley: {
        "display_name": "Alley",
        "x": 100,
        "y": 200,
        "description": "A narrow alley between buildings. Niko conducts business in the shadows.",
    },
    Location.town_square: {
        "display_name": "Town Square",
        "x": 250,
        "y": 150,
        "description": "The center of Lumen Market. Vale announces news here.",
    },
}

# ─── Action Effects ──────────────────────────────────────────────

# How each action type affects NPC sentiment (base values before NPC-specific modifiers)
ACTION_EFFECTS = {
    "steal": {
        "trust": -20,
        "fear": +15,
        "respect": -15,
        "anger": +25,
        "public": True,
        "severity": 0.8,
    },
    "gift": {
        "trust": +15,
        "fear": -5,
        "respect": +10,
        "anger": -10,
        "public": True,
        "severity": 0.3,
    },
    "help": {
        "trust": +20,
        "fear": -10,
        "respect": +15,
        "anger": -15,
        "public": True,
        "severity": 0.4,
    },
    "lie": {
        "trust": -15,
        "fear": +10,
        "respect": -20,
        "anger": +15,
        "public": False,
        "severity": 0.6,
    },
    "apologize": {
        "trust": +10,
        "fear": -5,
        "respect": +5,
        "anger": -20,
        "public": True,
        "severity": 0.3,
    },
    "threaten": {
        "trust": -25,
        "fear": +25,
        "respect": -10,
        "anger": +30,
        "public": False,
        "severity": 0.9,
    },
    "ask_rumor": {
        "trust": 0,
        "fear": 0,
        "respect": 0,
        "anger": 0,
        "public": False,
        "severity": 0.1,
    },
    "return_item": {
        "trust": +20,
        "fear": -10,
        "respect": +15,
        "anger": -25,
        "public": True,
        "severity": 0.5,
    },
}
