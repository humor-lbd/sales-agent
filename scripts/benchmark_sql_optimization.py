"""
LLM SQL 优化基准脚本。

用法：
    # 测量优化前基线
    python scripts/benchmark_sql_optimization.py --phase before

    # 测量优化后
    python scripts/benchmark_sql_optimization.py --phase after

    # 对比两次测量结果，生成报告
    python scripts/benchmark_sql_optimization.py --compare logs/benchmark_before_xxx.json logs/benchmark_after_xxx.json

输出：
    - logs/benchmark_{phase}_{timestamp}.json
    - docs/benchmark_comparison_report.md（compare 模式）
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from _common import compact, stable_hash

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import get_settings  # noqa: E402
from app.db.database import SessionLocal  # noqa: E402
from app.logic.schemas import UserInfo  # noqa: E402
from app.logic.services import SalesQueryService  # noqa: E402
from app.logic.sql_agent.executor import SqlExecutor  # noqa: E402
from app.logic.sql_agent.generator import LlmSqlGenerator  # noqa: E402
from app.logic.sql_agent.models import GeneratedSql, SqlTaskSpec  # noqa: E402
from app.logic.sql_agent.schema_registry import SqlSchemaRegistry  # noqa: E402
from app.logic.sql_agent.service import LlmSqlQueryService  # noqa: E402
from app.logic.tools import SalesTools  # noqa: E402


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class BenchmarkResult:
    task_type: str
    tool_name: str
    role: str
    scene: str
    iteration: int
    source: str  # template / cache / generator
    generation_ms: float
    total_ms: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    validation_ok: bool
    result_hash: str
    error: str | None
    sql_preview: str


@dataclass
class TestCase:
    task_type: str
    tool_name: str
    role: str
    scene: str
    user: UserInfo | None
    call: Any  # lambda(SalesTools) -> Any


# ---------------------------------------------------------------------------
# Capturing wrappers
# ---------------------------------------------------------------------------

class BenchmarkGenerator(LlmSqlGenerator):
    """记录生成过程的 Generator 包装。"""

    def __init__(self, settings, sink: list[dict[str, Any]]) -> None:
        super().__init__(settings)
        self.sink = sink

    def generate(self, task: SqlTaskSpec, schema: SqlSchemaRegistry, errors: list[str] | None = None) -> GeneratedSql:
        result = super().generate(task, schema, errors)
        self.sink.append({
            "phase": "generated",
            "task_type": task.task_type,
            "duration_ms": self.last_duration_ms,
            "usage": dict(self.last_usage),
            "sql": compact(result.sql),
        })
        return result


class BenchmarkExecutor(SqlExecutor):
    """记录执行过程的 Executor 包装。"""

    def __init__(self, db, max_rows: int, timeout_seconds: int, sink: list[dict[str, Any]]) -> None:
        super().__init__(db, max_rows, timeout_seconds)
        self.sink = sink

    def execute(self, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        started = time.perf_counter()
        try:
            rows = super().execute(sql, params)
        except Exception as exc:
            self.sink.append({"phase": "executed", "ok": False, "error": str(exc)})
            raise
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        self.sink.append({"phase": "executed", "ok": True, "duration_ms": elapsed, "row_count": len(rows)})
        return rows


class BenchmarkService(LlmSqlQueryService):
    """记录审计信息的 Service 包装。"""

    def __init__(self, *args, audit_sink: list[dict[str, Any]], **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.audit_sink = audit_sink

    def _audit_log(self, task, sql, params, row_count, audit, execution_ms) -> None:
        self.audit_sink.append({
            "source": audit.source,
            "template_id": audit.template_id,
            "cache_hit": audit.cache_hit,
            "generation_ms": round(audit.generation_ms, 2),
            "execution_ms": round(execution_ms, 2),
            "prompt_tokens": audit.prompt_tokens,
            "completion_tokens": audit.completion_tokens,
            "total_tokens": audit.total_tokens,
            "row_count": row_count,
        })
        super()._audit_log(task, sql, params, row_count, audit, execution_ms)


# ---------------------------------------------------------------------------
# Build tools with LLM SQL enabled
# ---------------------------------------------------------------------------

def build_benchmark_tools(db, user: UserInfo | None, capture_sink: list[dict[str, Any]]) -> SalesTools:
    base_settings = get_settings()
    llm_settings = base_settings.model_copy(update={
        "llm_sql_enabled": True,
        "llm_sql_shadow_mode": False,
        "llm_sql_use_fallback": False,
        "llm_sql_repair_attempts": 1,
        "llm_sql_temperature": 0.0,
    })
    service = SalesQueryService(db, user, None)
    service.settings = llm_settings
    service.llm_sql = BenchmarkService(
        db=db,
        current_user=user,
        redis_client=None,
        settings=llm_settings,
        generator=BenchmarkGenerator(llm_settings, capture_sink),
        executor=BenchmarkExecutor(db, llm_settings.llm_sql_max_rows, llm_settings.llm_sql_timeout_seconds, capture_sink),
        audit_sink=capture_sink,
    )
    return SalesTools(service)


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

def build_test_cases() -> list[TestCase]:
    start = "2026-05-01"
    end = "2026-05-31"
    prev_start = "2026-04-01"
    prev_end = "2026-04-30"
    director = UserInfo(user_id=9101, username="于博同", role="SALES_DIRECTOR", region_id=3, rep_id=9101)

    return [
        TestCase("order_detail", "query_sales_data", "销售总监", "订单明细", director,
                 lambda t: t.query_orders(start, end, limit=8)),
        TestCase("sales_summary", "get_sales_summary", "销售总监", "销售额汇总", director,
                 lambda t: t.get_sales_summary(start, end)),
        TestCase("rep_ranking", "get_top_reps", "销售总监", "销售员排名", director,
                 lambda t: t.get_top_reps(start, end, top_n=5)),
        TestCase("region_ranking", "get_region_ranking", "销售总监", "大区排名", director,
                 lambda t: t.get_region_ranking(start, end)),
        TestCase("product_ranking", "get_top_products", "销售总监", "产品排名", director,
                 lambda t: t.get_top_products(start, end, 5)),
        TestCase("monthly_trend", "get_monthly_trend", "销售总监", "月度趋势", director,
                 lambda t: t.get_monthly_trend(6)),
        TestCase("refund_rates", "detect_sales_anomalies", "销售总监", "退单率", director,
                 lambda t: t.detect_all_anomalies()),
    ]


# ---------------------------------------------------------------------------
# Run benchmark
# ---------------------------------------------------------------------------

def run_benchmark(phase: str, iterations: int = 3) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    cases = build_test_cases()

    with SessionLocal() as db:
        for case in cases:
            for i in range(iterations):
                print(f"  [{phase}] {case.role} / {case.tool_name} / {case.scene} (iter {i+1}/{iterations})", flush=True)
                capture: list[dict[str, Any]] = []
                error = None
                result_hash = ""
                total_ms = 0.0

                try:
                    tools = build_benchmark_tools(db, case.user, capture)
                    started = time.perf_counter()
                    result = case.call(tools)
                    total_ms = round((time.perf_counter() - started) * 1000, 2)
                    result_hash = stable_hash(result)
                except Exception as exc:
                    error = str(exc)
                    total_ms = round((time.perf_counter() - started) * 1000, 2) if 'started' in dir() else 0

                # Extract metrics from capture
                generations = [c for c in capture if c.get("phase") == "generated"]
                audits = [c for c in capture if c.get("source")]

                source = audits[-1]["source"] if audits else "unknown"
                gen_ms = sum(g.get("duration_ms", 0) for g in generations)
                prompt_tokens = sum(g.get("usage", {}).get("prompt_tokens", 0) for g in generations)
                completion_tokens = sum(g.get("usage", {}).get("completion_tokens", 0) for g in generations)
                total_tokens = sum(g.get("usage", {}).get("total_tokens", 0) for g in generations)
                validation_ok = error is None
                sql_preview = compact(generations[-1].get("sql", "") if generations else "")

                results.append(asdict(BenchmarkResult(
                    task_type=case.task_type,
                    tool_name=case.tool_name,
                    role=case.role,
                    scene=case.scene,
                    iteration=i + 1,
                    source=source,
                    generation_ms=round(gen_ms, 2),
                    total_ms=total_ms,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    validation_ok=validation_ok,
                    result_hash=result_hash,
                    error=error,
                    sql_preview=sql_preview,
                )))

    # Summary
    by_task: dict[str, list[dict]] = {}
    for r in results:
        by_task.setdefault(r["task_type"], []).append(r)

    summary = {}
    for task_type, items in by_task.items():
        valid = [i for i in items if i["error"] is None]
        summary[task_type] = {
            "count": len(items),
            "success_count": len(valid),
            "source": valid[0]["source"] if valid else "error",
            "avg_generation_ms": round(sum(i["generation_ms"] for i in valid) / len(valid), 2) if valid else 0,
            "avg_total_ms": round(sum(i["total_ms"] for i in valid) / len(valid), 2) if valid else 0,
            "min_total_ms": round(min(i["total_ms"] for i in valid), 2) if valid else 0,
            "max_total_ms": round(max(i["total_ms"] for i in valid), 2) if valid else 0,
            "avg_prompt_tokens": round(sum(i["prompt_tokens"] for i in valid) / len(valid), 2) if valid else 0,
            "avg_total_tokens": round(sum(i["total_tokens"] for i in valid) / len(valid), 2) if valid else 0,
            "result_hashes": list(set(i["result_hash"] for i in valid)),
            "consistent": len(set(i["result_hash"] for i in valid)) <= 1 if valid else False,
        }

    return {
        "phase": phase,
        "timestamp": time.strftime("%Y%m%d_%H%M%S"),
        "iterations": iterations,
        "total_cases": len(results),
        "results": results,
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# Compare two benchmark runs
# ---------------------------------------------------------------------------

def compare_reports(before_path: str, after_path: str) -> str:
    before = json.loads(Path(before_path).read_text(encoding="utf-8"))
    after = json.loads(Path(after_path).read_text(encoding="utf-8"))

    before_summary = before["summary"]
    after_summary = after["summary"]

    lines = [
        "# LLM SQL 优化对比报告",
        "",
        f"- 优化前：`{Path(before_path).name}`（{before['phase']}）",
        f"- 优化后：`{Path(after_path).name}`（{after['phase']}）",
        f"- 每组迭代次数：{before['iterations']}",
        "",
        "## 总览",
        "",
        "| task_type | 优化前来源 | 优化后来源 | 优化前平均耗时(ms) | 优化后平均耗时(ms) | 耗时变化 | 优化前token | 优化后token | 结果一致 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    all_task_types = sorted(set(list(before_summary.keys()) + list(after_summary.keys())))

    total_before_ms = 0
    total_after_ms = 0
    total_before_tokens = 0
    total_after_tokens = 0
    template_upgrade_count = 0

    for task_type in all_task_types:
        b = before_summary.get(task_type, {})
        a = after_summary.get(task_type, {})

        b_ms = b.get("avg_total_ms", 0)
        a_ms = a.get("avg_total_ms", 0)
        b_tokens = b.get("avg_total_tokens", 0)
        a_tokens = a.get("avg_total_tokens", 0)
        b_source = b.get("source", "N/A")
        a_source = a.get("source", "N/A")

        total_before_ms += b_ms
        total_after_ms += a_ms
        total_before_tokens += b_tokens
        total_after_tokens += a_tokens

        if b_source == "generator" and a_source == "template":
            template_upgrade_count += 1

        diff_ms = a_ms - b_ms
        diff_pct = (diff_ms / b_ms * 100) if b_ms else 0
        diff_str = f"{diff_ms:+.1f} ({diff_pct:+.1f}%)" if b_ms else "N/A"

        consistent = a.get("consistent", False)

        lines.append(
            f"| {task_type} | {b_source} | {a_source} | {b_ms:.1f} | {a_ms:.1f} | {diff_str} | "
            f"{b_tokens:.0f} | {a_tokens:.0f} | {'是' if consistent else '否'} |"
        )

    total_diff = total_after_ms - total_before_ms
    total_pct = (total_diff / total_before_ms * 100) if total_before_ms else 0
    token_diff = total_after_tokens - total_before_tokens
    token_pct = (token_diff / total_before_tokens * 100) if total_before_tokens else 0

    lines.extend([
        "",
        "## 关键指标汇总",
        "",
        f"- 模板命中率提升：{len([t for t in before_summary.values() if t.get('source') == 'template'])} / {len(before_summary)} → "
        f"{len([t for t in after_summary.values() if t.get('source') == 'template'])} / {len(after_summary)} task_type",
        f"- 模板升级数：{template_upgrade_count} 个 task_type 从 generator 升级为 template",
        f"- 总耗时变化：{total_before_ms:.1f}ms → {total_after_ms:.1f}ms（{total_diff:+.1f}ms, {total_pct:+.1f}%）",
        f"- 总 token 变化：{total_before_tokens:.0f} → {total_after_tokens:.0f}（{token_diff:+.0f}, {token_pct:+.1f}%）",
        "",
        "## 逐 task_type 详情",
        "",
    ])

    for task_type in all_task_types:
        b = before_summary.get(task_type, {})
        a = after_summary.get(task_type, {})
        lines.extend([
            f"### {task_type}",
            "",
            f"- 优化前：source={b.get('source', 'N/A')}, avg_total_ms={b.get('avg_total_ms', 0):.1f}, "
            f"avg_generation_ms={b.get('avg_generation_ms', 0):.1f}, avg_tokens={b.get('avg_total_tokens', 0):.0f}",
            f"- 优化后：source={a.get('source', 'N/A')}, avg_total_ms={a.get('avg_total_ms', 0):.1f}, "
            f"avg_generation_ms={a.get('avg_generation_ms', 0):.1f}, avg_tokens={a.get('avg_total_tokens', 0):.0f}",
            f"- 结果一致性：{'通过' if a.get('consistent') else '需检查'}",
            "",
        ])

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="LLM SQL 优化基准脚本")
    parser.add_argument("--phase", choices=["before", "after"], help="运行阶段标记")
    parser.add_argument("--iterations", type=int, default=3, help="每组迭代次数（默认 3）")
    parser.add_argument("--compare", nargs=2, metavar=("BEFORE", "AFTER"), help="对比两次运行结果")
    args = parser.parse_args()

    logs_dir = ROOT / "logs"
    docs_dir = ROOT / "docs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    if args.compare:
        report = compare_reports(args.compare[0], args.compare[1])
        report_path = docs_dir / "benchmark_comparison_report.md"
        report_path.write_text(report, encoding="utf-8")
        print(f"[compare] report written: {report_path}")
        print(report)
        return 0

    if not args.phase:
        parser.error("需要指定 --phase before 或 --phase after")

    print(f"[benchmark] phase={args.phase}, iterations={args.iterations}", flush=True)
    data = run_benchmark(args.phase, args.iterations)

    ts = data["timestamp"]
    out_path = logs_dir / f"benchmark_{args.phase}_{ts}.json"
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"[benchmark] results written: {out_path}", flush=True)

    # Print summary table
    print("\n## Summary")
    print(f"{'task_type':<20} {'source':<12} {'avg_ms':>10} {'avg_tokens':>12} {'consistent':>12}")
    print("-" * 70)
    for task_type, stats in sorted(data["summary"].items()):
        print(f"{task_type:<20} {stats['source']:<12} {stats['avg_total_ms']:>10.1f} {stats['avg_total_tokens']:>12.0f} {'Yes' if stats['consistent'] else 'No':>12}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
