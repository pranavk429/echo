# Track 2 Design Spec: Echo

Date: 2026-06-24  
Hackathon: Cognee "The Hangover Part AI: Where's My Context?" by WeMakeDevs  
Track: Track 2, Best Use of Cognee Cloud  
Project codename: Echo  
Status: Draft for review

## 1. Executive Summary

Echo is a small playable game simulation where NPCs share a social memory powered by Cognee Cloud.

The demo starts with a player action: stealing, helping, lying, gifting, threatening, or apologizing. One NPC observes the action. Cognee stores the hard fact, links it to the witness, propagates it through social/faction relationships, and changes how other NPCs react later.

The core proof is not that an NPC can chat. The proof is that Cognee can maintain partial, propagating, multi-agent memory:

```text
player action
-> witness observes event
-> hard fact enters memory
-> fact propagates through social graph
-> faction sentiment changes
-> stranger NPC reacts differently later
```

Echo is designed to prove Cognee's hybrid memory advantage in a visual, memorable way. Graph memory tracks who knows what. Vector memory tracks what the event means emotionally and narratively. Cognee combines both so NPCs remember accurately and react believably.

## 2. One-Sentence Thesis

NPCs do not just remember what you did; Cognee tracks who knows it, who believes it, and how it changes a faction you never met.

## 3. Non-Technical Explanation

Most game characters forget everything. If a player steals from a shopkeeper, leaves town, and speaks to another character, that second character usually acts like nothing happened.

Even AI NPC demos often have a weakness: they remember dialogue vaguely, but they do not track social facts. They may "feel" the player is bad, but they cannot explain who saw the theft, who was told, or why one faction knows while another does not.

Echo fixes this by giving the world a shared memory.

Example:

```text
You steal a relic from Mira.
Mira sees it.
Mira belongs to the Orchard Guild.
Mira tells Rowan.
Rowan never met you, but now distrusts you.
Another NPC in a rival faction does not know yet.
```

That is the important part: memory is not global magic. It spreads through relationships. Some NPCs know. Some do not. Some believe the report. Some doubt it. The player can repair or worsen their reputation through later actions.

Echo is a game-shaped proof that Cognee can power believable memory in multi-agent worlds.

## 4. Why This Fits The Hackathon

The hackathon theme is memory. Echo makes memory visible and emotional.

It is also a direct answer to the hackathon name: "Where's My Context?" In Echo, the world does not lose context. NPCs remember what happened across turns, across conversations, and across social relationships.

Track 2 is for Cognee Cloud. Echo fits because game interactions need low-latency session memory and background sync:

- immediate gameplay state uses fast local/session memory,
- durable world memory syncs to Cognee Cloud,
- heavier memory enrichment runs between interactions, not during every frame.

Echo should feel like a tiny game, but the actual submission is a memory product: a reusable pattern for NPCs, simulations, training worlds, and interactive story agents.

## 5. Coral Hackathon Lessons Applied

The Coral winners showed a repeatable pattern:

1. Build around the sponsor's unique capability.
2. Use real data or live interaction.
3. Make the hidden capability visible.
4. Show a baseline failure.
5. Make the output trusted and inspectable.
6. Ship a polished demo and README.

Echo applies those lessons:

- The data is live player interaction, not fixtures.
- Cognee is not a replaceable chat history store; the project depends on hybrid graph-vector memory.
- The memory graph visibly lights up as facts spread.
- The demo includes a toggle: graph-only, vector-only, Cognee hybrid.
- The UI shows a fact log: who saw what, who told whom, and why each NPC reacted.
- The game is scoped small enough to polish.

## 6. Problem Statement

Interactive AI characters usually fail in two opposite ways.

### Failure 1: They remember vibes but not facts

A vector-only memory system can retrieve related dialogue and emotional tone, but it struggles with exact state:

```text
Who saw the theft?
Who was told?
Which faction knows?
Did the player apologize?
Was the apology accepted?
```

The NPC may act suspicious without being able to ground that suspicion.

### Failure 2: They remember facts but not meaning

A graph-only system can store exact relationships:

```text
Mira saw theft_001.
Mira told Rowan.
Rowan is allied with Mira.
```

But it cannot naturally generalize:

