# Cognee Hackathon Context

Date: 2026-06-24  
Purpose: shared context for planning and building both Cognee hackathon tracks.

## 1. Current Situation

We are preparing for the Cognee "The Hangover Part AI: Where's My Context?" hackathon by WeMakeDevs.

Current local workspace:

- `CLAUDE.md`: original project brain.
- `context.md`: this shared summary.
- `PROJECT_SUMMARY.md`: compact project summary for future continuation.
- `docs/superpowers/specs/2026-06-24-track1-argus-design.md`: Track 1 design spec.
- `docs/superpowers/specs/2026-06-24-track2-echo-design.md`: Track 2 design spec.
- `skills-lock.json`: local skill lock file.

This workspace is not currently a git repository.

## 2. Hackathon Overview

Main theme:

> Build AI that does not forget. Use Cognee as the memory layer.

Important confirmed framing from the public hackathon page:

- The theme is open-ended.
- Projects can be agents, apps, tools, games, or automations.
- Cognee must be used for memory.
- Projects are judged on:
  - Potential Impact,
  - Creativity and Innovation,
  - Technical Excellence,
  - Best Use of Cognee,
  - User Experience,
  - Presentation Quality.
- Projects must be built from scratch after the hackathon begins.
- AI assistants are allowed but must be disclosed.

Track focus:

- Track 1: Best Use of Open Source / self-hosted Cognee.
- Track 2: Best Use of Cognee Cloud.

Prize note:

- `CLAUDE.md` said Track 2 prize was an iPhone 17.
- The live hackathon FAQ said Best Use of Cognee Cloud wins an iPad per team member.
- Treat the live website as more current than the local note, and verify prize details again before submission materials are finalized.

## 3. Cognee Overview

Cognee is an open-source AI memory platform for agents.

The important idea:

```text
Cognee = vector memory + graph memory + relational metadata
```

In simple terms:

- Vector memory understands meaning.
- Graph memory understands relationships.
- Relational storage tracks structured metadata.

The hackathon-winning opportunity is to build something that needs all of these at once.

Key Cognee concepts from our research:

- `remember`: high-level memory write flow.
- `recall`: high-level memory retrieval flow.
- `forget`: delete memory.
- `improve`: improve memory.
- `cognify`: ingestion/build pipeline for turning data into graph/vector memory.
- `memify`: self-improving post-processing/enrichment layer.
- `GRAPH_COMPLETION`: vector-seed plus graph traversal answer mode.
- `CYPHER`: structured graph query mode, requiring a Cypher-capable backend such as Neo4j.
- `TEMPORAL`: time-aware retrieval when temporal cognify is used.
- Ontology grounding can validate extracted facts and mark whether nodes are grounded.

Constraints:

- Cognee calls can take seconds, so do not put heavy memory calls in real-time loops.
- Cypher traversal needs Neo4j.
- `memify` needs our own observability if we want to show what changed.
- Temporal schema should be discovered with a spike, not assumed.
- LLMs should phrase answers, not invent facts.

## 4. Coral Hackathon Lessons

We reviewed the prior WeMakeDevs Coral hackathon because it had the same organizer pattern.

Referenced projects:

- Manthan: first-prize winner.
- Coral-powered optimizer / GSoC matchmaker: first-prize winner.
- Coral Reef: prior project that did not win.

Core lesson:

> Winners build around the sponsor's unique capability. Non-winners often use sponsor tech as a removable layer.

### Manthan Pattern

Manthan's thesis:

> A senior analyst spends 5 hours on a chargeback. Manthan spends 3 minutes.

Why it worked:

- Clear business pain.
- Clear time-saving number.
- Coral was structurally necessary.
- It queried many SaaS sources through one SQL surface.
- It showed citations and human approval.
- It had a polished README and deployed demo.

### GSoC Matchmaker Pattern

The matchmaker connected LeetCode skill profiles to GitHub issues.

Why it worked:

