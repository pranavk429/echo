# Project Summary: Cognee Hackathon

Date: 2026-06-24  
Purpose: compact, durable project memory for future sessions.

## Current Objective

Prepare two separate Cognee hackathon submissions, one per prize track, but build them one at a time.

Primary build order:

1. Track 1: Argus, self-hosted Cognee causal SRE agent.
2. Track 2: Echo, Cognee Cloud NPC social-memory game.

## Workspace State

Workspace path:

```text
/Users/pranav1296/cognee
```

Important files:

- `CLAUDE.md`: original project brain with hackathon context, Cognee notes, and two ideas.
- `context.md`: shared planning context from research and brainstorming.
- `PROJECT_SUMMARY.md`: compact project memory for future continuation.
- `docs/superpowers/specs/2026-06-24-track1-argus-design.md`: Track 1 design spec.
- `docs/superpowers/specs/2026-06-24-track2-echo-design.md`: Track 2 design spec.
- `skills-lock.json`: local skill lock file.

Repository status:

- This workspace is not currently a git repository.
- Do not claim docs were committed unless a git repo is initialized later.

## Hackathon Context

Hackathon:

```text
Cognee "The Hangover Part AI: Where's My Context?" by WeMakeDevs
```

Theme:

```text
Build AI that does not forget. Use Cognee as the memory layer.
```

Judging criteria from the public page:

- Potential Impact.
- Creativity and Innovation.
- Technical Excellence.
- Best Use of Cognee.
- User Experience.
- Presentation Quality.

Tracks:

- Track 1: Best Use of Open Source / self-hosted Cognee.
- Track 2: Best Use of Cognee Cloud.

Rules and notes:

- Projects must be built from scratch after the hackathon begins.
- AI assistants are allowed but must be disclosed.
- The local `CLAUDE.md` and live hackathon page had a prize mismatch for Track 2. Verify prize details from the live page before submission copy is finalized.

## Cognee Mental Model

Cognee is the memory layer.

Simple model:

```text
Cognee = vector memory + graph memory + relational metadata
```

What each part means:

- Vector memory finds things by meaning.
- Graph memory follows relationships.
- Relational metadata tracks structured facts, timestamps, IDs, and datasets.

Winning idea filter:

```text
If pure-vector RAG could solve it, weak.
If pure-graph alone could solve it, weak.
If hybrid graph-vector memory is necessary, strong.
```

Important Cognee primitives and constraints:

- `remember`, `recall`, `forget`, `improve`.
- `cognify` builds memory from data.
- `memify` can enrich or improve memory after ingestion.
- `GRAPH_COMPLETION` is the flagship hybrid retrieval path.
- `CYPHER` requires a Cypher-capable graph backend such as Neo4j.
- `TEMPORAL` support exists, but exact timestamp schema should be discovered by spike.
- Cognee calls can be slow, so avoid synchronous heavy calls in real-time loops.
- LLMs should phrase answers, not invent facts.
- `memify` observability is DIY if we want to show before/after memory changes.

## Coral Hackathon Lessons

Reviewed:

- Coral hackathon page: `https://www.wemakedevs.org/hackathons/coral`
- Manthan winner: `https://github.com/akash-mondal/manthan`
- GSoC/Open-source Matchmaker winner: `https://github.com/yashhh-23/coral-powered-optimizer`
- Prior non-winning project Coral Reef: `https://github.com/pranavk429/coral-reef`

Winning formula:

1. Build around the sponsor's unique capability.
2. Use real data or live interaction.
3. Make the hidden capability visible.
4. Show a baseline failing.
5. Provide citations/provenance and honest failure handling.
6. Have one sentence judges can repeat.
7. Deploy and document like a real product.

Manthan's lesson:

```text
"A senior analyst spends 5 hours on a chargeback. Manthan spends 3 minutes."
```

The sponsor tech was structurally necessary. Coral made many SaaS sources queryable as one SQL surface. The demo showed real source citations and human approval.

Coral Reef lesson:

- Good domain, but the demo path used mock SQL / fixtures.
- Sponsor tech felt replaceable.
- Scope looked like a proof-of-concept.

Do not repeat:

- Do not make Cognee removable.
- Do not make mock data the main demo.
- Do not build a generic memory chatbot.
- Do not hide the graph/vector memory operation.