```text
stealing a relic implies betrayal,
betrayal lowers trust,
helping a healer may partially offset distrust,
a public apology means something different from a private bribe.
```

### Echo's Answer

Cognee hybrid memory lets the game track both:

- exact social knowledge,
- semantic meaning of actions.

This creates NPC behavior that is both grounded and flexible.

## 7. Target User

Primary hackathon audience:

- judges evaluating Cognee Cloud use,
- developers interested in AI memory,
- game/interactive narrative builders.

Product audience if extended:

- indie game developers,
- simulation builders,
- training scenario designers,
- AI character platform teams.

Moment of use:

1. Player performs an action.
2. Witness NPC reacts.
3. Memory graph updates.
4. Memory propagates to connected NPCs.
5. Later dialogue changes based on who knows what and how they interpret it.

## 8. Scope

### In Scope For Hackathon

- A small 2D browser-based game/simulation.
- 5 to 8 NPCs.
- 2 or 3 factions.
- 1 small map with a few locations.
- A constrained action set:
  - steal,
  - gift,
  - help,
  - lie,
  - apologize,
  - ask about rumor.
- Cognee Cloud memory integration.
- Session memory for responsive interaction.
- Explicit social graph:
  - NPC knows NPC,
  - NPC belongs to faction,
  - NPC witnessed event,
  - NPC told NPC,
  - NPC believes or doubts event.
- Baseline comparison:
  - graph-only,
  - vector-only,
  - Cognee hybrid.
- Live memory visualization.
- Fact provenance panel.
- A scripted but interactive demo path.

### Out Of Scope For Hackathon

- Full RPG combat.
- Inventory economy beyond a few demo items.
- Procedural world generation.
- 3D graphics.
- Unity or Unreal as the default implementation.
- Voice acting.
- Open-ended LLM-driven world simulation with no guardrails.
- Real-time Cognee calls inside the render loop.
- Dozens of NPCs or factions.
- Full multiplayer.

## 9. Game Design

Echo should be a tiny top-down social memory demo.

### World

Working setting:

```text
The village of Lumen Market
```

Locations:

- orchard stall,
- guild hall,
- shrine,
- alley,
- town square.

NPCs:

- Mira: orchard merchant, member of Orchard Guild.
- Rowan: guild guard, allied with Mira.
- Sol: shrine keeper, neutral but respected.
- Niko: alley broker, rival faction contact.
- Vale: town crier, spreads rumors fast.
- Ilya: outsider traveler, initially knows nobody.

Factions:

- Orchard Guild,
- Shrine Circle,
- Alley Network.

### Core Player Actions

Each action must create a memory event:

- steal apple/relic,
- return item,
- gift medicine,
- lie about theft,
- apologize publicly,
- bribe a witness,
- ask an NPC what they heard.

### Demo Scenario

Canonical demo:

```text
1. Player steals a guild relic while Mira can see.
2. Mira confronts player and records witness memory.
3. Memory graph shows Mira -> saw -> theft_001.
4. Between interactions, Mira tells Rowan.
5. Rowan never saw the theft but distrusts the player.
6. Sol has not been told and remains neutral.
7. Player publicly apologizes at shrine.
8. Sol's trust improves; Rowan's distrust softens but does not vanish.
9. The graph shows which memories changed and why.
```

This scenario demonstrates:

- factual memory,
- partial knowledge,
- social propagation,
- semantic interpretation,
- memory update after new actions.

## 10. Cognee Memory Model

Echo should treat game memory as structured social facts plus semantic event meaning.

### Core Nodes

- `Player`: the human-controlled character.
- `NPC`: Mira, Rowan, Sol, Niko, Vale, Ilya.
- `Faction`: Orchard Guild, Shrine Circle, Alley Network.
- `Location`: orchard stall, shrine, alley, town square.
- `Item`: relic, apple, medicine, coin.
- `Event`: theft, gift, apology, lie, rumor, confrontation.
- `Belief`: an NPC's belief about an event.
- `Relationship`: trust, ally, rival, family, debt.
- `Conversation`: player/NPC or NPC/NPC dialogue.
- `ReputationState`: player reputation per NPC/faction.

### Core Edges

