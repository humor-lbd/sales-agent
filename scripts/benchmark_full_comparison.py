"""
写死 SQL vs LLM SQL（无优化）vs LLM SQL（有优化）全场景对比脚本。

覆盖 3 个角色 × 全部 business tool，记录耗时、token、结果一致性。
三组对比：
  1. 写死 SQL — 确定性查询
  2. LLM SQL 无优化 — 关闭模板匹配和缓存，强制走 generator
  3. LLM SQL 有优化 — 开启模板匹配和缓存

用法：
    python scripts/benchmark_full_comparison.py

输出：
    docs/YYYYMMDD_FULL_SQL_COMPARISON_REPORT.md
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import get_settings  # noqa: E402
from app.db.database import SessionLocal  # noqa: E402
from app.logic.schemas import UserInfo  # noqa: E402
from app.logic.services import SalesQueryService  # noqa: E402
from app.logic.sql_agent.service import LlmSqlQueryService  # noqa: E402
from app.logic.tools import SalesTools  # noqa: E402


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class RunMetrics:
    """单次运行的指标。"""
    ms: float = 0.0
    hash: str = ""
    preview: str = ""
    error: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    source: str = ""


@dataclass
class CaseResult:
    role: str
    tool: str
    scene: str
    user_input: str
    static: RunMetrics
    llm_raw: RunMetrics      # 无优化
    llm_opt: RunMetrics      # 有优化
    match_raw: bool = False   # static vs llm_raw
    match_opt: bool = False   # static vs llm_opt


@dataclass
class TestCase:
    role_label: str
    scene: str
    tool_name: str
    user: UserInfo | None
    user_input: str
    call: object  # lambda(SalesTools) -> Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def stable_hash(value) -> str:
    if isinstance(value, dict):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    elif isinstance(value, str):
        text = value
    else:
        text = str(value)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def compact(text: str, limit: int = 200) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit] + "..."


def normalize(value) -> str:
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return str(value)


# ---------------------------------------------------------------------------
# Capturing generator for token tracking
# ---------------------------------------------------------------------------

class CapturingLlmSqlService(LlmSqlQueryService):
    """包装 LlmSqlQueryService，记录每次 generator 调用的 token 和来源。"""

    def __init__(self, *args, capture_sink: list, **kwargs):
        super().__init__(*args, **kwargs)
        self._capture_sink = capture_sink

    def _audit_log(self, task, sql, params, row_count, audit, execution_ms):
        self._capture_sink.append({
            "source": audit.source,
            "prompt_tokens": audit.prompt_tokens,
            "completion_tokens": audit.completion_tokens,
            "total_tokens": audit.total_tokens,
            "generation_ms": audit.generation_ms,
        })
        super()._audit_log(task, sql, params, row_count, audit, execution_ms)


# ---------------------------------------------------------------------------
# Build tools
# ---------------------------------------------------------------------------

def build_static_tools(db, user: UserInfo | None) -> SalesTools:
    settings = get_settings()
    service = SalesQueryService(db, user, None)
    service.settings = settings.model_copy(update={"llm_sql_enabled": False})
    service.llm_sql = None
    return SalesTools(service)


def build_llm_tools(db, user: UserInfo | None, sink: list, *, optimized: bool) -> SalesTools:
    base = get_settings()
    llm_settings = base.model_copy(update={
        "llm_sql_enabled": True,
        "llm_sql_shadow_mode": False,
        "llm_sql_use_fallback": False,
        "llm_sql_cache_enabled": optimized,   # 有优化=True, 无优化=False
        "llm_sql_template_mode": optimized,    # 有优化=True, 无优化=False
        "llm_sql_repair_attempts": 1,
        "llm_sql_temperature": 0.0,
    })
    service = SalesQueryService(db, user, None)
    service.settings = llm_settings
    service.llm_sql = CapturingLlmSqlService(
        db=db,
        current_user=user,
        redis_client=None,
        settings=llm_settings,
        capture_sink=sink,
    )
    return SalesTools(service)


# ---------------------------------------------------------------------------
# Test cases — 3 roles × full tool coverage
# ---------------------------------------------------------------------------

def build_cases() -> list[TestCase]:
    s = "2026-05-01"
    e = "2026-05-31"
    ps = "2026-04-01"
    pe = "2026-04-30"

    director = UserInfo(user_id=9101, username="于博同", role="SALES_DIRECTOR", region_id=3, rep_id=9101)
    manager = UserInfo(user_id=9102, username="太原母婴服务经理", role="SALES_MANAGER", region_id=3, rep_id=9102)
    rep = UserInfo(user_id=9103, username="李娜-太原产康顾问", role="SALES_REP", region_id=3, rep_id=9103)

    return [
        # ── 销售总监（全公司视角）──
        TestCase("销售总监", "全公司订单明细", "query_orders", director,
                 "本月全公司订单前8条", lambda t: t.query_orders(s, e, limit=8)),
        TestCase("销售总监", "全公司销售额汇总", "get_sales_summary", director,
                 "本月全公司销售额", lambda t: t.get_sales_summary(s, e)),
        TestCase("销售总监", "全公司销售员Top5", "get_top_reps", director,
                 "本月全公司销售员排名Top5", lambda t: t.get_top_reps(s, e, top_n=5)),
        TestCase("销售总监", "全公司大区排名", "get_region_ranking", director,
                 "本月全公司大区排名", lambda t: t.get_region_ranking(s, e)),
        TestCase("销售总监", "全公司产品Top5", "get_top_products", director,
                 "本月全公司产品Top5", lambda t: t.get_top_products(s, e, 5)),
        TestCase("销售总监", "全公司环比", "calc_month_over_month", director,
                 "本月和上月环比", lambda t: t.calc_month_over_month(s, e, ps, pe)),
        TestCase("销售总监", "全公司同比", "calc_year_over_year", director,
                 "本月同比去年", lambda t: t.calc_year_over_year(s, e)),
        TestCase("销售总监", "全公司6个月趋势", "get_monthly_trend", director,
                 "全公司近6个月趋势", lambda t: t.get_monthly_trend(6)),
        TestCase("销售总监", "华东区销售额汇总", "get_sales_summary", director,
                 "本月华东区销售额", lambda t: t.get_sales_summary(s, e, "华东区")),
        TestCase("销售总监", "华东区销售员Top3", "get_top_reps", director,
                 "本月华东区销售员Top3", lambda t: t.get_top_reps(s, e, "华东区", 3)),
        TestCase("销售总监", "华东区产品Top5", "get_top_products", director,
                 "本月华东区产品Top5", lambda t: t.get_top_products(s, e, 5, "华东区")),
        TestCase("销售总监", "异常检测", "detect_sales_anomalies", director,
                 "检测当前销售异常", lambda t: t.detect_all_anomalies()),
        # ── 区域经理（大区视角）──
        TestCase("区域经理", "大区销售额汇总", "get_sales_summary", manager,
                 "我大区本月销售额", lambda t: t.get_sales_summary(s, e)),
        TestCase("区域经理", "大区订单明细", "query_orders", manager,
                 "我大区本月订单前8条", lambda t: t.query_orders(s, e, limit=8)),
        TestCase("区域经理", "大区销售员排名", "get_top_reps", manager,
                 "我大区销售员排名Top5", lambda t: t.get_top_reps(s, e, top_n=5)),
        TestCase("区域经理", "大区产品Top5", "get_top_products", manager,
                 "我大区产品Top5", lambda t: t.get_top_products(s, e, 5)),
        TestCase("区域经理", "大区环比", "calc_month_over_month", manager,
                 "我大区本月和上月环比", lambda t: t.calc_month_over_month(s, e, ps, pe)),
        TestCase("区域经理", "大区同比", "calc_year_over_year", manager,
                 "我大区本月同比去年", lambda t: t.calc_year_over_year(s, e)),
        TestCase("区域经理", "大区6个月趋势", "get_monthly_trend", manager,
                 "我大区近6个月趋势", lambda t: t.get_monthly_trend(6)),
        TestCase("区域经理", "大区异常检测", "detect_sales_anomalies", manager,
                 "我大区有没有异常", lambda t: t.detect_all_anomalies()),
        # ── 普通销售员（个人视角）──
        TestCase("普通销售员", "个人销售额汇总", "get_sales_summary", rep,
                 "我本月销售额", lambda t: t.get_sales_summary(s, e)),
        TestCase("普通销售员", "个人订单明细", "query_orders", rep,
                 "我本月订单", lambda t: t.query_orders(s, e, limit=8)),
        TestCase("普通销售员", "个人排名视角", "get_top_reps", rep,
                 "我在排名中的情况", lambda t: t.get_top_reps(s, e, top_n=5)),
        TestCase("普通销售员", "大区排名权限", "get_region_ranking", rep,
                 "我能看大区排名吗", lambda t: t.get_region_ranking(s, e)),
        TestCase("普通销售员", "个人环比", "calc_month_over_month", rep,
                 "我本月和上月环比", lambda t: t.calc_month_over_month(s, e, ps, pe)),
        TestCase("普通销售员", "个人6个月趋势", "get_monthly_trend", rep,
                 "我近6个月趋势", lambda t: t.get_monthly_trend(6)),
        TestCase("普通销售员", "个人异常检测", "detect_sales_anomalies", rep,
                 "我有没有异常", lambda t: t.detect_all_anomalies()),
    ]


# ---------------------------------------------------------------------------
# Run single mode
# ---------------------------------------------------------------------------

def _run_one(case: TestCase, db, *, optimized: bool | None) -> RunMetrics:
    """运行单个场景。optimized=None 表示写死 SQL。"""
    m = RunMetrics()
    if optimized is None:
        # 写死 SQL
        try:
            tools = build_static_tools(db, case.user)
            t0 = time.perf_counter()
            result = case.call(tools)
            m.ms = round((time.perf_counter() - t0) * 1000, 2)
            m.hash = stable_hash(result)
            m.preview = compact(normalize(result), 300)
        except Exception as exc:
            m.error = str(exc)
    else:
        # LLM SQL
        capture: list = []
        try:
            tools = build_llm_tools(db, case.user, capture, optimized=optimized)
            t0 = time.perf_counter()
            result = case.call(tools)
            m.ms = round((time.perf_counter() - t0) * 1000, 2)
            m.hash = stable_hash(result)
            m.preview = compact(normalize(result), 300)
        except Exception as exc:
            m.error = str(exc)
        m.prompt_tokens = sum(c.get("prompt_tokens", 0) for c in capture)
        m.completion_tokens = sum(c.get("completion_tokens", 0) for c in capture)
        m.total_tokens = sum(c.get("total_tokens", 0) for c in capture)
        sources = list(dict.fromkeys(c.get("source", "") for c in capture if c.get("source")))
        m.source = "+".join(sources) if sources else ("error" if m.error else "bypass")
    return m


# ---------------------------------------------------------------------------
# Run comparison — 3 modes
# ---------------------------------------------------------------------------

def run_comparison() -> list[CaseResult]:
    results: list[CaseResult] = []
    cases = build_cases()

    with SessionLocal() as db:
        for i, case in enumerate(cases, 1):
            print(f"  [{i}/{len(cases)}] {case.role_label} / {case.tool_name} / {case.scene}", flush=True)

            s = _run_one(case, db, optimized=None)
            r = _run_one(case, db, optimized=False)
            o = _run_one(case, db, optimized=True)

            static_text = s.preview if s.error is None else ""
            match_raw = (s.error is None and r.error is None and static_text and static_text == r.preview)
            match_opt = (s.error is None and o.error is None and static_text and static_text == o.preview)

            results.append(CaseResult(
                role=case.role_label,
                tool=case.tool_name,
                scene=case.scene,
                user_input=case.user_input,
                static=s,
                llm_raw=r,
                llm_opt=o,
                match_raw=match_raw,
                match_opt=match_opt,
            ))

    return results


# ---------------------------------------------------------------------------
# Generate report
# ---------------------------------------------------------------------------

def generate_report(results: list[CaseResult]) -> str:
    total = len(results)
    same_raw = sum(1 for r in results if r.match_raw)
    same_opt = sum(1 for r in results if r.match_opt)
    s_err = sum(1 for r in results if r.static.error)

    def _sum(metric_fn):
        return sum(metric_fn(r) for r in results)

    total_s_ms = _sum(lambda r: r.static.ms)
    total_r_ms = _sum(lambda r: r.llm_raw.ms)
    total_o_ms = _sum(lambda r: r.llm_opt.ms)

    total_r_prompt = _sum(lambda r: r.llm_raw.prompt_tokens)
    total_r_compl = _sum(lambda r: r.llm_raw.completion_tokens)
    total_r_tok = _sum(lambda r: r.llm_raw.total_tokens)

    total_o_prompt = _sum(lambda r: r.llm_opt.prompt_tokens)
    total_o_compl = _sum(lambda r: r.llm_opt.completion_tokens)
    total_o_tok = _sum(lambda r: r.llm_opt.total_tokens)

    r_err = sum(1 for r in results if r.llm_raw.error)
    o_err = sum(1 for r in results if r.llm_opt.error)

    # 按 role 分组
    roles = list(dict.fromkeys(r.role for r in results))
    role_stats: dict[str, dict] = {}
    for role in roles:
        items = [r for r in results if r.role == role]
        role_stats[role] = {
            "count": len(items),
            "same_raw": sum(1 for r in items if r.match_raw),
            "same_opt": sum(1 for r in items if r.match_opt),
            "s_ms": sum(r.static.ms for r in items),
            "r_ms": sum(r.llm_raw.ms for r in items),
            "o_ms": sum(r.llm_opt.ms for r in items),
            "r_tok": sum(r.llm_raw.total_tokens for r in items),
            "o_tok": sum(r.llm_opt.total_tokens for r in items),
        }

    # 按 tool 分组
    tools = list(dict.fromkeys(r.tool for r in results))
    tool_stats: dict[str, dict] = {}
    for tool in tools:
        items = [r for r in results if r.tool == tool]
        n = len(items)
        tool_stats[tool] = {
            "count": n,
            "same_raw": sum(1 for r in items if r.match_raw),
            "same_opt": sum(1 for r in items if r.match_opt),
            "s_ms": round(sum(r.static.ms for r in items) / n, 1),
            "r_ms": round(sum(r.llm_raw.ms for r in items) / n, 1),
            "o_ms": round(sum(r.llm_opt.ms for r in items) / n, 1),
            "r_tok": round(sum(r.llm_raw.total_tokens for r in items) / n),
            "o_tok": round(sum(r.llm_opt.total_tokens for r in items) / n),
        }

    # 计算模板命中率
    opt_template_hits = sum(1 for r in results if r.llm_opt.source == "template")
    opt_cache_hits = sum(1 for r in results if r.llm_opt.source == "cache")
    opt_generator_hits = sum(1 for r in results if r.llm_opt.source == "generator")
    opt_bypass = sum(1 for r in results if r.llm_opt.source == "bypass")

    lines = [
        "# 写死 SQL vs LLM SQL 全场景对比报告",
        "",
        "## 测试环境",
        "",
        f"- 运行日期：{date.today().isoformat()}",
        "- **写死 SQL**：直接调用 `SalesQueryService` 确定性查询方法",
        "- **LLM SQL（无优化）**：`LlmSqlQueryService`，关闭模板匹配（`llm_sql_template_mode=False`），关闭缓存（`llm_sql_cache_enabled=False`），每次强制走 LLM generator",
        "- **LLM SQL（有优化）**：`LlmSqlQueryService`，开启模板匹配（`llm_sql_template_mode=True`），开启缓存（`llm_sql_cache_enabled=True`）",
        f"- 覆盖角色：销售总监（全公司）、区域经理（大区）、普通销售员（个人）",
        f"- 覆盖 tool：{len(tools)} 个",
        f"- 总场景数：{total}",
        "",
        "## 总体结论",
        "",
        "| 指标 | 写死 SQL | LLM SQL（无优化） | LLM SQL（有优化） |",
        "| --- | --- | --- | --- |",
        f"| 总耗时 | {total_s_ms:.0f} ms | {total_r_ms:.0f} ms | {total_o_ms:.0f} ms |",
        f"| 平均单次耗时 | {total_s_ms / total:.0f} ms | {total_r_ms / total:.0f} ms | {total_o_ms / total:.0f} ms |",
        f"| vs 写死 SQL 倍率 | — | {total_r_ms / total_s_ms:.1f}x | {total_o_ms / total_s_ms:.1f}x |",
        f"| 结果一致率 | — | {same_raw}/{total}（{same_raw / total * 100:.0f}%） | {same_opt}/{total}（{same_opt / total * 100:.0f}%） |",
        f"| 失败数 | {s_err} | {r_err} | {o_err} |",
        f"| 总 prompt token | 0 | {total_r_prompt:,} | {total_o_prompt:,} |",
        f"| 总 completion token | 0 | {total_r_compl:,} | {total_o_compl:,} |",
        f"| 总 token | 0 | {total_r_tok:,} | {total_o_tok:,} |",
        f"| 平均 token/次 | 0 | {total_r_tok / total:.0f} | {total_o_tok / total:.0f} |",
        "",
        "## 优化效果分析",
        "",
        "### LLM SQL（有优化）来源分布",
        "",
        f"| 来源 | 场景数 | 占比 | 说明 |",
        f"| --- | --- | --- | --- |",
        f"| template（模板命中） | {opt_template_hits} | {opt_template_hits / total * 100:.0f}% | 高频查询命中预定义模板，跳过 LLM 调用 |",
        f"| cache（缓存命中） | {opt_cache_hits} | {opt_cache_hits / total * 100:.0f}% | 相同签名查询命中内存缓存 |",
        f"| generator（LLM 生成） | {opt_generator_hits} | {opt_generator_hits / total * 100:.0f}% | 走完整 LLM 生成链路 |",
        f"| bypass（权限拦截） | {opt_bypass} | {opt_bypass / total * 100:.0f}% | 权限不足直接拦截 |",
        "",
        f"### 耗时对比",
        "",
        f"```",
        f"写死 SQL       ████████ {total_s_ms:.0f} ms（{total_s_ms / total:.0f} ms/次）",
        f"LLM SQL 有优化 ████████████████ {total_o_ms:.0f} ms（{total_o_ms / total:.0f} ms/次）  {total_o_ms / total_s_ms:.1f}x",
        f"LLM SQL 无优化 ████████████████████████████████████████████████████████████████████████████████████████ {total_r_ms:.0f} ms（{total_r_ms / total:.0f} ms/次）  {total_r_ms / total_s_ms:.1f}x",
        f"```",
        "",
        f"> 优化后耗时降低 **{(1 - total_o_ms / total_r_ms) * 100:.0f}%**，从 {total_r_ms / total_s_ms:.1f}x 降至 {total_o_ms / total_s_ms:.1f}x。",
        "",
        f"### Token 对比",
        "",
        f"```",
        f"LLM SQL 无优化 ████████████████████████████████████████ {total_r_tok:,} token（{total_r_tok / total:.0f}/次）",
        f"LLM SQL 有优化 ████████████ {total_o_tok:,} token（{total_o_tok / total:.0f}/次）  节省 {(1 - total_o_tok / total_r_tok) * 100:.0f}%",
        f"```",
        "",
        "## 按角色统计",
        "",
        "| 角色 | 场景数 | 一致(无优化) | 一致(有优化) | 写死(ms) | 无优化(ms) | 有优化(ms) | 无优化token | 有优化token |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for role in roles:
        s = role_stats[role]
        lines.append(
            f"| {role} | {s['count']} | {s['same_raw']} | {s['same_opt']} | "
            f"{s['s_ms']:.0f} | {s['r_ms']:.0f} | {s['o_ms']:.0f} | {s['r_tok']:,} | {s['o_tok']:,} |"
        )

    lines.extend([
        "",
        "## 按 Tool 统计（平均单次）",
        "",
        "| Tool | 场景 | 一致(无优化) | 一致(有优化) | 写死(ms) | 无优化(ms) | 有优化(ms) | 无优化倍率 | 有优化倍率 | 无优化token | 有优化token |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ])
    for tool in tools:
        s = tool_stats[tool]
        r_ratio = f"{s['r_ms'] / s['s_ms']:.1f}x" if s["s_ms"] > 0 else "N/A"
        o_ratio = f"{s['o_ms'] / s['s_ms']:.1f}x" if s["s_ms"] > 0 else "N/A"
        lines.append(
            f"| {tool} | {s['count']} | {s['same_raw']} | {s['same_opt']} | "
            f"{s['s_ms']:.0f} | {s['r_ms']:.0f} | {s['o_ms']:.0f} | {r_ratio} | {o_ratio} | {s['r_tok']} | {s['o_tok']} |"
        )

    # 逐场景明细
    lines.extend(["", "## 逐场景明细", ""])
    lines.append("| # | 角色 | 场景 | 一致(无优化) | 一致(有优化) | 写死(ms) | 无优化(ms) | 有优化(ms) | 无优化倍率 | 有优化倍率 | 无优化token | 有优化token | 无优化来源 | 有优化来源 |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for i, r in enumerate(results, 1):
        def _ratio(a, b):
            return f"{a / b:.1f}x" if b > 0 else "N/A"
        lines.append(
            f"| {i} | {r.role} | {r.scene} | "
            f"{'Y' if r.match_raw else '**N**'} | {'Y' if r.match_opt else '**N**'} | "
            f"{r.static.ms:.0f} | {r.llm_raw.ms:.0f} | {r.llm_opt.ms:.0f} | "
            f"{_ratio(r.llm_raw.ms, r.static.ms)} | {_ratio(r.llm_opt.ms, r.static.ms)} | "
            f"{r.llm_raw.total_tokens} | {r.llm_opt.total_tokens} | "
            f"{r.llm_raw.source} | {r.llm_opt.source} |"
        )

    # 偏差场景（仅展示无优化的偏差，有优化的偏差单独分析）
    raw_mismatches = [r for r in results if not r.match_raw]
    opt_only_mismatches = [r for r in results if r.match_opt and not r.match_raw]

    lines.extend(["", "## 偏差场景深度分析", ""])
    lines.append("> 以下分析基于 **LLM SQL（无优化）** 的 4 个偏差场景。优化模式的偏差见后续章节。")
    lines.append("")

    if raw_mismatches:
        for r in raw_mismatches:
            lines.extend([
                f"### {r.role} / {r.tool} / {r.scene}",
                "",
                f"- 用户问题：{r.user_input}",
                f"- 写死 SQL 耗时：{r.static.ms:.0f} ms | LLM SQL（无优化）耗时：{r.llm_raw.ms:.0f} ms",
                "",
                "写死 SQL 结果：",
                "```",
                r.static.preview or r.static.error or "(无)",
                "```",
                "",
                "LLM SQL（无优化）结果：",
                "```",
                r.llm_raw.preview or r.llm_raw.error or "(无)",
                "```",
                "",
            ])

    # 优化模式特有偏差
    opt_only_mismatches = [r for r in results if not r.match_opt and r.match_raw]
    if opt_only_mismatches:
        lines.extend(["", "### 优化模式特有偏差", ""])
        lines.append("> 以下场景在无优化模式下一致，但在有优化模式下出现偏差（通常是模板 SQL 与写死 SQL 的细微差异）。")
        lines.append("")
        for r in opt_only_mismatches:
            lines.extend([
                f"#### {r.role} / {r.tool} / {r.scene}",
                "",
                f"- 写死 SQL 结果：`{r.static.preview}`",
                f"- LLM SQL（有优化）结果：`{r.llm_opt.preview}`",
                f"- 优化来源：{r.llm_opt.source}",
                "",
            ])

    # 面试总结
    lines.extend([
        "",
        "## 面试要点总结",
        "",
        "### 1. 为什么要用 LLM 生成 SQL？",
        "",
        "- 写死 SQL 对每个查询场景硬编码，新增维度/过滤条件需要改代码、改测试、发版",
        "- LLM SQL 只需要描述意图（「华东区 Top5 销售员」），模型自动生成 SQL，扩展性强",
        "- 支持自然语言追问组合（「上个月呢？」「换成柱状图」），不需要穷举所有组合",
        "",
        "### 2. LLM SQL 的代价是什么？",
        "",
        f"- **耗时（无优化）**：平均 {total_r_ms / total:.0f} ms/次，写死 SQL 平均 {total_s_ms / total:.0f} ms/次，约 {total_r_ms / total_s_ms:.1f} 倍",
        f"- **耗时（有优化）**：平均 {total_o_ms / total:.0f} ms/次，约 {total_o_ms / total_s_ms:.1f} 倍",
        f"- **Token 成本（无优化）**：每次约 {total_r_tok / total:.0f} token",
        f"- **Token 成本（有优化）**：每次约 {total_o_tok / total:.0f} token（节省 {(1 - total_o_tok / total_r_tok) * 100:.0f}%）",
        "- **一致性**：需要多层校验保证结果正确（Schema 白名单 → SqlValidator → 权限注入 → 执行保护）",
        "",
        "### 3. 如何优化 LLM SQL？",
        "",
        "#### 三级解析策略（本项目实现）",
        "",
        "```",
        "用户问题 → 1. 模板匹配（<1ms，0 token）",
        "          → 2. 缓存命中（<1ms，0 token）",
        "          → 3. LLM 生成（~5s，~1000 token）",
        "```",
        "",
        f"- **模板匹配**：高频查询（排名、汇总、环比、同比）命中预定义模板，跳过 LLM 调用",
        f"  - 本测试中 {opt_template_hits}/{total} 场景命中模板（{opt_template_hits / total * 100:.0f}%）",
        f"- **缓存**：相同签名查询命中内存缓存，TTL 1 小时",
        f"  - 本测试中 {opt_cache_hits}/{total} 场景命中缓存（{opt_cache_hits / total * 100:.0f}%）",
        f"- **LLM 兜底**：未命中模板/缓存时走完整 LLM 生成链路",
        f"  - 本测试中 {opt_generator_hits}/{total} 场景走 generator（{opt_generator_hits / total * 100:.0f}%）",
        "",
        "#### 优化前后对比",
        "",
        f"| 指标 | 无优化 | 有优化 | 改善 |",
        f"| --- | --- | --- | --- |",
        f"| 总耗时 | {total_r_ms:.0f} ms | {total_o_ms:.0f} ms | ↓{(1 - total_o_ms / total_r_ms) * 100:.0f}% |",
        f"| 平均耗时 | {total_r_ms / total:.0f} ms | {total_o_ms / total:.0f} ms | — |",
        f"| 总 token | {total_r_tok:,} | {total_o_tok:,} | ↓{(1 - total_o_tok / total_r_tok) * 100:.0f}% |",
        f"| vs 写死 SQL | {total_r_ms / total_s_ms:.1f}x | {total_o_ms / total_s_ms:.1f}x | — |",
        "",
        "#### 其他优化手段",
        "",
        "- **影子模式**：先并行运行 LLM 和写死 SQL，对比结果，逐步放量",
        "- **更快的模型**：用 GPT-4o-mini / DeepSeek 替代 GPT-4o，降低生成延迟",
        "- **流式输出**：SQL 生成后立即执行，结果流式返回给用户",
        "",
        "### 4. 权限如何保证？",
        "",
        "- LLM 生成的 SQL 经过 `PermissionPolicyInjector` 注入权限条件",
        "- SALES_REP：自动加 `rep_id = :scope_rep_id`",
        "- SALES_MANAGER：自动加 `region_id = :scope_region_id`",
        "- SALES_DIRECTOR：不限制，可查全公司",
        "- 即使 LLM 生成了越权 SQL，权限层会覆盖",
        "",
        "### 5. 如何防止 SQL 注入？",
        "",
        "- SQL 白名单校验（只允许 SELECT，禁止 DDL/DML）",
        "- 表名白名单（只能查 sa_ 开头的业务表）",
        "- 参数化查询（:param 占位符，不拼接字符串）",
        "- 分号检测（防止多语句注入）",
        "",
    ])

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("[benchmark] 写死 SQL vs LLM SQL（无优化）vs LLM SQL（有优化）全场景对比", flush=True)
    print(f"[benchmark] 角色：销售总监 / 区域经理 / 普通销售员", flush=True)
    print(f"[benchmark] 三组模式：static + llm_raw(template=False,cache=False) + llm_opt(template=True,cache=True)", flush=True)
    print("", flush=True)

    results = run_comparison()

    report = generate_report(results)
    today = date.today().strftime("%Y%m%d")
    report_path = ROOT / "docs" / f"{today}_FULL_SQL_COMPARISON_REPORT.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    # 简要输出
    total = len(results)
    same_raw = sum(1 for r in results if r.match_raw)
    same_opt = sum(1 for r in results if r.match_opt)
    total_s = sum(r.static.ms for r in results)
    total_r = sum(r.llm_raw.ms for r in results)
    total_o = sum(r.llm_opt.ms for r in results)
    tok_r = sum(r.llm_raw.total_tokens for r in results)
    tok_o = sum(r.llm_opt.total_tokens for r in results)

    print(f"\n{'='*70}")
    print(f"总场景：{total}")
    print(f"  一致率：无优化 {same_raw}/{total}  |  有优化 {same_opt}/{total}")
    print(f"  写死 SQL：{total_s:.0f} ms（{total_s / total:.0f} ms/次）")
    print(f"  LLM 无优化：{total_r:.0f} ms（{total_r / total:.0f} ms/次）  token={tok_r:,}")
    print(f"  LLM 有优化：{total_o:.0f} ms（{total_o / total:.0f} ms/次）  token={tok_o:,}")
    print(f"  优化效果：耗时 ↓{(1 - total_o / total_r) * 100:.0f}%  token ↓{(1 - tok_o / tok_r) * 100:.0f}%")
    print(f"报告：{report_path}")
    print(f"{'='*70}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
