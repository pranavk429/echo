# Echo — Day-1 De-Risk Spike Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** In one day, prove that the real Cognee Cloud API does every load-bearing thing Echo's design assumes — or learn exactly which assumptions are wrong and pivot before committing the week.

**Architecture:** A single Python script (`echo_spike.py`) run against **Cognee Cloud** (via the free Developer plan). Each test is isolated, prints a clear PASS/FAIL with latency, and writes a JSONL result log. No game code, no frontend, no database of our own. Pure API verification.

**Tech Stack:** Python 3.11+, `cognee` pip package, Cognee Cloud tenant, an LLM provider key (OpenAI or Anthropic), `time.perf_counter` for measurement, stdlib `json`/`pathlib`/`asyncio`.

---

## Why this spike exists (read before running)

CLAUDE.md §9 is explicit: *"Day 1 = de-risk spike. Verify the proof empirically before committing the week. If the day-1 spike is red, pivot without sentiment."*

Every assumption Echo rests on has been pulled from docs and CLAUDE.md notes — but docs lie, versions drift, and the ⚠️-caveated primitives (`improve` custom tasks, `TEMPORAL`, session memory) are exactly the ones we cannot ship without. The spike is the empirical ground-truth pass.

**This spike is RED if any of these go red:**
1. Cannot connect to Cognee Cloud and round-trip a `remember`/`recall`.
2. `recall` cannot answer a question whose answer lives in a *different ingested sentence* than the question's keywords (the multi-hop claim — the core of the Impossibility Filter).
3. Session memory is not meaningfully faster than full graph recall (kills the "responsive gameplay" promise — the #1 Echo restriction).
4. `improve()` with a custom `enrichment_tasks` callable silently does nothing or raises (kills the self-improvement showpiece).
5. `TEMPORAL` recall returns nothing on a scoped before/after query (kills the repair-resolution mechanic — apologies-after-theft need temporal ordering).
6. The partial-knowledge demo (a stranger NPC has *no* path to an event) cannot be reproduced — i.e., recall leaks across datasets or can't be scoped.

If 1–6 are red, we do NOT build Echo. We pivot (Track 1 is already won elsewhere; we either re-scope Echo to what the spike proves, or write the loss up honestly).

---

## File Structure

```
echo-spike/
├── echo_spike.py           # one async script, 7 spike tests + harness
├── .env.example            # template for secrets (COGNEE_BASE_URL, COGNEE_API_KEY, LLM key)
├── .gitignore              # ignores .env, spike_results.jsonl, __pycache__
├── requirements.txt        # pinned: cognee, python-dotenv
├── README.md               # how to run, how to read the results
└── spike_results.jsonl     # created at runtime; one JSON object per test run
```

`echo_spike.py` is the only code file. Each test is a standalone async function `test_N_<name>(ctx) -> dict` returning `{name, passed, latency_ms, detail, raw_answer}`. The harness runs them in order, appends each result to `spike_results.jsonl`, and prints a summary table. A test never stops the run — failures cascade into the log for triage.

---

## Pre-flight: environment + secrets

### Task 0: Create the spike workspace and Python environment

**Files:**
- Create: `echo-spike/requirements.txt`
- Create: `echo-spike/.env.example`
- Create: `echo-spike/.gitignore`

- [ ] **Step 1: Create the directory and venv**

```bash
mkdir -p echo-spike
cd echo-spike
python3.11 -m venv .venv
source .venv/bin/activate
```

If `python3.11` is missing, use `python3 -m venv .venv` — Cognee needs ≥3.10.

- [ ] **Step 2: Pin dependencies**

Create `echo-spike/requirements.txt`:

```
cognee>=0.1.30
python-dotenv>=1.0.0
```

(Pin to the latest stable `cognee` on the day the spike runs. Verify with `pip show cognee` after install and record the version in `spike_results.jsonl` via the harness — see Task 1.)

- [ ] **Step 3: Install**

```bash
pip install -r requirements.txt
```

Expected: completes without error. If `cognee` fails to install, this is spike-red before any code runs — report it and stop.

- [ ] **Step 4: Create `.env.example`**

Create `echo-spike/.env.example`:

```
# Cognee Cloud — copy from platform.cognee.ai → API Keys
COGNEE_BASE_URL=https://your-tenant.aws.cognee.ai
COGNEE_API_KEY=your-api-key

# LLM provider — Cognee needs one for cognify/recall. OpenAI is simplest.
LLM_PROVIDER=openai
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini

# Vector / graph backends are managed by Cloud — do NOT set them.
```

- [ ] **Step 5: Create `.gitignore`**

Create `echo-spike/.gitignore`:

```
.env
.venv/
__pycache__/
spike_results.jsonl
```

- [ ] **Step 6: Copy to `.env` and fill in real values**

```bash
cp .env.example .env
```

Edit `.env` with the real Cognee Cloud tenant URL + API key (from `platform.cognee.ai` → API Keys page) and a real LLM key.

---

## The harness and the 7 tests

### Task 1: Write the harness

**Files:**
- Create: `echo-spike/echo_spike.py`

The harness: loads env, connects to Cognee Cloud via `cognee.serve()`, records the installed `cognee` version, runs each test function, logs JSONL, prints a summary, disconnects.

- [ ] **Step 1: Write the skeleton with `connect`, `log`, `summary`, `disconnect`**

Create `echo-spike/echo_spike.py`:

```python
import asyncio
import json
import os
import time
from pathlib import Path

import cognee
from dotenv import load_dotenv

load_dotenv()

RESULTS_PATH = Path("spike_results.jsonl")
RESULTS_PATH.unlink(missing_ok=True)


def log_result(result: dict) -> None:
    with RESULTS_PATH.open("a") as f:
        f.write(json.dumps(result) + "\n")
    flag = "PASS" if result["passed"] else "FAIL"
    print(f"[{flag}] {result['name']}  ({result['latency_ms']} ms)")
    if result.get("detail"):
        print(f"        {result['detail']}")


def timed(fn):
    async def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        try:
            payload = await fn(*args, **kwargs)
            passed = payload.get("passed", True)
            detail = payload.get("detail", "")
            raw = payload.get("raw", None)
        except Exception as e:
            passed = False
            detail = f"EXCEPTION: {type(e).__name__}: {e}"
            raw = None
        latency_ms = int((time.perf_counter() - t0) * 1000)
        return {
            "name": fn.__name__.replace("test_", ""),
            "passed": passed,
            "latency_ms": latency_ms,
            "detail": detail,
            "raw_answer": raw,
        }

    return wrapper


async def connect() -> dict:
    import importlib.metadata as md
    version = md.version("cognee")
    await cognee.serve(
        url=os.environ["COGNEE_BASE_URL"],
        api_key=os.environ["COGNEE_API_KEY"],
    )
    log_result({
        "name": "cognee_version",
        "passed": True,
        "latency_ms": 0,
        "detail": f"cognee=={version}",
        "raw_answer": version,
    })
    return {"cognee_version": version}


async def main():
    ctx = await connect()
    tests = [
        test_1_cloud_roundtrip,
        test_2_multi_hop_disjoint,
        test_3_session_vs_graph_latency,
        test_4_improve_custom_enrichment,
        test_5_temporal_scoped_recall,
        test_6_partial_knowledge_isolation,
        test_7_open_action_classification,
    ]
    for test in tests:
        result = await test(ctx)
        log_result(result)
    await cognee.disconnect()
    print("\n=== SPIKE SUMMARY ===")
    passed = sum(1 for line in RESULTS_PATH.read_text().splitlines() if json.loads(line).get("passed"))
    total = sum(1 for _ in RESULTS_PATH.open())
    print(f"{passed}/{total} checks passed. See spike_results.jsonl.")


if __name__ == "__main__":
    asyncio.run(main())
```

The `@timed` decorator is applied per-test below. Each test isolates its own dataset (via `dataset_name=...`) so parallel runs don't contaminate each other.

- [ ] **Step 2: Smoke-test the harness**

Add a throwaway test, run `python echo_spike.py`, confirm you see the version line and a clean exit (the 7 tests will be undefined errors — that's fine for this step, we're proving the harness boots against Cloud).

Expected: `[PASS] cognee_version` line printed, then a clean traceback about a missing test name. Fix the traceback by adding tests below; the connection itself is the gate.

- [ ] **Step 3: Commit**

```bash
git init && git add -A && git commit -m "spike: harness + env scaffold for Echo day-1 de-risk"
```

---

### Task 2: Test 1 — Cloud roundtrip (`remember` + `recall`)

**The claim:** Cognee Cloud accepts data via `remember()` and returns it via `recall()`.

**Pass condition:** The answer mentions "Cognee" or "memory" — i.e., the round-trip works end-to-end on Cloud.

- [ ] **Step 1: Write the test**

```python
@timed
async def test_1_cloud_roundtrip(ctx):
    await cognee.forget(everything=True)
    await cognee.remember(
        "Cognee is the memory layer for this Echo spike. It stores facts.",
        dataset_name="spike_t1",
    )
    results = await cognee.recall(
        query_text="What does Cognee store?",
        datasets=["spike_t1"],
    )
    answer = " ".join(str(r) for r in results).lower()
    passed = "fact" in answer or "memory" in answer
    return {
        "passed": passed,
        "detail": "round-trip OK" if passed else f"unexpected answer: {answer[:200]}",
        "raw": answer[:500],
    }
```

- [ ] **Step 2: Run it**

```bash
python echo_spike.py
```

Expected: `[PASS] cloud_roundtrip  (<latency> ms)`. Record the latency — this is the baseline for a cold `cognify`-on-write. Expect 2–10s on Cloud.

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "spike: test 1 cloud roundtrip"
```

**If FAIL:** Cognee Cloud credentials, networking, or LLM provider misconfig. Fix before continuing — every other test depends on this.

---

### Task 3: Test 2 — Multi-hop across disjoint sentences (THE Impossibility Filter test)

**The claim:** `recall` can answer a question whose answer requires connecting two facts that live in *different* ingested sentences and share no keywords with the question. This is the **single most important test** in the spike — it's the Q1/Q4 moat.

**Pass condition:** Asking about the *fruit* (never named in the theft sentence) returns an answer that correctly identifies the apple theft and that Mira saw it.

- [ ] **Step 1: Write the test — ingest two semantically disjoint facts**

```python
@timed
async def test_2_multi_hop_disjoint(ctx):
    await cognee.forget(everything=True)
    await cognee.remember(
        [
            "Mira tends the orchard stall in Lumen Market.",
            "Someone took the red fruit from the stall while Mira was watching.",
            "Rowan is a guard allied with Mira.",
            "The red fruit is called an apple.",
        ],
        dataset_name="spike_t2",
    )
    results = await cognee.recall(
        query_text="What happened to the apple, and who witnessed it?",
        datasets=["spike_t2"],
    )
    answer = " ".join(str(r) for r in results).lower()
    has_apple = "apple" in answer or "fruit" in answer
    has_mira = "mira" in answer
    passed = has_apple and has_mira
    return {
        "passed": passed,
        "detail": (
            "multi-hop OK" if passed
            else f"apple={has_apple} mira={has_mira}: {answer[:200]}"
        ),
        "raw": answer[:500],
    }
```

- [ ] **Step 2: Run it**

```bash
python echo_spike.py
```

Expected: `[PASS] multi_hop_disjoint`. If this passes, the Impossibility Filter holds empirically.

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "spike: test 2 multi-hop disjoint (impossibility filter)"
```

**If FAIL — this is the most important failure to interpret:**
- If `apple` is missing: Cognee isn't connecting the entity across sentences. Try `top_k=20` and a more pointed query. Still failing → the LLM provider may be weak (try a stronger model).
- If `mira` is missing: the witness relationship didn't extract. Try rephrasing the ingest as `"Mira saw someone take the apple from the stall."` (more direct triplet) and re-run.
- If **both fail after rephrasing**: this is spike-RED. Echo's whole pitch is multi-hop reasoning. Pivot.

---

### Task 4: Test 3 — Session memory vs. full graph recall latency

**The claim:** Session memory (fast cache, `session_id`) is meaningfully faster than a full graph `recall`. This is the Q6 hot-path claim — Echo's "responsive gameplay" depends on it.

**Pass condition:** `median(session_recalls) < 0.5 × median(graph_recalls)` AND `median(session_recalls) < 500 ms`.

- [ ] **Step 1: Write the test**

```python
@timed
async def test_3_session_vs_graph_latency(ctx):
    import statistics
    await cognee.forget(everything=True)
    await cognee.remember(
        "Echo is a village where NPCs share social memory through Cognee.",
        dataset_name="spike_t3",
    )

    async def timed_call(coro_fn):
        t0 = time.perf_counter()
        await coro_fn()
        return (time.perf_counter() - t0) * 1000

    session_id = "spike_t3_session"

    async def session_recall():
        return await cognee.recall(
            query_text="What is Echo?",
            session_id=session_id,
            datasets=["spike_t3"],
        )

    async def graph_recall():
        return await cognee.recall(
            query_text="What is Echo?",
            datasets=["spike_t3"],
        )

    # Warm the session with one write, so the cache has something
    await cognee.recall(query_text="What is Echo?", session_id=session_id, datasets=["spike_t3"])

    session_times = [await timed_call(session_recall) for _ in range(5)]
    graph_times = [await timed_call(graph_recall) for _ in range(5)]

    s_med = statistics.median(session_times)
    g_med = statistics.median(graph_times)
    passed = (s_med < 0.5 * g_med) and (s_med < 500)
    return {
        "passed": passed,
        "detail": f"session_med={int(s_med)}ms graph_med={int(g_med)}ms ratio={s_med/g_med:.2f}",
        "raw": {"session_ms": session_times, "graph_ms": graph_times},
    }
```

- [ ] **Step 2: Run it**

```bash
python echo_spike.py
```

Expected: `[PASS] session_vs_graph_latency`. Numbers go in the design doc — they drive the snapshot-cache aggressiveness in the real build (Q6).

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "spike: test 3 session vs graph latency"
```

**If FAIL (interpret by the numbers, not the boolean):**
- `s_med < 500ms` but ratio > 0.5: session is fast but not *dramatically* faster. Workable — adjust the design to use session memory for *recent* context and accept graph recall for full knowledge.
- `s_med > 500ms`: session memory isn't fast enough for the hot path. The design must mirror a snapshot locally (Q6 Tier 2); the Cloud session cache becomes a warm-backup, not the hot read.
- Session recall returns nothing: the session cache may need an explicit write step. Check the Sessions guide; if session writes need a separate API, add it.

---

### Task 5: Test 4 — `improve()` with a custom enrichment task (the memify showpiece)

**The claim:** `improve()` accepts a custom `enrichment_tasks` callable and the change persists in a subsequent `recall`. This is the Q7 self-improvement mechanic.

**Pass condition:** After `improve()` with a custom task, a `recall` returns an answer that reflects the enrichment (e.g., a derived summary phrase that wasn't in the original ingest).

**⚠️ This is the most likely test to fail** because the custom-task API surface is the least-documented. Approach defensively: try the high-level API first; if it silently no-ops, fall back to checking whether `improve()` with `build_global_context_index=True` produces observable change.

- [ ] **Step 1: Write the test — try custom enrichment first**

```python
@timed
async def test_4_improve_custom_enrichment(ctx):
    await cognee.forget(everything=True)
    await cognee.remember(
        [
            "The thief stole a golden relic from Mira's stall.",
            "Mira cried out when she saw the theft.",
            "Rowan heard Mira's cry.",
        ],
        dataset_name="spike_t4",
        self_improvement=False,  # we'll improve manually
    )

    baseline = await cognee.recall(
        query_text="Summarize what happened at the stall.",
        datasets=["spike_t4"],
    )
    baseline_text = " ".join(str(r) for r in baseline).lower()

    async def add_faction_insight(data=None, **kwargs):
        # A trivial custom enrichment: emit a derived summary string.
        # Real implementation would write a node/edge; this proves the hook fires.
        return ["The theft at Mira's stall harmed the Orchard Guild's trust."]

    try:
        await cognee.improve(
            dataset="spike_t4",
            enrichment_tasks=[add_faction_insight],
        )
        improved = await cognee.recall(
            query_text="Summarize what happened at the stall.",
            datasets=["spike_t4"],
        )
        improved_text = " ".join(str(r) for r in improved).lower()
        passed = "guild" in improved_text and "guild" not in baseline_text
        return {
            "passed": passed,
            "detail": (
                "custom enrichment observable" if passed
                else f"baseline_has_guild={'guild' in baseline_text} improved_has_guild={'guild' in improved_text}"
            ),
            "raw": {"baseline": baseline_text[:300], "improved": improved_text[:300]},
        }
    except Exception as e:
        # Fallback: does build_global_context_index at least change something?
        await cognee.improve(dataset="spike_t4", build_global_context_index=True)
        improved = await cognee.recall(
            query_text="Summarize what happened at the stall.",
            datasets=["spike_t4"],
        )
        improved_text = " ".join(str(r) for r in improved).lower()
        passed = len(improved_text) > 10  # got *some* answer back
        return {
            "passed": passed,
            "detail": f"FALLBACK global_context_index only; custom hook raised {type(e).__name__}: {e}",
            "raw": improved_text[:300],
        }
```

- [ ] **Step 2: Run it**

```bash
python echo_spike.py
```

Expected: `[PASS] improve_custom_enrichment` (custom path) or `[PASS]` via fallback (weaker but workable).

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "spike: test 4 improve custom enrichment"
```

**If FAIL:** Custom enrichment tasks may require a specific signature or registration. Check the `improve` docstring on the installed version (`python -c "import cognee; help(cognee.improve)"`); if the callable signature differs, update and re-run. If still no-op: drop custom enrichment from scope, fall back to `build_global_context_index` + `feedback_alpha` as the "self-improvement" mechanic, and adjust Q7's win-the-room artifact accordingly. This is a downgrade, not a kill.

---

### Task 6: Test 5 — Temporal scoped recall

**The claim:** `remember(temporal_cognify=True)` + `recall(SearchType.TEMPORAL)` returns scoped before/after answers. This is the Q8 repair-resolution mechanic (apology-after-theft).

**Pass condition:** A "before/after" query returns events in the correct temporal scope.

- [ ] **Step 1: Write the test**

```python
@timed
async def test_5_temporal_scoped_recall(ctx):
    from cognee.api.v1.search import SearchType
    await cognee.forget(everything=True)
    await cognee.remember(
        "At 9:00 the player stole the relic. "
        "At 9:05 Mira confronted the player. "
        "At 9:20 the player returned the relic. "
        "At 9:25 Mira thanked the player.",
        dataset_name="spike_t5",
        temporal_cognify=True,
        self_improvement=False,
    )

    results = await cognee.recall(
        query_type=SearchType.TEMPORAL,
        query_text="What happened before 9:10?",
        datasets=["spike_t5"],
        top_k=10,
    )
    answer = " ".join(str(r) for r in results).lower()
    has_theft = "stole" in answer or "relic" in answer or "theft" in answer
    has_return = "return" in answer or "thank" in answer
    passed = has_theft and not has_return
    return {
        "passed": passed,
        "detail": (
            "temporal scope OK" if passed
            else f"theft={has_theft} return_leaked={has_return}: {answer[:200]}"
        ),
        "raw": answer[:500],
    }
```

- [ ] **Step 2: Run it**

```bash
python echo_spike.py
```

Expected: `[PASS] temporal_scoped_recall`.

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "spike: test 5 temporal scoped recall"
```

**If FAIL:**
- If `has_return` leaks: temporal scoping is fuzzy. Try a more explicit time format (`2026-06-27T09:00:00Z`) and stricter query phrasing.
- If `has_theft` is missing: the temporal ingest didn't pick up events. Inspect with a plain `GRAPH_COMPLETION` recall on the same data to see what was extracted.
- If **both fail**: drop the apology-repair mechanic from the core demo; show repair via an explicit `repairs:` edge we write ourselves + standard recall. (A downgrade — Q8 weakens — but Echo still ships.)

---

### Task 7: Test 6 — Partial-knowledge isolation (the stranger-NPC proof)

**The claim:** A `recall` scoped to one dataset does NOT surface facts from a different dataset, AND recall on a *separate* dataset that has no path to the event returns nothing about it. This is the Q1/Q2 partial-knowledge guarantee — the boundary that makes vector-only look bad by contrast.

**Pass condition:** Stranger dataset recall returns nothing about the theft; witness dataset recall does.

- [ ] **Step 1: Write the test — two datasets, one knows, one doesn't**

```python
@timed
async def test_6_partial_knowledge_isolation(ctx):
    await cognee.forget(everything=True)

    # Mira's world: she witnessed the theft
    await cognee.remember(
        "Mira saw the player steal the golden relic from the orchard stall.",
        dataset_name="spike_t6_mira",
    )

    # Sol's world: he was never told, knows nothing about any theft
    await cognee.remember(
        "Sol tends the shrine and meditates. Sol knows nothing about recent events.",
        dataset_name="spike_t6_sol",
    )

    mira_recall = await cognee.recall(
        query_text="Did anyone steal anything?",
        datasets=["spike_t6_mira"],
    )
    mira_answer = " ".join(str(r) for r in mira_recall).lower()

    sol_recall = await cognee.recall(
        query_text="Did anyone steal anything?",
        datasets=["spike_t6_sol"],
    )
    sol_answer = " ".join(str(r) for r in sol_recall).lower()

    mira_knows = "steal" in mira_answer or "relic" in mira_answer or "theft" in mira_answer
    sol_leaks = "relic" in sol_answer or "theft" in sol_answer or "mira" in sol_answer
    passed = mira_knows and not sol_leaks
    return {
        "passed": passed,
        "detail": (
            "isolation OK" if passed
            else f"mira_knows={mira_knows} sol_leaked={sol_leaks}"
        ),
        "raw": {"mira": mira_answer[:300], "sol": sol_answer[:300]},
    }
```

- [ ] **Step 2: Run it**

```bash
python echo_spike.py
```

Expected: `[PASS] partial_knowledge_isolation`.

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "spike: test 6 partial knowledge isolation"
```

**If FAIL:**
- If `sol_leaks`: dataset isolation isn't enforced. This is a **major** design constraint — either Cloud RBAC (`ENABLE_BACKEND_ACCESS_CONTROL`) needs to be on, or we need per-NPC *node sets* instead of datasets (see Search Basics doc on `node_name` filtering). Re-test with `node_name=["sol_namespace"]` scoping.
- If `mira_knows` is False: the same recall is failing on a known-good query. Recheck Test 1.

---

### Task 8: Test 7 — Open-action archetype classification (the anti-hardcode proof)

**The claim:** A novel action described in free text is classified into a known archetype by vector similarity, *without* that action being in any seed table. This is the Q3 anti-hardcode proof — the strongest answer to "this is scripted."

**Pass condition:** A query about an action never explicitly ingested ("threatened Niko with a knife") returns a response that classifies it as a threat/violence (negative valence), surfacing the semantically nearest seed action.

- [ ] **Step 1: Write the test — seed archetypes, then probe a novel action**

```python
@timed
async def test_7_open_action_classification(ctx):
    await cognee.forget(everything=True)
    await cognee.remember(
        [
            "Stealing from a merchant is an act of theft with strongly negative valence.",
            "Giving medicine to a sick child is an act of generosity with positive valence.",
            "Lying about a theft is an act of deception with negative valence.",
            "Publicly apologizing at the shrine is an act of remorse with positive valence.",
        ],
        dataset_name="spike_t7",
    )

    # A novel action — never ingested, not in any seed table
    results = await cognee.recall(
        query_text="I threatened Niko with a knife. What kind of act is this and what is its valence?",
        datasets=["spike_t7"],
    )
    answer = " ".join(str(r) for r in results).lower()
    is_negative = any(w in answer for w in ["negative", "violence", "threat", "harmful", "aggression"])
    mentions_seed = any(w in answer for w in ["theft", "deception", "stealing"])
    passed = is_negative
    return {
        "passed": passed,
        "detail": (
            "novel action classified" if passed
            else f"not classified as negative: {answer[:200]}"
        ),
        "raw": answer[:500],
    }
```

- [ ] **Step 2: Run it**

```bash
python echo_spike.py
```

Expected: `[PASS] open_action_classification`.

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "spike: test 7 open action classification"
```

**If FAIL:** The seed library may be too small, or the query too leading. Try rephrasing the probe ("I drew my blade and demanded Niko's coin") and/or expanding the seed set with a clearer "threat/violence" example. If it still can't classify a never-ingested action, the anti-hardcode proof weakens — Echo falls back to a closed action enum and loses its strongest differentiation. Spike-yellow, not red.

---

## Triage the results

### Task 9: Read the results and decide GO / PIVOT / DOWNGRADE

- [ ] **Step 1: Read the summary**

```bash
cat spike_results.jsonl
```

- [ ] **Step 2: Apply the decision matrix**

| Result pattern | Decision |
|---|---|
| Tests 1, 2, 6 PASS (the core three) | **GO.** Echo's thesis holds. 3, 4, 5, 7 are downgradable. |
| Test 2 FAIL (multi-hop) | **PIVOT.** The Impossibility Filter is broken — Cognee can't do the join. Do not build Echo as designed. |
| Test 6 FAIL (isolation) and not fixable with `node_name` | **PIVOT.** Partial-knowledge boundary is the whole pitch; without it, the toggle proves nothing. |
| Test 3 FAIL (session latency) | **DOWNGRADE hot path.** Add a local snapshot cache (Q6 Tier 2). Echo ships but needs an extra layer. |
| Test 4 FAIL (custom enrichment) | **DOWNGRADE Q7.** Use `build_global_context_index` + `feedback_alpha` as the self-improvement showpiece instead of custom tasks. |
| Test 5 FAIL (temporal) | **DOWNGRADE Q8.** Replace temporal recall with explicit `repairs:` edges written by our code + standard recall. |
| Test 7 FAIL (classification) | **DOWNGRADE Q3.** Fall back to closed action enum; lose the open-action wow-beat. Echo still wins on the toggle + propagation. |

- [ ] **Step 3: Write the spike outcome into the project memory**

Append to `echo-spike/README.md` (create it):

```markdown
## Spike Outcome — <DATE>

- cognee version tested: <from spike_results.jsonl>
- Tests passed: X/7
- Decision: GO / PIVOT / DOWNGRADE
- Downgrades applied: <list>
- Latency findings (median session recall, median graph recall): <numbers>
- Notes for the build plan: <anything surprising>
```

- [ ] **Step 4: Commit and report**

```bash
git add -A && git commit -m "spike: outcome recorded — <GO|PIVOT|DOWNGRADE>"
```

Then surface the outcome to the human. If GO: the next step is the full 7-day build plan. If PIVOT: stop, reassess scope with the human. If DOWNGRADE: list the downgrades and write the adjusted build plan.

---

## Time budget

| Block | Hours |
|---|---|
| Task 0 (env + secrets) | 0.5 |
| Task 1 (harness) | 0.5 |
| Task 2 (Test 1) | 0.5 |
| Task 3 (Test 2) | 1.0 |
| Task 4 (Test 3) | 1.0 |
| Task 5 (Test 4) | 1.5 |
| Task 6 (Test 5) | 0.5 |
| Task 7 (Test 6) | 0.5 |
| Task 8 (Test 7) | 0.5 |
| Task 9 (triage + outcome) | 0.5 |
| **Total** | **~7 hours** |

A full day, with buffer. If Tasks 0–3 are green by lunch, the afternoon is Tests 4–7 + triage. If Task 2 (multi-hop) goes red, stop and surface to the human *immediately* — do not burn the afternoon on the downgradable tests.

---

## What "done" looks like

A committed `echo-spike/` repo with:
1. A `spike_results.jsonl` recording every test with latency + raw answer.
2. A `README.md` with the GO/PIVOT/DOWNGRADE decision and the latency numbers that will drive the build's hot-path design.
3. A clear answer, per CLAUDE.md §9, to: "did we prove the Impossibility Filter holds against the real Cognee Cloud API before committing the week?"