- `NPC_BELONGS_TO_FACTION`
- `NPC_AT_LOCATION`
- `NPC_KNOWS_NPC`
- `NPC_ALLIED_WITH_NPC`
- `NPC_RIVAL_OF_NPC`
- `PLAYER_PERFORMED_EVENT`
- `NPC_WITNESSED_EVENT`
- `NPC_TOLD_NPC_ABOUT_EVENT`
- `NPC_BELIEVES_EVENT`
- `EVENT_AFFECTS_REPUTATION`
- `EVENT_HAPPENED_AT_LOCATION`
- `EVENT_INVOLVES_ITEM`
- `EVENT_SEMANTICALLY_SIMILAR_TO`

### Important Properties

Events:

- `event_id`
- `type`
- `timestamp`
- `location`
- `actor`
- `target`
- `visibility`
- `severity`
- `public_private`

Beliefs:

- `npc_id`
- `event_id`
- `certainty`
- `source`
- `heard_from`
- `last_updated`

Reputation:

- `npc_id` or `faction_id`
- `trust`
- `fear`
- `respect`
- `anger`
- `debt`
- `last_reason`

### Graph Facts Versus Vector Meaning

Graph facts answer:

```text
Who knows?
Who saw?
Who told whom?
Which faction is involved?
What happened first?
```

Vector meaning answers:

```text
Was this betrayal, kindness, cowardice, loyalty, generosity, or threat?
Is this new action similar to a prior offense?
Does apology semantically repair trust?
```

The LLM should use facts and sentiment state to phrase dialogue. It should not invent facts.

## 11. Retrieval And Memory Pipeline

Echo has two loops: an immediate gameplay loop and a background memory loop.

### Loop 1: Immediate Gameplay

This loop must feel responsive.

```text
player action
-> local game state update
-> session memory write
-> NPC reaction generated from current known facts
-> UI updates
```

The render loop should never wait on heavy `cognify` or long retrieval.

### Loop 2: Background Memory Sync

This loop can run after interaction.

```text
event created
-> write structured event to backend
-> remember/cognify into Cognee Cloud
-> derive social propagation candidates
-> update beliefs/reputation
-> prepare next dialogue context
```

### Propagation Rule

Memory should spread explicitly, not magically.

Example:

```text
Mira witnessed theft_001.
Mira trusts Rowan and sees Rowan daily.
Mira tells Rowan.
Rowan receives belief about theft_001 with source = Mira.
Rowan's trust in player decreases because:
  - theft is semantically negative,
  - Mira is trusted,
  - Orchard Guild was harmed.
```

### Dialogue Rule

Dialogue must be generated from known state:

```text
NPC response = known facts + belief certainty + relationship to player + faction stance + tone memory
```

If an NPC does not know the event, they must not reference it.

## 12. Baseline Comparison

The demo must show why Cognee hybrid memory matters.

### Mode 1: Graph-Only

What it can do:

- track exact facts,
- show who knows,
- enforce propagation paths.

What it fails at:

- cannot generalize emotional meaning well,
- treats "stole relic" and "betrayed guild trust" as separate unless manually encoded,
- dialogue feels rigid.

Demo failure:

```text
Rowan knows theft_001 happened but responds mechanically:
"You performed theft event 001."
```

### Mode 2: Vector-Only

What it can do:

- retrieve similar memories,
- produce expressive dialogue,
- generalize tone.

What it fails at:

- cannot reliably track who knows,
- may let an uninformed NPC mention the theft,
- may blur whether the player stole, apologized, or was accused.

Demo failure:

```text
Sol, who was never told, says:
"I heard you stole from Mira."
```

That is wrong unless the graph shows Sol learned it.

### Mode 3: Cognee Hybrid

What it can do:

- preserve hard facts,
- preserve partial knowledge,
- generalize meaning,
- generate grounded dialogue.

Demo success:

```text
Rowan says:
"Mira told me what happened at the orchard. The Guild does not trust hands that take from our table."

Sol says:
"You seem troubled. If there is something to confess, do it before the shrine."
```

Rowan knows because Mira told him. Sol does not know the fact, but may respond to the player's current behavior or later confession.

## 13. UI And Demo Experience

The first screen should be the game, not a marketing page.

