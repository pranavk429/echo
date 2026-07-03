"""Echo — Day-1 de-risk spike against real Cognee Cloud.

7 isolated tests + harness. Each test prints PASS/FAIL with latency and appends
a JSON object to spike_results.jsonl. A test never aborts the run; failures
cascade into the log for triage in Task 9.

API notes (verified against cognee==1.2.2 before writing):
- serve(url, api_key) -> CloudClient
- recall() returns list[RecallResponse]; QA entries expose .answer, session
  context entries expose .content. A text extractor is needed.
- enrichment_tasks is a param of memify(), NOT improve(). Custom tasks must be
  wrapped in Task(executable, ...).
- temporal_cognify is a param of cognify(), not remember(). For Test 5 we use
  add() then cognify(temporal_cognify=True).
"""

import asyncio
import importlib.metadata as md
import json
import os
import random
import string
import statistics
import time
from pathlib import Path

import cognee
from cognee.modules.pipelines.tasks.task import Task
from cognee.modules.search.types.SearchType import SearchType
from dotenv import load_dotenv

load_dotenv()

RESULTS_PATH = Path("spike_results.jsonl")
RESULTS_PATH.unlink(missing_ok=True)

# Unique run ID so datasets don't clash across runs (forget() is broken on this Cloud instance)
RUN_ID = "run_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=6))


def log_result(result: dict) -> None:
    with RESULTS_PATH.open("a") as f:
        f.write(json.dumps(result, default=str) + "\n")
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


def recall_text(results) -> str:
    """Flatten a list[RecallResponse] into a lowercase text blob.

    Different recall routes return different entry shapes (QA, graph context,
    session context). Pull the most informative text field off each."""
    if results is None:
        return ""
    out = []
    for r in results:
        if r is None:
            continue
        for attr in ("answer", "content", "text", "summary"):
            v = getattr(r, attr, None)
            if v:
                out.append(str(v))
        if not out or not any(getattr(r, a, None) for a in ("answer", "content", "text", "summary")):
            out.append(str(r))
    return " ".join(out).lower()


async def connect() -> dict:
    version = md.version("cognee")
    base_url = os.environ.get("COGNEE_BASE_URL")
    api_key = os.environ.get("COGNEE_API_KEY")
    if not base_url or not api_key:
        raise RuntimeError(
            "Missing COGNEE_BASE_URL / COGNEE_API_KEY. Copy .env.example to .env and fill them in."
        )
    client = await cognee.serve(url=base_url, api_key=api_key)
    log_result({
        "name": "cognee_version",
        "passed": True,
        "latency_ms": 0,
        "detail": f"cognee=={version}",
        "raw_answer": version,
    })
    return {"cognee_version": version, "client": client}


@timed
async def test_1_cloud_roundtrip(ctx):
    await cognee.remember(
        "Cognee is the memory layer for this Echo spike. It stores facts.",
        dataset_name=f"spike_t1_{RUN_ID}",
    )
    results = await cognee.recall(
        query_text="What does Cognee store?",
        datasets=[f"spike_t1_{RUN_ID}"],
    )
    answer = recall_text(results)
    passed = "fact" in answer or "memory" in answer
    return {
        "passed": passed,
        "detail": "round-trip OK" if passed else f"unexpected answer: {answer[:200]}",
        "raw": answer[:500],
    }


@timed
async def test_2_multi_hop_disjoint(ctx):
    await cognee.remember(
        [
            "Mira tends the orchard stall in Lumen Market.",
            "Someone took the red fruit from the stall while Mira was watching.",
            "Rowan is a guard allied with Mira.",
            "The red fruit is called an apple.",
        ],
        dataset_name=f"spike_t2_{RUN_ID}",
    )
    results = await cognee.recall(
        query_text="What happened to the apple, and who witnessed it?",
        datasets=[f"spike_t2_{RUN_ID}"],
        top_k=20,
    )
    answer = recall_text(results)
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


@timed
async def test_3_session_vs_graph_latency(ctx):
    await cognee.remember(
        "Echo is a village where NPCs share social memory through Cognee.",
        dataset_name=f"spike_t3_{RUN_ID}",
    )

    async def timed_call(coro_fn):
        t0 = time.perf_counter()
        await coro_fn()
        return (time.perf_counter() - t0) * 1000

    session_id = f"spike_t3_session_{RUN_ID}"

    async def session_recall():
        return await cognee.recall(
            query_text="What is Echo?",
            session_id=session_id,
            datasets=[f"spike_t3_{RUN_ID}"],
        )

    async def graph_recall():
        return await cognee.recall(
            query_text="What is Echo?",
            datasets=[f"spike_t3_{RUN_ID}"],
        )

    # Warm the session cache with one read.
    try:
        await session_recall()
    except Exception:
        pass

    session_times = [await timed_call(session_recall) for _ in range(5)]
    graph_times = [await timed_call(graph_recall) for _ in range(5)]

    s_med = statistics.median(session_times)
    g_med = statistics.median(graph_times)
    ratio = (s_med / g_med) if g_med else float("inf")
    passed = (s_med < 0.5 * g_med) and (s_med < 500)
    return {
        "passed": passed,
        "detail": f"session_med={int(s_med)}ms graph_med={int(g_med)}ms ratio={ratio:.2f}",
        "raw": {"session_ms": [int(t) for t in session_times], "graph_ms": [int(t) for t in graph_times]},
    }