## Track 1: Argus

Track:

```text
Best Use of Open Source / self-hosted Cognee
```

One-liner:

```text
When production breaks, Argus traces the causal graph from symptom to exact deployed PR in seconds, while vanilla RAG confidently retrieves the wrong logs.
```

Plain English:

Argus is a production-bug detective. When checkout fails, it finds the root cause by connecting symptoms, logs, service dependencies, deploy timing, git commits, and PRs.

Core path:

```text
symptom
-> log event
-> failing service
-> dependency service
-> deploy before error
-> PR / commit
-> author
```

Why Cognee is necessary:

- Vector memory finds the relevant starting point from fuzzy language.
- Graph memory follows service and deploy relationships.
- Temporal filtering checks what happened before the failure.
- Semantic ranking chooses among candidate PRs after graph/time pruning.

Hero data:

- Google Online Boutique.
- One staged real fault with real commit/PR.
- Real logs, deploy timestamps, service topology, and git history.
- RCAEval only as support benchmark, mainly root-cause service accuracy.

Demo:

- Left: vanilla RAG retrieves similar but wrong/incomplete logs.
- Right: Argus animates causal path and timeline.
- Evidence chips link to logs, topology, deploy, commit/PR.

Critical risks:

- RAG accidentally succeeds, invalidating the proof.
- Too much time spent on observability stack.
- Graph animation is pretty but does not prove causality.
- Cognee temporal/Cypher behavior differs from assumptions.

Spec:

```text
docs/superpowers/specs/2026-06-24-track1-argus-design.md
```

## Track 2: Echo

Track:

```text
Best Use of Cognee Cloud
```

One-liner:

```text
NPCs do not just remember what you did; Cognee tracks who knows it, who believes it, and how it changes a faction you never met.
```

Plain English:

Echo is a small game simulation where NPCs have shared social memory. If the player steals from one NPC, that NPC remembers. If the NPC tells an ally, the ally reacts even without meeting the player.

Core path:

```text
player action
-> witness observes event
-> hard fact enters memory
-> fact propagates through social graph
-> faction sentiment changes
-> stranger NPC reacts differently later
```

Why Cognee is necessary:

- Graph memory stores facts: who saw what, who knows whom, factions, who was told.
- Vector memory stores meaning/tone: theft, betrayal, generosity, fear, trust.
- Hybrid memory creates factual but flexible NPC behavior.

Recommended implementation:

- 2D browser game, not Unity/Unreal.
- Phaser/Pixi/React canvas frontend.
- Python service connected to Cognee Cloud.
- Use Cloud session memory for fast interactions and background graph sync.

Why not Unity/Unreal:

- Unity is likely free for this use but adds C# and engine overhead.
- Unreal is likely free for hackathon use but is too heavy.
- Hackathon points come from memory behavior, not AAA graphics.

Demo:

- Player steals, lies, helps, or gives item.
- Witness NPC reacts.
- Memory graph lights up.
- Fact propagates to another NPC through faction/social edge.
- Stranger NPC reacts differently.
- Toggle shows graph-only, vector-only, and Cognee hybrid behavior.

Critical risks:

- NPCs feel like generic chatbots.
- Cognee calls block gameplay.
- Propagation seems magical or unfair.
- Game scope consumes too much time.

Spec:

```text
docs/superpowers/specs/2026-06-24-track2-echo-design.md
```

## Sequencing

Build order:

1. Argus first.
2. Echo second.

Reason:

- Argus is stronger on impact, technical excellence, and self-hosted Cognee use.
- Echo is stronger on creativity, UX, and memorability.
- Building both simultaneously risks two unfinished submissions.

## Next Steps

Immediate next step:

- Review both design specs:
  - `docs/superpowers/specs/2026-06-24-track1-argus-design.md`
  - `docs/superpowers/specs/2026-06-24-track2-echo-design.md`

Then:

1. Approve Track 1 Argus spec.
2. Create Argus implementation plan.
3. Build Argus Day-1 spike:
   - Cognee self-hosted,
   - Neo4j,
   - tiny sample ingestion,
   - graph traversal,
   - RAG baseline failure,
   - memory improvement instrumentation.
4. If Argus spike passes, build the Online Boutique hero incident.
5. Return to Echo after Argus is demo-ready.