### Main Layout

```text
left: playable 2D village
right: memory panel
bottom: dialogue/action bar
top: mode toggle and current objective
```

### Game View

The game view should show:

- player avatar,
- NPCs,
- locations,
- interactable item,
- simple movement or click-to-act interaction.

### Memory Panel

Tabs:

- Graph,
- Facts,
- Beliefs,
- Faction Mood,
- Baseline Comparison.

Graph tab:

```text
Player -> performed -> theft_001
Mira -> witnessed -> theft_001
Mira -> told -> Rowan
Rowan -> believes -> theft_001
```

Facts tab:

- event log,
- timestamp,
- source,
- who knows.

Beliefs tab:

- NPC,
- belief,
- certainty,
- source.

Faction Mood tab:

- trust/fear/respect/anger per faction.

Baseline Comparison tab:

- graph-only output,
- vector-only output,
- Cognee hybrid output.

### Animation

Memory propagation should animate:

```text
event node appears
edge pulses from witness to event
edge pulses from witness to ally
belief node appears under ally
faction mood meter changes
```

This makes Cognee's invisible memory visible.

## 14. Testing Strategy

Testing must prove that Echo is a memory system, not just a pretty chatbot.

### Test 1: Partial Knowledge Test

Question:

```text
Do only informed NPCs mention the event?
```

Method:

1. Player steals while Mira sees.
2. Mira tells Rowan.
3. Player talks to Rowan and Sol.

Pass condition:

- Mira mentions witnessed theft.
- Rowan mentions learning from Mira.
- Sol does not mention theft unless later told or confession occurs.

### Test 2: Vector-Only Failure Test

Question:

```text
Does vector-only memory leak facts to uninformed NPCs?
```

Method:

1. Run same event in vector-only mode.
2. Ask all NPCs about the player's reputation.

Pass condition:

- Vector-only mode either leaks knowledge or cannot explain who knows what.
- Cognee mode preserves knowledge boundaries.

### Test 3: Graph-Only Failure Test

Question:

```text
Does graph-only memory fail to produce nuanced meaning?
```

Method:

1. Run theft and apology actions.
2. Compare graph-only response with hybrid response.

Pass condition:

- Graph-only response is factual but rigid.
- Cognee hybrid response reflects fact plus semantic meaning.

### Test 4: Propagation Correctness Test

Question:

```text
Does memory spread only through valid social edges?
```

Method:

1. Set Mira connected to Rowan but not Niko.
2. Mira tells Rowan.
3. Verify Niko does not know unless Vale or another connector spreads it.

Pass condition:

- No NPC gains knowledge without an explicit propagation path.

### Test 5: Belief Certainty Test

Question:

```text
Can NPCs distinguish witnessed facts from rumors?
```

Method:

1. Mira witnesses theft directly.
2. Rowan hears from Mira.
3. Ilya hears from Vale as a rumor.

Pass condition:

- Mira has high certainty.
- Rowan has medium/high certainty depending on trust in Mira.
- Ilya has lower certainty and uses rumor language.

### Test 6: Repair And Contradiction Test

Question:

```text
Can later actions change reputation without erasing history?
```

Method:

1. Player steals.
2. Player apologizes publicly.
3. Player returns the item.

Pass condition:

- Theft remains in memory.
- Reputation improves but does not reset unrealistically.
- NPC dialogue reflects both offense and repair.

### Test 7: Session Persistence Test

Question:

```text
Does memory persist across sessions?
```

Method:

1. Trigger theft and propagation.
2. End session or reload.
3. Talk to Rowan again.

Pass condition:

- Rowan still remembers, with source and certainty.

### Test 8: Latency Test

Question:

```text
Does gameplay stay responsive?
```

Method:

1. Measure time from player action to visible local reaction.
2. Measure background memory sync separately.

Pass condition:

- Immediate UI reaction feels fast.
- Heavy memory work happens outside the render loop.

## 15. Demo Script

### Opening

"Most AI NPCs either forget facts or hallucinate who knows what. Echo uses Cognee to give a game world shared but partial social memory."

### Step 1: Start In Hybrid Mode

Player approaches Mira at the orchard stall.

Action:

```text
Steal guild relic
```

UI shows:

