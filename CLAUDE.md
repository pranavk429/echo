# CLAUDE.md — Cognee Hackathon Project ("Where's My Context?")

> **What this file is:** the shared brain for any AI agent (or human) working on this
> project. Read it fully before proposing code or a plan. This is **context, not a build
> spec** — it captures the mission, the constraints, the winning architecture, the verified
> facts about Cognee, and the two candidate ideas in depth. Detailed specs come **later**,
> per idea, once one is locked for execution.

---

## 0. TL;DR

We are entering the **Cognee "The Hangover Part AI: Where's My Context?https://www.wemakedevs.org/hackathons/cognee** hackathon
(WeMakeDevs, **Jun 29 – Jul 5, 2026**). We are **not** building a chatbot-with-memory.https://github.com/topoteretes/cognee
We are building an **architectural breakthrough** that proves Cognee's core thesis:

> **Hybrid graph + vector memory unlocks categories of AI that are impossible with pure
> vector or pure graph alone.**

Two ideas are documented here, one per prize track:

- **Track 1 (Best Use of Open Source / self-hosted):** **Argus** — a Causal SRE agent that
  finds a production bug's root cause by *causal graph traversal*, not log search.
- **Track 2 (Best Use of Cognee Cloud):** **Echo** — a game NPC "hive-mind" where NPCs
  remember what you did (graph) and a grudge propagates across a faction (vector + graph).

Builder is **solo**, window is **7 days**. We have a **free Cognee Cloud Developer plan
(1 month)** for Track 2.

---

## 1. Mission & success definition

- **Win first prize.** Among thousands of strong, senior-level entrants. Generic = lose.
- **Prove the impossibility thesis.** Every design decision must showcase something that a
  pure-vector RAG (e.g. Pinecone) **cannot** do and a pure-graph DB (e.g. Neo4j alone)
  **cannot** do. If either alone could do it, the idea is dead.
- **Be the use case the sponsor wants to showcase** — something they have "never seen
  before," that validates why hybrid graph-vector memory is a new category.
- **Save real time/money or create a genuinely new experience**, on **real data / live
  interaction**, deployed and runnable — never on mock fixtures.

---

## 2. The hackathon — facts

- **Event:** Cognee "The Hangover Part AI: Where's My Context?" (WeMakeDevs).
- **Dates:** Jun 29 – Jul 5, 2026.
- **Theme:** open-ended. "Give your AI a memory." Build anything (agents, apps, tools,
  games, automations) as long as Cognee is the memory layer. Games are explicitly allowed.
- **Two Grand Prizes = our two tracks:**
  - **Track 1 — "Best Use of Open Source":** best build on **self-hosted open-source
    Cognee.** Prize: Apple MacBook (per team member).
  - **Track 2 — "Best Use of Cognee Cloud":** best build on **Cognee Cloud** (managed).
    Prize: iPhone 17 (per team member). **We have a free Developer plan for this.**
- **Side tracks (bonus, not our focus):** Open-Source Track ($100/PR, top 20 — upstream
  fixes we hit during the build to farm this), Best Blogs, Social Buzz.
- **Judging criteria (six — design every artifact to score on these):**
  1. **Potential Impact** — does it solve a meaningful problem?
  2. **Creativity & Innovation** — unique, not a clone.
  3. **Technical Excellence** — execution quality + depth of Cognee integration.
  4. **Best Use of Cognee** — does it *deeply* use the memory lifecycle, not bolt it on?
  5. **User Experience** — intuitive interface / demo.
  6. **Presentation Quality** — README, demo video, clarity of the pitch.
- Top winners get Cognee job interviews (not a guarantee).

---

## 3. Who we are & hard constraints

- **Solo developer. 7-day build window.** This dominates every scope decision.
- **Prior result to learn from:** we entered the **Coral** hackathon (same organizer) with
  project **coral-reef** (compliance-evidence agent) and **lost**. The autopsy below is the
  most valuable asset in this file. Do not repeat those mistakes.