- Narrow, understandable user problem.
- Coral connected two very different data sources.
- The output was actionable: open issue links.
- It had live frontend and backend deployment.

### Coral Reef Lesson

Coral Reef had a reasonable idea: compliance evidence collection.

Why it likely lost:

- Main demo used mock SQL / fixtures.
- Coral was replaceable by the mock engine.
- Only seven controls, which felt small.
- It read more like a proof-of-concept than a real sponsor-native product.

Do-not-repeat list:

- Do not make mock data the main demo path.
- Do not make Cognee removable.
- Do not build a generic chatbot with memory.
- Do not over-scope and under-polish.
- Do not hide the sponsor capability.

## 5. Winning Formula For Cognee

Every idea should pass this filter:

```text
If Pinecone-only RAG could do it, the idea is weak.
If Neo4j-only graph could do it, the idea is weak.
If Cognee's hybrid graph-vector memory is necessary, the idea is strong.
```

Winning artifact pattern:

1. A one-sentence thesis judges can repeat.
2. Real data or live interaction.
3. Visible memory traversal/propagation.
4. Baseline comparison showing failure without Cognee.
5. Citations and provenance.
6. One strong number or unforgettable moment.
7. Polished README and demo video.

## 6. Track 1: Argus

Track:

> Best Use of Open Source / self-hosted Cognee.

Project:

> Argus, a causal SRE agent that finds the root cause of production incidents.

One-liner:

> When production breaks, Argus traces the causal graph from symptom to exact deployed PR in seconds, while vanilla RAG confidently retrieves the wrong logs.

Plain English:

When an app breaks, engineers need to find out what changed. Logs might show checkout failures, but the real cause may be a change in another service. Argus uses Cognee memory to connect fuzzy symptoms, logs, service relationships, deploy timing, and git history.

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

- Vector memory finds the starting point from human language.
- Graph memory follows dependencies and deploy relationships.
- Time filtering ensures causes happened before symptoms.
- Semantic ranking chooses among candidate PRs after graph/time pruning.

Hero demo:

- Use Google Online Boutique.
- Stage one real fault with a real commit/PR.
- Capture real logs and deploy timestamps.
- Ingest real service topology and git history.
- Ask vanilla RAG and Argus the same question.
- Show RAG failing and Argus finding the cause.

Support benchmark:

- Use RCAEval for root-cause service accuracy, not exact PR claims unless data supports it.

Main UI:

- Left: RAG baseline results.
- Right: Argus causal path.
- Center/side: 2D graph traversal and timeline.
- Evidence chips link to logs, deploys, commits, and topology.

Primary risks:

- RAG accidentally succeeds.
- Time is wasted on observability stack plumbing.
- The graph visualization becomes pretty but not explanatory.
- Cognee temporal/Cypher behavior differs from assumptions.

Current spec:

- See `docs/superpowers/specs/2026-06-24-track1-argus-design.md`.

## 7. Track 2: Echo

Track:

> Best Use of Cognee Cloud.

Project:

> Echo, a game NPC hive-mind where NPCs remember what the player did and social memory propagates through factions.

One-liner:

> NPCs do not just remember what you did; Cognee tracks who knows it, who believes it, and how it changes a faction you never met.

Plain English:

Most game NPCs forget everything. In Echo, if the player steals from one NPC, that NPC remembers. If that NPC tells an ally, the ally can react even if the player never met them. The world changes because memory spreads through relationships.

Core path:

```text
player action
-> witness NPC observes fact
-> Cognee stores event
-> memory propagates through social graph
-> other NPC changes attitude
-> future dialogue changes
```

Why Cognee is necessary:

- Graph memory stores hard facts:
  - who saw what,
  - who knows whom,
  - faction membership,
  - who has been told.
- Vector memory stores meaning and tone:
  - theft,
  - betrayal,
  - generosity,
  - fear,
  - trust.
- Cognee hybrid lets NPCs react with both factual accuracy and semantic nuance.