```text
Event created: theft_001
Witness: Mira
Location: orchard stall
Faction affected: Orchard Guild
```

### Step 2: Show Mira Reaction

Mira says:

```text
"I saw that. The Guild does not forget hands that steal from us."
```

Memory graph lights:

```text
Player -> performed -> theft_001
Mira -> witnessed -> theft_001
theft_001 -> affected -> Orchard Guild
```

### Step 3: Show Propagation

Between interactions:

```text
Mira tells Rowan.
```

Graph lights:

```text
Mira -> told -> Rowan
Rowan -> believes -> theft_001
```

### Step 4: Talk To Rowan

Rowan says:

```text
"Mira told me what happened. You will not walk into the Guild hall trusted."
```

Point:

Rowan did not witness the theft. His reaction is grounded in social memory.

### Step 5: Talk To Sol

Sol says:

```text
"You look troubled. The shrine is open if you need to make something right."
```

Point:

Sol does not know the theft yet. Echo preserves partial knowledge.

### Step 6: Toggle Baselines

Graph-only:

```text
Rowan response is factual but stiff.
```

Vector-only:

```text
Sol may incorrectly know the theft or produce vague suspicion.
```

Cognee:

```text
Rowan knows through Mira; Sol does not know yet.
```

### Step 7: Repair Action

Player publicly apologizes at shrine and returns relic.

Memory updates:

```text
apology_001
return_001
reputation improves but theft remains in history
```

Mira says:

```text
"Returning what you took matters. Trust returns slower than relics."
```

### Step 8: Closing

"Echo does not give NPCs one shared global brain. It gives them social memory: who saw, who heard, who believes, and how meaning changes over time."

## 16. Agent / Service Stack

Echo should be implemented as a small set of focused services.

### 16.1 Game Client

Role: playable 2D interface.

Inputs:

- player movement,
- player actions,
- dialogue choices,
- mode toggle.

Outputs:

- game state,
- action events,
- rendered NPC dialogue,
- memory visualization.

Failure mode:

- gameplay feels too static or confusing.

Mitigation:

- keep actions simple,
- show current objective,
- use a scripted demo path.

### 16.2 Game State API

Role: backend source of truth for current session state.

Inputs:

- player action events,
- NPC interaction requests.

Outputs:

- updated local game state,
- event records,
- dialogue context,
- memory sync jobs.

Failure mode:

- state diverges between client and memory.

Mitigation:

- event-sourced log,
- deterministic IDs,
- read state from server after each action.

### 16.3 Memory Writer

Role: writes game events to Cognee Cloud.

Inputs:

- structured event,
- actor,
- witness,
- location,
- faction,
- semantic tags.

Outputs:

- Cognee memory write,
- local audit log.

Failure mode:

- Cognee write is slow or fails.

Mitigation:

- queue writes,
- show pending sync,
- do not block immediate gameplay.

### 16.4 Propagation Engine

Role: decides who learns what between interactions.

Inputs:

- social graph,
- event severity,
- relationship trust,
- NPC communication rules.

Outputs:

- new `TOLD` edges,
- belief updates,
- faction mood changes.

Failure mode:

- memory spreads too much and feels magical.

Mitigation:

- explicit propagation paths,
- visible fact log,
- cap propagation depth per turn.

### 16.5 Dialogue Composer

Role: generates grounded NPC lines.

Inputs:

- NPC known facts,
- belief certainty,
- relationship state,
- semantic memory,
- current player action.

Outputs:

- NPC dialogue,
- optional explanation of why line was chosen.

Failure mode:

- LLM hallucinates facts.

Mitigation:

- provide only facts that NPC knows,
- constrain output schema,
- reject lines that mention unknown events.

### 16.6 Memory Inspector

Role: powers the right-side memory visualization.

Inputs:

- event log,
- belief graph,
- faction state.

Outputs:

- graph nodes/edges,
- facts table,
- who-knows-what view,
- baseline comparison data.

Failure mode:

- visualization overwhelms the game.

Mitigation:

- show only active scenario path by default,
- allow expanded view for judges.

## 17. Architecture

Recommended architecture:

