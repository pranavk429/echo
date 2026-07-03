# Handoff Prompt — Echo Day-1 Spike Execution

Copy everything below this line into the new agent session.

---

You are picking up a Cognee hackathon project at the start of build week. Read this entire prompt before doing anything.

## Your mission, in one sentence

Execute the **Day-1 de-risk spike** for **Echo** (Track 2 of the Cognee hackathon) — a one-day, 7-test Python spike against real Cognee Cloud that proves (or refutes) every load-bearing assumption before we commit the week to building.

## Read these files FIRST (in this order, fully)

1. `/Users/pranav1296/cog2/CLAUDE.md` — the project brain. Read it ALL. Pay special attention to §5 (Cognee API surface), §6 IDEA B (Echo), §8 (sequencing), and §9 (working agreement / rules). The rules in §9 are non-negotiable.
2. `/Users/pranav1296/cog2/echo_spec.md` — the full Echo design spec (Track 2).
3. `/Users/pranav1296/cog2/docs/superpowers/plans/2026-06-27-echo-day1-spike.md` — **the spike plan you are executing.** This is your primary work artifact. It has 9 tasks with checkbox steps, exact code, and a GO/PIVOT/DOWNGRADE decision matrix in Task 9.

Do not skip the reads. Do not summarize them in your head — read them fully. If anything in them contradicts this prompt, the files win.

## Project facts (do not re-litigate these — they are decided)

- **Hackathon:** Cognee "The Hangover Part AI: Where's My Context?" by WeMakeDevs, Jun 29 – Jul 5, 2026.
- **We are going for Track 2 ONLY in this project** (`/cog2`): "Best Use of Cognee Cloud." Track 1 (Argus) is a separate, already-handled project. Do not touch Argus.
- **The idea (Echo):** a 2D browser game where NPCs share social memory via Cognee Cloud. A witnessed theft becomes a graph fact (who-saw-what); the vector layer generalizes it into a faction-wide disposition; a stranger NPC with no personal knowledge edge to the event still shifts attitude via faction-scoped semantic recall. The moat: **Cognee's hybrid graph+vector memory is structurally necessary — pure vector leaks facts to uninformed NPCs, pure graph can't classify novel actions semantically.**
- **The user is non-technical.** They have the idea; you bring the architecture. Explain decisions in plain English when they ask. Do not ask them to pick between technical options unless a decision genuinely needs their input.
- **We have a free Cognee Cloud Developer plan** (1 month). The user will provide credentials.

## Design decisions ALREADY COMMITTED (from prior grilling sessions — do not re-debate)

These are locked. If you find a problem during the spike that challenges one, surface it to the user explicitly rather than silently changing direction.

1. **Cognee is the query engine, not just the store.** "What does this NPC know/feel" is ALWAYS a live Cognee `recall`, never a row we precomputed. This is what makes Cognee non-removable.
2. **2D browser game** (React + HTML canvas + tiny render loop), NOT Unity/Unreal. The judging rubric has no "engine quality" axis.
3. **Python backend** (Cognee is Python-first; `cognee` client is first-class there).
4. **6 NPCs, 3 factions** (Mira, Rowan, Sol, Niko, Vale, Ilya; Orchard Guild, Shrine Circle, Alley Network).
5. **Three-tier reaction ladder** for live-LLM reliability: Tier A grounded LLM line, Tier B templated grounded line, Tier C silent-state beat.
6. **Supply-side grounding:** the LLM composer is only ever given the NPC's known-event set; it cannot emit an event_id it wasn't handed.
7. **The toggle shows STRONG baselines, not strawmen** — the vector-only baseline uses per-NPC filtered namespaces; we still beat it on faction-reputation-blindness, not on fact-leaking.
8. **Open-action text box** for the anti-hardcode proof (free-text actions classified by archetype via vector similarity).
9. **Faction-scoped recall** is the core impossibility-filter pass (stranger-NPC disposition via vector, gated by faction membership edges).
10. **`improve()` (v1.0 memify)** is the self-improvement showpiece — custom enrichment tasks if the spike proves them, else `build_global_context_index` + `feedback_alpha` as fallback.