- **"Both tracks" caveat:** the two tracks are **mutually-exclusive infra** (self-hosted
  OSS vs managed Cloud), so one project cannot win both — going for both means two
  projects. See **§8 Reality & sequencing** for the honest solo guidance. Both ideas are
  documented as first-class regardless.

---

## 4. The winning architecture — six laws (from the Coral autopsy)

We dissected the two Coral winners (Manthan; the GSoC/OSS matchmaker) against our loss.
The pattern is unambiguous:

1. **Built *around* the sponsor's one unique capability — not bolted on.** Manthan's whole
   thesis ("think in joins — one wide query instead of one round-trip per source") is
   meaningless without Coral. **coral-reef used Coral as a removable queryable layer — that
   was the kill shot.** For us: the app must be *impossible* without hybrid graph-vector.
2. **No mock data. Ever.** coral-reef's #1 loss reason: the demo ran on fixtures, so judges
   saw a *simulation*, not a product. Winners ran live on real APIs, deployed.
3. **A one-sentence thesis a judge can repeat.** "5 hours → 3 minutes." If we can't compress
   it to a sentence, it won't survive the judging room.
4. **Make the invisible capability *visible*.** Manthan rendered SQL fanning across 11
   sources live. Memory is invisible by default — our demo must *render the graph being
   traversed / the grudge propagating*.
5. **Trust engineering.** Citations / provenance (no fabrication), honest failure handling,
   human-in-the-loop on actions, real references. Look like something you'd trust.
6. **Quantify + deploy + document.** One hero number, a live URL, a magazine-grade README.

### The Impossibility Filter (the gate every feature must pass)

> If a **Pinecone-only RAG** could do it → dead. If a **Neo4j-only graph** could do it → dead.

The asymmetric advantage of Cognee is the **synchronized hybrid layer** (every graph node
has an embedding, so you move between semantic similarity and relational traversal without
losing coherence). That unlocks four things neither side can do alone:

| Capability | Why pure-vector fails | Why pure-graph fails |
|---|---|---|
| **Multi-hop reasoning over facts that never co-occur in one document** | RAG retrieves passages; can't synthesize A (doc 1) + B (doc 50) joined by an inferred edge | Can traverse, but can't find the entry node from fuzzy natural language |
| **Temporal evolution & contradiction resolution** | Retrieves both contradictory chunks, averages to mush | No semantic ranking of which version matters now |
| **Self-improving memory (`memify`)** — reweight / prune / derive edges by usage | No structure to reweight | No semantic signal to drive enrichment |
| **Ontology-grounded provenance** (`ontology_valid`) | Can't separate grounded fact from hallucination | No fuzzy recall over validated nodes |

### coral-reef's death modes — the DO-NOT-REPEAT list

- Mock/fixture data instead of live integrations.
- Cognee (then Coral) used as a removable layer, not the architectural core.
- Toy scope (7 controls) that reads as a proof-of-concept.
- Low polish / traction signals (1 star, no deploy, "built with AI assistance" framing).

---

## 5. Cognee — verified capabilities (the real API surface)

> These are **verified from Cognee docs/source as of this research**, with caveats. Name
> these real primitives in code and README — judges score "Best Use of Cognee." Do **not**
> invent API. When in doubt, run a spike against the live library before relying on it.

**Storage model:** hybrid **graph + vector + relational**, kept **synchronized** (every
graph node has a corresponding embedding). Pluggable backends: graph (Kuzu default / Neo4j
/ Neptune / Postgres), vector (LanceDB default / pgvector / Chroma / Qdrant), relational
(SQLite / Postgres).

**High-level API:** `remember` (= `add` + `cognify` + `improve`), `recall` (auto-routes to
the best search strategy), `forget` (delete data, e.g. a dataset, with relational
integrity), `improve`. Also `cognee.serve()` (run as a service) and session memory.

**`cognify` — the build pipeline (6-stage ECL):** classify docs → check permissions →
extract text chunks → LLM extracts `(subject, relation, object)` triplets → generate
summaries → embed + commit edges to the graph. **Incremental** (only new/changed files
re-process). LLM-heavy ⇒ **seconds, not frame-time** (see latency caveat).