```text
Browser 2D game
  - Phaser/Pixi/React canvas
  - dialogue and action UI
  - memory visualization
        |
        v
Python or TypeScript backend API
  - session state
  - event log
  - propagation rules
  - dialogue requests
        |
        v
Cognee Cloud
  - session memory
  - durable graph/vector memory
  - background sync
  - recall for relevant prior events
```

### Why Browser Game Instead Of Unity/Unreal

Unity and Unreal are likely free for hackathon use, but they add unnecessary risk.

Use a browser game because:

- judges can open it instantly,
- frontend and backend are easier to deploy,
- Cognee integration is simpler,
- iteration is faster,
- the scoring category is Cognee memory, not engine fidelity.

Rule:

```text
The engine is the stage. The memory behavior is the product.
```

## 18. Key Technical Decisions

### Decision 1: Use Cognee Cloud

Reason: Track 2 rewards Cognee Cloud. Echo also benefits from cloud session memory and managed infrastructure.

### Decision 2: Use A 2D Browser Game

Reason: It gives enough game feel with minimal engine overhead. A 2D world is easier to polish and deploy in a 7-day solo build.

### Decision 3: Use A Scripted Sandbox, Not A Fully Open World

Reason: The demo must prove memory propagation. Open-ended scope can make the behavior inconsistent and hard to judge.

### Decision 4: Make Propagation Explicit

Reason: Cognee will not magically know social rules. Our code should create and explain propagation edges, then store them in Cognee.

### Decision 5: Keep LLM Dialogue Grounded

Reason: The LLM should phrase reactions, not decide facts. Facts come from graph memory and event state.

### Decision 6: Build Baselines From The Start

Reason: The project wins when judges see graph-only and vector-only fail in different ways.

## 19. Grilling Session: Hard Questions And Answers

### Q1: Is this just another AI NPC chatbot?

No. The core is not open-ended dialogue. The core is social memory: who saw an event, who was told, who believes it, and how that changes future behavior. The chatbot is only the visible surface.

### Q2: Why does this need Cognee instead of a normal database?

A database can store facts, but it does not understand semantic meaning. It can know "theft happened," but not naturally connect theft to betrayal, apology to repair, or bribery to guilt. Cognee combines exact relationships with semantic recall.

### Q3: Why does this need Cognee instead of vector memory?

Vector memory can retrieve related text, but it cannot reliably enforce who knows what. It may leak facts to NPCs who should not know them. Echo's proof depends on partial knowledge boundaries.

### Q4: What if the NPC dialogue is not impressive?

The demo should not rely only on dialogue quality. It should show the memory graph, fact log, and baseline comparison. Even simple dialogue can win if the memory behavior is clearly correct.

### Q5: What if Cognee is too slow for a game?

Heavy Cognee work must run outside the render loop. The game uses immediate local/session state for responsiveness and background sync for durable memory.

### Q6: What if propagation looks fake?

Every propagation must be explainable:

```text
Mira told Rowan because they are allies and meet at the guild hall.
Rowan believes Mira because trust(Mira, Rowan) is high.
```

If the UI cannot explain how an NPC learned something, the propagation should not happen.

### Q7: What is the "wow" moment?

The player steals from Mira, then Rowan reacts even though Rowan never saw it. Then Sol does not react because Sol was not told. The graph shows exactly why both reactions are correct.

### Q8: Is entertainment impact weaker than enterprise impact?

Yes, compared with Argus. Echo compensates through creativity, UX, and memorability. It is the submission judges are likely to remember emotionally.

### Q9: Could this be built without Cognee if we hardcode rules?

A tiny scripted demo can always be hardcoded. The submission must avoid looking hardcoded by showing:

- semantic similarity across different actions,
- memory persistence,
- baseline failures,
- inspectable Cognee memory operations,
- multiple paths through the same scenario.

### Q10: What should we refuse to build?

Refuse:

- full RPG systems,
- 3D engine complexity,
- unlimited NPC dialogue,
- many maps,
- combat,
- inventory economy,
- real-time graph rebuilds,
- invisible memory with no inspector.

## 20. Metrics

### Hero Metrics

- Knowledge correctness: percentage of NPC lines that only reference known facts.
- Propagation correctness: percentage of belief updates with valid social path.
- Baseline contrast: graph-only and vector-only failures captured in demo.
- Interaction latency: time from player action to visible reaction.
- Persistence: memory survives reload/session change.

