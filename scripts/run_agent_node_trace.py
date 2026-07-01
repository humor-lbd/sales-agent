"""
运行 Agent 节点级追踪，并输出角色化复杂问题的执行报告。

运行方式：
    E:\develop\mini_anaconda\envs\dev\python.exe scripts\run_agent_node_trace.py
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from _common import compact

from app.core.config import get_settings
from app.db.database import SessionLocal
from app.graph.middleware import AgentMiddleware
from app.graph.nodes.bootstrap import bootstrap_node
from app.graph.nodes.guardrails import guardrails_node
from app.graph.nodes.memory import load_memory_node, persist_memory_node
from app.graph.nodes.react_agent import react_agent_node
from app.graph.nodes.react_tool_executor import react_tool_executor_node
from app.logic.schemas import UserInfo
from app.logic.services import MemoryService, SalesQueryService
from app.logic.tools import SalesTools


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "docs" / "AGENT_NODE_TRACE_REPORT.md"


class RecorderMiddleware(AgentMiddleware):
    def __init__(self, settings, request_id: str) -> None:
        super().__init__(settings, request_id)
        self.records: list[dict] = []

    def trace(self, title: str, payload=None) -> None:
        self.records.append({"title": title, "payload": payload})
        super().trace(title, payload)


def last_ai_summary(react_messages) -> dict:
    if not react_messages:
        return {}
    message = react_messages[-1]
    tool_calls = getattr(message, "tool_calls", None) or []
    return {
        "type": message.__class__.__name__,
        "content": compact(str(getattr(message, "content", ""))),
        "tool_calls": tool_calls,
    }


def summarize_update(node_name: str, update: dict) -> dict:
    summary = {"node": node_name}
    if node_name == "bootstrap":
        summary["state"] = {
            "session_id": update.get("session_id"),
            "request_text": update.get("request_text"),
            "tool_call_count": update.get("tool_call_count"),
            "react_round_count": update.get("react_round_count"),
        }
    elif node_name == "load_memory":
        summary["messages_count"] = len(update.get("messages") or [])
        summary["react_messages_count"] = len(update.get("react_messages") or [])
        summary["summary_context"] = compact(update.get("summary_context") or "无", 1000)
    elif node_name == "guardrails":
        summary["rejected"] = update.get("rejected")
        if update.get("final_answer"):
            summary["final_answer"] = compact(update.get("final_answer"), 1000)
    elif node_name == "react_agent":
        summary["react_round_count"] = update.get("react_round_count")
        summary["final_answer"] = compact(update.get("final_answer") or "", 1000)
        summary["last_ai_message"] = last_ai_summary(update.get("react_messages") or [])
    elif node_name == "react_tool_executor":
        summary["tool_call_count"] = update.get("tool_call_count")
        summary["tool_results"] = compact((update.get("tool_results") or {}).get("text", ""), 1000)
        summary["artifacts_count"] = len(update.get("artifacts") or [])
    elif node_name == "persist_memory":
        summary["saved"] = True
    return summary


def run_case(user: UserInfo, question: str, label: str) -> dict:
    settings = get_settings()
    with SessionLocal() as db:
        service = SalesQueryService(db, user, None)
        tools = SalesTools(service)
        memory_service = MemoryService(db)
        session_id = f"trace-{label}-{uuid4().hex[:8]}"
        request_id = uuid4().hex
        middleware = RecorderMiddleware(settings, request_id)
        runtime = SimpleNamespace(
            context={
                "current_user": user,
                "settings": settings,
                "tools": tools,
                "memory_service": memory_service,
                "today": date.today().isoformat(),
                "request_id": request_id,
                "middleware": middleware,
            }
        )

        timeline: list[dict] = []
        state = bootstrap_node({"session_id": session_id, "request_text": question})
        timeline.append(summarize_update("bootstrap", state))

        update = load_memory_node(state, runtime)
        state.update(update)
        timeline.append(summarize_update("load_memory", update))

        update = guardrails_node(state)
        state.update(update)
        timeline.append(summarize_update("guardrails", update))

        while not state.get("rejected") and not state.get("final_answer"):
            update = react_agent_node(state, runtime)
            state.update(update)
            timeline.append(summarize_update("react_agent", update))
            if state.get("final_answer"):
                break

            update = react_tool_executor_node(state, runtime)
            state.update(update)
            timeline.append(summarize_update("react_tool_executor", update))

        update = persist_memory_node(state, runtime)
        timeline.append(summarize_update("persist_memory", update))

        return {
            "label": label,
            "user": user.model_dump(),
            "session_id": session_id,
            "request_id": request_id,
            "question": question,
            "timeline": timeline,
            "trace_records": middleware.records,
            "final_answer": state.get("final_answer", ""),
            "artifacts": state.get("artifacts") or [],
            "llm_sql_enabled": settings.llm_sql_enabled,
            "llm_sql_shadow_mode": settings.llm_sql_shadow_mode,
        }


def build_report(cases: list[dict]) -> str:
    lines = [
        "# Agent 节点级输出与最终结果报告",
        "",
        "## 运行配置",
        "",
        f"- 当前 `LLM_SQL_ENABLED`：`{cases[0]['llm_sql_enabled']}`",
        f"- 当前 `LLM_SQL_SHADOW_MODE`：`{cases[0]['llm_sql_shadow_mode']}`",
        "- 结论：如果 `LLM_SQL_ENABLED=false`，当前运行项目就不是 LLM 生成 SQL，而是原来的确定性查询。",
        "",
    ]
    for case in cases:
        lines.extend(
            [
                f"## {case['label']}",
                "",
                f"- 用户：`{case['user']['username']}` / 角色：`{case['user']['role']}` / region_id：`{case['user']['region_id']}` / rep_id：`{case['user']['rep_id']}`",
                f"- session_id：`{case['session_id']}`",
                f"- request_id：`{case['request_id']}`",
                f"- 提问：{case['question']}",
                "",
                "### 节点输出",
                "",
            ]
        )
        for idx, node in enumerate(case["timeline"], start=1):
            lines.append(f"{idx}. `{node['node']}`")
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(node, ensure_ascii=False, indent=2, default=str))
            lines.append("```")
        lines.extend(["", "### Agent Trace", ""])
        for idx, record in enumerate(case["trace_records"], start=1):
            lines.append(f"{idx}. `{record['title']}`")
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(record, ensure_ascii=False, indent=2, default=str))
            lines.append("```")
        lines.extend(
            [
                "",
                "### 最终结果",
                "",
                "```text",
                case["final_answer"] or "",
                "```",
                "",
                f"附件数量：`{len(case['artifacts'])}`",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    cases = [
        run_case(
            UserInfo(user_id=9103, username="李娜-太原产康顾问", role="SALES_REP", region_id=3, rep_id=9103),
            "请基于我当前权限，分析我最近6个月的销售趋势、本月销售额、我的订单明细前5条、和上月相比的环比变化，并生成一张趋势图，最后告诉我有没有明显异常风险。",
            "普通销售员复杂问题",
        ),
        run_case(
            UserInfo(user_id=9102, username="太原母婴服务经理", role="SALES_MANAGER", region_id=3, rep_id=9102),
            "请基于我负责的大区，分析近6个月销售趋势、本月销售额、销售员Top5、产品Top5、和上月环比变化，生成一张趋势图，并最后判断当前有没有需要我重点关注的异常。",
            "区域经理复杂问题",
        ),
    ]
    REPORT_PATH.write_text(build_report(cases), encoding="utf-8")
    print(f"[trace] report written: {REPORT_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