## Your task right now

Execute `/Users/pranav1296/cog2/docs/superpowers/plans/2026-06-27-echo-day1-spike.md` from Task 0 through Task 9.

**Load the `executing-plans` skill** (or `subagent-driven-development` if your harness supports subagents) and follow it. The plan uses checkbox syntax for a reason — track progress against it.

## Credentials (the user will provide these — do NOT invent them)

You need three secrets before you can run anything:
- `COGNEE_BASE_URL` — the user's Cognee Cloud tenant URL (from `platform.cognee.ai` → API Keys page)
- `COGNEE_API_KEY` — the user's Cognee Cloud API key
- `LLM_API_KEY` — an OpenAI (or Anthropic) key for Cognee's LLM calls

**Ask the user for these the moment you reach Task 0, Step 6.** Do not fabricate credentials. Do not commit them to git (the `.gitignore` in the plan already excludes `.env`).

## Rules you MUST follow (from CLAUDE.md §9, condensed)

- **Spike before relying on any Cognee capability with a ⚠️ caveat.** The whole point of this day is empirical verification.
- **No mock/fixture data in the demo path.** (This spike tests the real API — no mocks.)
- **Name real Cognee primitives** (`remember`, `recall`, `improve`, `SearchType.TEMPORAL`, `session_id`, `datasets`, `cognee.serve`). Do not invent API that isn't in the docs. The plan's code uses verified signatures.
- **If the spike goes RED, pivot without sentiment.** Do not push through a failed multi-hop test to "make the demo work." Report the failure honestly.
- **Instrument everything.** The spike logs JSONL with latency + raw answers for a reason — those numbers drive the build's hot-path design.
- **Do not commit secrets.** `.env` is gitignored; keep it that way.

## What "done" looks like (from the plan's closing)

A committed `echo-spike/` repo (likely under `/Users/pranav1296/cog2/echo-spike/`) with:
1. `spike_results.jsonl` — every test recorded with latency + raw answer.
2. `README.md` — the GO/PIVOT/DOWNGRADE decision and the latency numbers that drive the build's hot path.
3. A clear yes/no answer to: *"Did we prove the Impossibility Filter holds against the real Cognee Cloud API before committing the week?"*

## The decision matrix (Task 9 — the most important output)

| Result pattern | Decision |
|---|---|
| Tests 1, 2, 6 PASS | **GO.** Echo's thesis holds. 3, 4, 5, 7 are downgradable. |
| Test 2 FAIL (multi-hop) | **PIVOT.** Impossibility Filter broken. Do not build Echo as designed. |
| Test 6 FAIL (isolation), not fixable with `node_name` | **PIVOT.** Partial-knowledge boundary is the whole pitch. |
| Test 3 FAIL (session latency) | **DOWNGRADE hot path.** Add a local snapshot cache layer. |
| Test 4 FAIL (custom enrichment) | **DOWNGRADE Q7.** Use global context index + feedback_alpha. |
| Test 5 FAIL (temporal) | **DOWNGRADE Q8.** Replace with explicit `repairs:` edges. |
| Test 7 FAIL (classification) | **DOWNGRADE Q3.** Closed action enum. |

If you hit PIVOT: **STOP and surface to the user before doing anything else.** Do not attempt to salvage by re-scoping on your own. The user decides whether to pivot the whole project or re-scope Echo.

## How to communicate with the user

- They are non-technical. Explain any failure in plain English (what we assumed vs. what actually happened vs. what it means for the project).
- Be direct about GO/PIVOT. Do not soften a PIVOT into "we'll figure it out."
- When you need a decision from them, present it as a clear either/or with your recommendation.
- After the spike completes (whatever the outcome), tell them what the next step is: if GO, the next step is the full 7-day build plan; if PIVOT, the next step is reassessing scope together.

## Start

Begin by reading the three files listed at the top. Then announce which skill you're using to execute the plan, create the `echo-spike/` workspace, and proceed through Task 0. Ask for credentials when you need them. Track every checkbox. Report results as they come in.