Baseline comparison:

- Graph-only NPC remembers literal facts but cannot generalize emotion well.
- Vector-only NPC has vague memory but cannot track who knows what.
- Cognee NPC combines facts, relationships, and tone.

Recommended stack:

- 2D browser game, not Unreal.
- Phaser/Pixi/React canvas frontend.
- Python service connected to Cognee Cloud.

Reason:

- Fastest to build.
- Easiest to deploy.
- Judges can open it instantly.
- The winning element is memory behavior, not AAA graphics.

Unity/Unreal note:

- Unity Personal is free for small teams under the relevant revenue/funding threshold.
- Unreal is free for this hackathon use and generally charges royalties only after substantial product revenue.
- Even though both are feasible, Unreal is overkill and Unity adds engine overhead. A browser game is the pragmatic choice.

Demo:

```text
player steals item
-> witness reacts
-> graph lights up
-> memory spreads to faction member
-> stranger NPC distrusts player
```

Primary risks:

- Calling Cognee synchronously in the game loop causes latency.
- NPC behavior feels like generic chat instead of structured memory.
- Propagation rules are unclear.
- The game consumes time that should go into memory proof.

Current spec:

- See `docs/superpowers/specs/2026-06-24-track2-echo-design.md`.

## 8. Sequencing

We are going for both tracks, one at a time.

Recommended order:

1. Build Track 1 Argus first.
2. Build Track 2 Echo second.

Reason:

- Argus is closer to the Manthan winning pattern:
  - painful real-world problem,
  - measurable impact,
  - strong technical depth,
  - sponsor-native memory architecture.
- Echo is more creative and memorable, but should not distract from first shipping a strong Track 1 entry.

## 9. Shared Demo Principles

Both projects need the same showpiece pattern:

### The Toggle

Show the same input with and without Cognee.

Argus:

```text
RAG fails; Cognee finds causal path.
```

Echo:

```text
graph-only and vector-only fail differently; Cognee creates believable social memory.
```

### The Cinematic

Make memory visible.

Argus:

```text
animated causal graph traversal and timeline.
```

Echo:

```text
animated social memory propagation.
```

### The Trust Layer

Never make unsupported claims.

Argus:

```text
log, topology, deploy, commit citations.
```

Echo:

```text
fact log showing who saw what and how each NPC learned it.
```

### The Simple Sentence

Each project needs a sentence judges can repeat.

Argus:

```text
RAG found logs; Argus found the cause.
```

Echo:

```text
NPCs remember what you did, who knows it, and how it changes the world.
```

## 10. Immediate Next Steps

1. Review both specs:
   - `docs/superpowers/specs/2026-06-24-track1-argus-design.md`
   - `docs/superpowers/specs/2026-06-24-track2-echo-design.md`
2. Approve Track 1 Argus as the first build target.
3. Create an implementation plan for Argus.
4. Build the Day-1 de-risk spike:
   - Cognee self-hosted,
   - Neo4j,
   - tiny sample ingestion,
   - temporal query,
   - RAG baseline,
   - one memory improvement log.
5. If spike passes, build the hero Online Boutique incident.
6. Return to Echo implementation planning only after Argus is demo-ready.

## 11. Sources Reviewed

- Cognee hackathon page: `https://www.wemakedevs.org/hackathons/cognee`
- Cognee GitHub repo: `https://github.com/topoteretes/cognee`
- Cognee docs: `https://docs.cognee.ai`
- Coral hackathon page: `https://www.wemakedevs.org/hackathons/coral`
- Manthan repo: `https://github.com/akash-mondal/manthan`
- Coral-powered optimizer repo: `https://github.com/yashhh-23/coral-powered-optimizer`
- Coral Reef repo: `https://github.com/pranavk429/coral-reef`
- RCAEval repo: `https://github.com/phamquiluan/RCAEval`
- Google Online Boutique: `https://github.com/GoogleCloudPlatform/microservices-demo`