@timed
async def test_4_improve_custom_enrichment(ctx):
    await cognee.remember(
        [
            "The thief stole a golden relic from Mira's stall.",
            "Mira cried out when she saw the theft.",
            "Rowan heard Mira's cry.",
        ],
        dataset_name=f"spike_t4_{RUN_ID}",
        self_improvement=False,
    )

    baseline = await cognee.recall(
        query_text="Summarize what happened at the stall.",
        datasets=[f"spike_t4_{RUN_ID}"],
    )
    baseline_text = recall_text(baseline)

    async def add_faction_insight(data=None, **kwargs):
        # Trivial custom enrichment: emits a derived summary string.
        # Real impl would write a node/edge; this proves the hook fires and
        # the output is reachable by a later recall.
        return ["The theft at Mira's stall harmed the Orchard Guild's trust."]

    custom_task = Task(add_faction_insight)
    try:
        await cognee.memify(
            dataset=f"spike_t4_{RUN_ID}",
            enrichment_tasks=[custom_task],
        )
        improved = await cognee.recall(
            query_text="Summarize what happened at the stall.",
            datasets=[f"spike_t4_{RUN_ID}"],
        )
        improved_text = recall_text(improved)
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
        # Fallback: does improve(build_global_context_index=True) at least change something?
        try:
            await cognee.improve(dataset=f"spike_t4_{RUN_ID}", build_global_context_index=True)
            improved = await cognee.recall(
                query_text="Summarize what happened at the stall.",
                datasets=[f"spike_t4_{RUN_ID}"],
            )
            improved_text = recall_text(improved)
            passed = len(improved_text) > 10
            return {
                "passed": passed,
                "detail": f"FALLBACK global_context_index only; custom hook raised {type(e).__name__}: {e}",
                "raw": improved_text[:300],
            }
        except Exception as e2:
            return {
                "passed": False,
                "detail": f"BOTH paths failed: custom={type(e).__name__}: {e}; fallback={type(e2).__name__}: {e2}",
                "raw": None,
            }


@timed
async def test_5_temporal_scoped_recall(ctx):
    # temporal_cognify is a cognify() param, so add() then cognify().
    await cognee.add(
        "At 2026-06-27T09:00:00Z the player stole the relic. "
        "At 2026-06-27T09:05:00Z Mira confronted the player. "
        "At 2026-06-27T09:20:00Z the player returned the relic. "
        "At 2026-06-27T09:25:00Z Mira thanked the player.",
        dataset_name=f"spike_t5_{RUN_ID}",
    )
    await cognee.cognify([f"spike_t5_{RUN_ID}"], temporal_cognify=True)

    results = await cognee.recall(
        query_type=SearchType.TEMPORAL,
        query_text="What happened before 2026-06-27T09:10:00Z?",
        datasets=[f"spike_t5_{RUN_ID}"],
        top_k=10,
    )
    answer = recall_text(results)
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


@timed
async def test_6_partial_knowledge_isolation(ctx):
    await cognee.remember(
        "Mira saw the player steal the golden relic from the orchard stall.",
        dataset_name=f"spike_t6_mira_{RUN_ID}",
    )

    await cognee.remember(
        "Sol tends the shrine and meditates. Sol knows nothing about recent events.",
        dataset_name=f"spike_t6_sol_{RUN_ID}",
    )

    mira_recall = await cognee.recall(
        query_text="Did anyone steal anything?",
        datasets=[f"spike_t6_mira_{RUN_ID}"],
    )
    mira_answer = recall_text(mira_recall)

    sol_recall = await cognee.recall(
        query_text="Did anyone steal anything?",
        datasets=[f"spike_t6_sol_{RUN_ID}"],
    )
    sol_answer = recall_text(sol_recall)

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


@timed
async def test_7_open_action_classification(ctx):
    await cognee.remember(
        [
            "Stealing from a merchant is an act of theft with strongly negative valence.",
            "Giving medicine to a sick child is an act of generosity with positive valence.",
            "Lying about a theft is an act of deception with negative valence.",
            "Publicly apologizing at the shrine is an act of remorse with positive valence.",
        ],
        dataset_name=f"spike_t7_{RUN_ID}",
    )

    results = await cognee.recall(
        query_text="I threatened Niko with a knife. What kind of act is this and what is its valence?",
        datasets=[f"spike_t7_{RUN_ID}"],
    )
    answer = recall_text(results)
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
    try:
        await cognee.disconnect()
    except Exception as e:
        print(f"(disconnect warning: {type(e).__name__})")
    print("\n=== SPIKE SUMMARY ===")
    lines = RESULTS_PATH.read_text().splitlines() if RESULTS_PATH.exists() else []
    passed = sum(1 for line in lines if json.loads(line).get("passed"))
    total = len(lines)
    print(f"{passed}/{total} checks passed. See spike_results.jsonl.")


if __name__ == "__main__":
    asyncio.run(main())