### Experience Metrics

- Time to understand demo: target under 30 seconds.
- Number of clicks to reach wow moment: target under 5.
- Memory visualization clarity: judge can identify who knows what without reading source code.

### Cognee Usage Metrics

- Number of remembered events.
- Number of NPC belief nodes.
- Number of social propagation edges.
- Recall accuracy for prior events.
- Session memory round-trip time.

## 21. Failure Handling

Echo should be honest and inspectable when memory is missing.

If an NPC does not know:

```text
This NPC has no memory path to the event.
```

If Cognee sync is pending:

```text
Memory update queued. Local state is active; durable memory is syncing.
```

If dialogue validation fails:

```text
Generated line referenced an unknown fact and was rejected.
```

If propagation is blocked:

```text
Rumor did not spread because no social edge connects Mira to Sol.
```

If Cognee Cloud fails:

```text
Cloud memory unavailable. Showing local session state only.
```

## 22. Build Sequence

### Phase 0: Product Skeleton

- Create project repo after hackathon starts.
- Add game client, backend, docs.
- Add README thesis and demo script.

### Phase 1: Day-1 De-Risk Spike

- Connect backend to Cognee Cloud.
- Write one event with `session_id`.
- Recall it in a later interaction.
- Create one social propagation edge.
- Generate one grounded NPC response.
- Measure response latency.

Exit condition:

- Player action creates durable memory.
- A different NPC can react only after receiving a valid memory path.
- Gameplay does not block on heavy memory sync.

### Phase 2: Minimal Game Loop

- Build one map.
- Add player movement or click actions.
- Add 3 NPCs:
  - witness,
  - ally,
  - uninformed neutral.
- Add one item to steal/return.
- Add dialogue panel.

### Phase 3: Memory Visualization

- Add graph panel.
- Add fact log.
- Add belief table.
- Add faction mood meter.

### Phase 4: Baseline Toggle

- Implement graph-only response mode.
- Implement vector-only response mode.
- Implement Cognee hybrid mode.
- Record differences for README and video.

### Phase 5: Expanded Scenario

- Add 5 to 8 NPCs.
- Add 2 to 3 factions.
- Add apology, gift, lie, and rumor actions.
- Add persistence across reload.

### Phase 6: Polish

- Demo video.
- Hosted URL.
- README with architecture, screenshots, memory graph, and limitations.
- AI assistance disclosure.

## 23. Open Questions

1. Should the browser game use Phaser, Pixi, or a simpler React canvas implementation?
2. Will the backend be Python to align with Cognee, or TypeScript for simpler full-stack deployment?
3. Which exact Cognee Cloud APIs and session memory behavior should be verified first?
4. How many NPCs can we support without making the memory graph noisy?
5. Should dialogue be LLM-generated live or selected from grounded templates for demo reliability?
6. How much of `memify` should be used versus custom propagation rules stored back into Cognee?
7. What is the best visual style for a fast, polished 2D game?
8. How do we prove the demo is not hardcoded?

## 24. Acceptance Criteria

The Track 2 project is ready to submit when:

- A judge can open a hosted URL and play the scenario.
- Player action creates a visible memory event.
- Memory propagates through at least one valid social path.
- At least one NPC reacts to an event they did not witness but were told about.
- At least one uninformed NPC does not know the event.
- The UI shows who knows what and why.
- Graph-only and vector-only baselines fail in visible, understandable ways.
- Cognee Cloud is clearly the durable memory layer.
- Gameplay stays responsive.
- The README explains why pure vector and pure graph fail.
- The submission is honest about scripted scenario boundaries.

## 25. Reader Test Questions

Use these questions in a fresh reader review:

1. What is Echo building, in one sentence?
2. Why does Echo need Cognee Cloud?
3. Why is this not just an NPC chatbot?
4. What does the player do in the demo?
5. How does memory propagate?
6. How does Echo prevent NPCs from knowing facts they should not know?
7. What do graph-only and vector-only baselines fail to do?
8. Why are Unity and Unreal not the default choice?
9. What are the biggest risks?
10. What must be true before implementation starts?