**`memify` — self-improving post-processing layer.** Refines the graph *after* ingestion
without a full rebuild: prune stale nodes, strengthen frequent edges, reweight by usage,
derive new facts. **Controllable:** `memify(extraction_tasks=[...], enrichment_tasks=[...])`
with custom functions wrapped as `Task(...)`; plugin-based, parameterized — **you can write
custom edge-reweighting / propagation logic as an enrichment task.**
⚠️ **Observability is DIY:** memify exposes no built-in diff/audit of what changed. If we
want a "memory improves with use" curve, **we instrument it ourselves** (log what our
enrichment task changes + run our own before/after eval). Budget time for this.

**Search — `SearchType` enum (14 retrieval modes). Key ones:**
- `GRAPH_COMPLETION` (flagship): vector-seed → walk matching triplets → LLM composes a
  natural-language answer. This is the core "hybrid" retrieval. Returns prose (good for
  chat, not for machine-parsing).
- `GRAPH_COMPLETION_COT` (iterative chain-of-thought) and
  `GRAPH_COMPLETION_CONTEXT_EXTENSION` (multi-round context) — upgrades for hard queries.
- `CYPHER`: run **raw Cypher** with `WHERE` filters, returns structured graph data (no LLM).
  ⚠️ **Requires a Cypher-capable backend — i.e. Neo4j. The default in-memory/Kuzu graph will
  NOT run Cypher.** Results come nested in a `search_result` structure (write extractors).
- `TEMPORAL`: time-aware retrieval. Enabled by cognifying with `temporal_cognify=True`,
  which builds an **event-based graph** — timestamps modeled as **dedicated nodes**, events
  carry start/end timestamps + `before`/`after`/`during` relationships.
  ⚠️ The exact timestamp node labels/properties are **undocumented — discover them via a
  spike** (`MATCH (n) RETURN n LIMIT 100`) before writing temporal Cypher filters.
- Others: `RAG_COMPLETION`, `CHUNKS`, `SUMMARIES`, `INSIGHTS`, `NATURAL_LANGUAGE`, etc.

**Ontology grounding:** supply an OWL/RDF (or Pydantic-modeled) ontology; an OWL/RDF
resolver validates LLM-extracted entities against it and stamps each node with an
`ontology_valid` flag → **distinguish grounded facts from hallucinations.** Tightening the
ontology also constrains extraction (kills junk triplets at the source).

**Cognee Cloud (Track 2):** managed/hosted version. Adds **session memory** ("fast cache,
syncs to the graph in the background" via `session_id`) — *this is the latency escape hatch
for real-time apps like the game.* Plus hosted `serve()`. We have a free 1-month Developer
plan.

**Constraints to respect (cross-cutting):**
- `cognify`/`recall` are **slow (seconds)** — never call synchronously in a real-time loop.
- `CYPHER` ⇒ **must run Neo4j backend.**
- `memify` is controllable but **not observable out of the box.**
- Temporal node schema must be **discovered**, not assumed.
- Always model **time as first-class node properties** and enforce ordering in the query —
  do not trust the LLM to infer "before/after."

---

## 6. The two ideas (detailed context — NOT specs)

### IDEA A — Track 1 (Open Source / self-hosted): **Argus** — Causal SRE Agent

**One-liner:** *When production breaks, Argus finds the root cause by traversing the causal
graph from symptom to the exact PR — not by searching logs.*

**Domain:** DevTools / production reliability (SRE). Self-hosted because code + logs are
sensitive and we need the Neo4j backend.

**The concept.** Ingest into Cognee: structured logs / stack traces (as typed error
events), the service dependency topology (from k8s manifests / compose files — *free,
deterministic*), git history (real commits/PRs/authors), and deploy events. When a bug
occurs, Argus performs **causal graph traversal** to locate the cause, instead of returning
similar log chunks.

**The moat (why it's impossible without hybrid).** A production bug is a *cascade*:
> API endpoint **A** fails (semantic log) → because it calls service **B** (graph edge) →
> which was recently changed by **PR #42** (commit graph + deploy event) → which introduced
> a lock on table **C** (schema graph).
Pure-vector RAG retrieves logs that *look like* the symptom and stops — it cannot connect a
symptom to a cause that lives in a different document, reached only via a dependency edge +
temporal order. Pure-graph can traverse but can't find the entry node from a fuzzy natural
-language symptom or rank by relevance. **Cognee combines semantic log analysis with
structural call-graph traversal — that's the whole pitch.**

**The crux that makes the proof valid (most important design rule).** The impossibility
proof only holds if **symptom and root cause are *semantically disjoint*** — they share no
vocabulary, so the *only* bridge is the dependency edge + temporal order. (E.g. a memory
leak in `currencyservice` surfacing as 500s in `checkout` — "currency" never appears in a
"checkout timeout" log.) **Engineer this deliberately, and verify on tape that vanilla RAG
fails on it.** Anchor the proof on the *structural cascade*, NOT on matching a PR's commit
message to the symptom (that hop is partly vector-doable and a sharp judge will say so).

**Data strategy (two tiers — kills both coral-reef death modes at once).**
- **Tier 1 — Hero demo (full real chain):** stage one fault on **Google Online Boutique
  (`microservices-demo`)** ourselves. Gives the *complete real chain*: real telemetry we
  capture (docker logs → typed events; **no heavy Prometheus/Loki/Tempo stack**), real
  topology (manifests), and a **real PR we commit** (real diff/author/timestamp). Lets us
  *guarantee* semantic disjointness. Ingest the repo's **full real git log** as noise so
  Argus finds the needle in a real haystack (not a 5-node toy).
- **Tier 2 — Credibility / anti-"toy":** replay **RCAEval** (github.com/phamquiluan/RCAEval;
  WWW'25) — 735 real failure cases, metrics+logs+traces, annotated root-cause service, 11
  fault types, across **Online Boutique / Sock Shop / Train Ticket**. **Download the CSVs
  only** (skip their 50 GB reproduction env). Report root-cause-**service** accuracy@k on a
  peer-reviewed public benchmark vs their 15 baselines. *Elegant overlap:* RCAEval includes
  Online Boutique, so Tier 1 and Tier 2 share one topology + git ingestion.
- ⚠️ **Honesty rule:** RCAEval gives ground-truth *service* + *indicator*, NOT the exact
  PR/author for chaos faults. Claim "finds the exact PR + author" only for Tier 1 (and
  RCAEval's *code-level* fault subset). On Tier 2 claim only *service* accuracy.

**Key Cognee primitives:** deterministic ingestion of structured data (logs/manifests/git)
as typed nodes + LLM extraction only for unstructured text (PR descriptions) gated by
`ontology_valid`; **Neo4j backend**; `GRAPH_COMPLETION` for the answer; `CYPHER` for the
structural traversal; `temporal_cognify=True` + timestamp ordering for "PR-before-error";
`memify` enrichment task that strengthens confirmed `symptom→cause` edges (self-improving
runbook + an accuracy-improves-with-use curve).

**The false-positive funnel (this *is* the technical story):** all deploys (~500) →
**temporal cut** (deploys before the error, in window) → ~3–8 → **topology cut** (BFS
upstream over `DEPENDS_ON` from the failing service) → ~1–3 → **vector rank** (error context
↔ PR diff) → top-1. Structure + time prune; semantics rank; no single filter suffices.

**The demo (the win screen):** side-by-side **toggle** — left: vanilla RAG returns 5
confidently-irrelevant log chunks; right: Argus renders the **2D animated traversal path**
(error → pulse along edges → PR → author) + a **timeline strip** ("deploy 14:10 → errors
14:13") + the **number** ("human: ~18 min; Argus: ~4 s"). Close with the **memify
improvement curve**. **2D path, not 3D** (3D is an unreadable hairball; judges must read the
path in 5 s).

**Scope guards:** **AST ingestion is a stretch goal, not core** — the cascade needs a call
-graph + commit-graph + schema-graph, which manifests + git already give us ~80%. Don't
rabbit-hole on AST. **No full observability stack** — logs→events, manifests→topology.

**Pre-mortem (the 3 ways Argus dies):** (1) RAG accidentally works ⇒ defuse with day-1
disjointness test on tape; (2) looks like a toy ⇒ defuse with real git-history noise + a
real PR + RCAEval; (3) time sunk on observability plumbing ⇒ banned after day 2.

---

### IDEA B — Track 2 (Cognee Cloud): **Echo** — NPC Hive-Mind

**One-liner:** *NPCs that remember you stole their apple (graph) and turn their whole
faction against you (vector) — and the grudge spreads to NPCs you never met.*

**Domain:** games / interactive narrative. Most on-theme idea (the hackathon is literally
named after a memory-loss comedy), and it kills coral-reef's two death modes **for free**:
**no mock data** (the player generates real interactions live on stage) and **inherently
visual** (Law 4 — memory becomes a watchable graph).

**The concept.** A small world of NPCs (5–8) sharing one Cognee memory substrate. The graph
tracks **hard facts and structure** — faction alliances, locations, inventory, who-did-what,
and **who-knows-what**. The vector layer tracks **narrative themes, tone, and past dialogue**.
NPCs converse with the player and each other; memory persists across sessions.

**The moat (the real breakthrough — lead with this, not the apple).** The apple is the
*skin*; the breakthrough is **partial, propagating, multi-agent memory**:
- **Graph-only NPC** knows you stole the apple but *can't generalize* the grudge to the
  faction (no semantic similarity) — it only resents the literal apple.
- **Vector-only NPC** has a vague "bad vibe" but *forgets the literal fact* and *can't track
  which NPCs know* (no structure for who-knows-what).
- **Cognee hybrid:** the hard fact (graph) **propagates along faction/`KNOWS` edges** to
  NPCs who never met you, and the **semantic grudge (vector) generalizes** the offense into
  a faction-wide disposition. *Neither store does this alone* — clean Impossibility Filter
  pass.

**Key Cognee primitives & how the hard parts are solved:**
- **Latency (the #1 restriction):** never call `cognify`/`recall` synchronously in the game
  loop. Memory **writes go async/background**; reads use **Cloud session memory** (fast
  cache → background graph sync) — this feature exists *exactly* for real-time apps. The
  render loop never blocks on the graph.
- **Hive-mind propagation is OUR code, not a Cognee freebie.** Cognee won't auto-diffuse a
  fact from NPC-A to NPC-B. Model it explicitly: `(NPC)-[:KNOWS]->(Event)` +
  `(NPC)-[:ALLIED_WITH/TOLD]->(NPC)` edges, and a **`memify` enrichment task** that spreads
  facts along those edges between interactions. *This is also the architectural showpiece.*
- **Anti-hallucination:** hard facts come from the **graph** (did-you-steal-the-apple is a
  boolean, + `ontology_valid` grounding); the **vector** layer sets tone; the **LLM only
  phrases** the line — it never invents *what happened*. Protects the "they remember
  accurately" promise.
- **Cost:** bound it — few NPCs, batch background `cognify`, don't re-cognify every utterance.

**Stack decision (critical for solo-7-day):** Cognee is **Python**; engines are C#/C++.
The judging rubric has **no "engine quality" axis** — a 3D village scores the same as a 2D
top-down on "Best Use of Cognee." **Default recommendation: a 2D browser game
(Phaser/Pixi) talking to a Python Cognee service over HTTP** — minimal bridge tax, instant
iteration, frees the whole week for the memory layer. Unity/Unreal are **free** for us
(Unity Personal < $200k; Unreal free < $1M/title) and *possible* (engine ↔ HTTP ↔ Python
`cognee.serve()`), but the bridge + scene/asset/controller overhead costs ~2–3 solo days for
zero extra judging credit. **Only use Unity if already fluent in C#; never Unreal for this.**

**The demo (the win screen):** three NPCs side-by-side — **graph-only / vector-only /
Cognee** — react to the same player action. Only Cognee's faction turns on you. Plus a
**live graph visualization** of the grudge *propagating* across faction edges to NPCs the
player never met. The judges can *poke it live* — memorability wins the room.

**Strategic note (honest):** competes in the **Creativity & UX lane**; scores high there and
likely *lower* on Potential Impact (entertainment, not infra ROI). That's a **contrarian
advantage** — ~90% of entrants will build enterprise memory chatbots; a playable hive-mind
is what judges remember walking out.

**Restrictions recap:** latency wall (→ async + session memory), propagation-is-our-code
(→ `memify` enrichment), engine bridge (→ 2D web), hallucination (→ graph facts + LLM
phrasing only), cost (→ few NPCs + batching).

---

## 7. Cross-cutting "win the room" pattern (applies to both ideas)

Every winning demo here has the same three artifacts:
1. **The toggle** — same input, pure-RAG vs Cognee, side by side. RAG fails; Cognee does the
   impossible thing. *This proves the thesis on stage.*
2. **The cinematic** — render the otherwise-invisible memory: the graph being traversed
   (Argus) / the grudge propagating (Echo). 2D, legible, animated.
3. **The number / the moment** — one quantified before/after (Argus) or one undeniable live
   reaction (Echo), on real data / live play, at a deployed URL.
Plus: trust engineering (provenance, honest failure, no fabrication) and a magazine-grade
README + demo video.

---

## 8. Reality & sequencing (honest architect note)

Both ideas are documented as first-class because that was the explicit ask. But the solo +
7-day constraint is real, and the two stacks share **almost nothing** (DevTools/Python/Neo4j
/data vs game/web/real-time). Building both well is not realistic; two half-built projects
across two stacks lose to one polished one.

**Guidance:** pick **one as primary** and ship it to first-prize polish; treat the other as
a *fast-follow only if* the primary is done and demo-ready with days to spare. Whichever is
chosen, **day 1 is a de-risk spike, not feature work** (prove the Impossibility Filter holds
against real Cognee API before committing the week). If the day-1 spike is red, pivot
without sentiment.

- **Argus day-1 spike:** stand up Cognee + **Neo4j**; `temporal_cognify=True` then
  `MATCH (n) RETURN n LIMIT 100` to learn the timestamp schema; write one temporal Cypher
  filter; build vanilla RAG on the same corpus and **record it failing** the disjoint hero
  query; write a trivial `memify` enrichment task and confirm the change persists.
- **Echo day-1 spike:** Cloud session-memory async write/read round-trip under game-loop
  timing; one `KNOWS`-edge propagation via a `memify` task; the 3-NPC toggle skeleton.

---

## 9. Working agreement (rules for the agent)

- **Pass the Impossibility Filter or don't build it.** If pure-vector or pure-graph could do
  it, stop.
- **No mock/fixture data in the demo path.** Real data or live interaction only.
- **Cognee is the architectural core, never a removable layer.**
- **Name real Cognee primitives** (§5); don't invent API; **spike before relying** on any
  capability with a ⚠️ caveat.
- **Model time as node properties; enforce ordering in queries**, not via LLM inference.
- **Graph = hard facts; vector = semantics/tone; LLM = phrasing only.** Don't let the LLM
  invent facts.
- **Day 1 = de-risk spike.** Verify the proof empirically before committing the week.
- **Guard scope ruthlessly** (solo, 7 days): AST deferred (Argus); 2D web over a game engine
  (Echo); no heavy observability stack; few NPCs.
- **Instrument `memify` ourselves** if we want the self-improvement curve (no built-in
  observability).
- **Build for the three win-the-room artifacts** (§7) from the start, not as an afterthought.
- **Upstream any Cognee bug/fix we hit** → free Open-Source side-track points.

---

## 10. Key references

- Cognee repo: github.com/topoteretes/cognee · Docs: docs.cognee.ai
- SearchType: docs.cognee.ai/python-api/search-type · Temporal: docs.cognee.ai/guides/time-awareness
- memify pipeline writeup (Medium, @cognee) · RCAEval: github.com/phamquiluan/RCAEval (arXiv:2412.17015)
- Online Boutique: Google `microservices-demo` · Hackathon: wemakedevs.org/hackathons/cognee
- Cloud Developer plan code: `COGNEE-35` (free, 1 month) — for Track 2.
