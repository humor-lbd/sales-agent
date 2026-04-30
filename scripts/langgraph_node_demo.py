"""
文件作用：
- 作为 LangGraph 节点演示脚本，按执行顺序打印每个节点的输出，帮助读者观察 Agent 内部链路。
- 运行这个脚本时，可以重点关注 react_agent 的推理轮次、react_tool_executor 的工具结果，以及最终回答与图表产物。
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.core.redis_client import get_redis_client
from app.core.security import build_user_from_rep
from app.db.database import SessionLocal
from app.graph.builder import get_sales_graph
from app.logic.services import MemoryService, SalesQueryService
from app.logic.tools import SalesTools


DIVIDER = "=" * 88
NODE_LABELS = {
    "bootstrap": "初始化状态",
    "load_memory": "读取历史记忆",
    "guardrails": "安全边界检查",
    "react_agent": "模型推理（决定继续调工具或直接回答）",
    "react_tool_executor": "执行工具调用并回写结果",
    "persist_memory": "写回会话记忆",
}


# 定义函数 _json_default，作为当前文件内部的辅助函数，给主流程提供支撑。
def _json_default(value: Any) -> Any:
    """
    作用：执行_json_default对应的业务逻辑。
    参数：value。
    返回：函数执行后的结果。
    """
    if isinstance(value, Decimal):
        return str(value)
    return str(value)


# 定义函数 _pretty_json，负责把结构化结果整理成更适合展示的形式。
def _pretty_json(value: Any) -> str:
    """
    作用：执行_pretty_json对应的业务逻辑。
    参数：value。
    返回：函数执行后的结果。
    """
    return json.dumps(value, ensure_ascii=False, indent=2, default=_json_default)


# 定义函数 _print_block_title，作为当前文件内部的辅助函数，给主流程提供支撑。
def _print_block_title(title: str) -> None:
    """
    作用：执行_print_block_title对应的业务逻辑。
    参数：title。
    返回：函数执行后的结果。
    """
    print()
    print(DIVIDER)
    print(title)
    print(DIVIDER)


# 定义函数 _print_rows_preview，作为当前文件内部的辅助函数，给主流程提供支撑。
def _print_rows_preview(rows: list[dict[str, Any]], limit: int = 3) -> None:
    """
    作用：执行_print_rows_preview对应的业务逻辑。
    参数：rows、limit。
    返回：函数执行后的结果。
    """
    if not rows:
        return
    print(f"结构化 rows 预览（最多 {limit} 条）：")
    print(_pretty_json(rows[:limit]))


# 定义函数 _print_groups_preview，作为当前文件内部的辅助函数，给主流程提供支撑。
def _print_groups_preview(groups: list[dict[str, Any]], limit: int = 2) -> None:
    """
    作用：执行_print_groups_preview对应的业务逻辑。
    参数：groups、limit。
    返回：函数执行后的结果。
    """
    if not groups:
        return
    print(f"分组 groups 预览（最多 {limit} 组）：")
    print(_pretty_json(groups[:limit]))


# 定义函数 _print_artifacts_preview，作为当前文件内部的辅助函数，给主流程提供支撑。
def _print_artifacts_preview(artifacts: list[dict[str, Any]], limit: int = 1) -> None:
    """
    作用：执行_print_artifacts_preview对应的业务逻辑。
    参数：artifacts、limit。
    返回：函数执行后的结果。
    """
    if not artifacts:
        return
    print(f"图表 artifacts 预览（最多 {limit} 个）：")
    print(_pretty_json(artifacts[:limit]))


# 定义函数 _print_node_output，负责当前文件中的一个关键步骤或对外能力。
def _print_node_output(step: int, node_name: str, node_output: Any, show_raw: bool) -> None:
    """
    作用：执行_print_node_output对应的业务逻辑。
    参数：step、node_name、node_output、show_raw。
    返回：函数执行后的结果。
    """
    label = NODE_LABELS.get(node_name, "未知节点")
    _print_block_title(f"[{step}] 节点：{node_name}（{label}）")

    if node_output is None:
        print("该节点没有显式返回值，通常表示它主要做了副作用操作，例如把结果写回数据库。")
        return

    if node_name == "bootstrap":
        print("bootstrap 会把本轮对话要用到的状态字段全部初始化。")
        print(f"初始化完成的字段：{', '.join(node_output.keys())}")
    elif node_name == "load_memory":
        messages = node_output.get("messages") or []
        print(f"已加载历史消息数：{len(messages)}")
        if messages:
            print("最近一条历史消息：")
            print(_pretty_json(messages[-1]))
    elif node_name == "guardrails":
        print(f"是否命中安全边界：{node_output.get('rejected')}")
        if node_output.get("final_answer"):
            print("如果命中安全边界，这里会直接给出拒答文案：")
            print(node_output["final_answer"])
    elif node_name == "react_agent":
        print("react_agent 会让模型判断：继续调用工具，还是直接给最终回答。")
        print(f"当前轮次：{node_output.get('react_round_count')}")
        if node_output.get("final_answer"):
            print("本轮已经得到最终回答：")
            print(node_output.get("final_answer") or "")
        else:
            print("本轮还没有最终回答，通常表示模型要求继续调用工具。")
    elif node_name == "react_tool_executor":
        tool_results = node_output.get("tool_results") or {}
        print("react_tool_executor 已执行模型请求的工具调用。")
        print(f"累计工具调用次数：{node_output.get('tool_call_count')}")
        if tool_results.get("text"):
            print("工具文本结果（可能是多次调用合并后）：")
            print(tool_results.get("text") or "")
        _print_rows_preview(tool_results.get("rows") or [])
        _print_groups_preview(tool_results.get("groups") or [])
        artifacts = node_output.get("artifacts") or []
        if artifacts:
            print(f"当前累计图表产物数：{len(artifacts)}")
            for index, artifact in enumerate(artifacts, start=1):
                print(f"- 图表 {index}：slot={artifact.get('slot')}，title={artifact.get('title')}")
            _print_artifacts_preview(artifacts)
    elif node_name == "persist_memory":
        print("persist_memory 已把当前用户问题和最终回答写入会话记忆。")
    else:
        print("节点输出：")
        print(_pretty_json(node_output))

    if show_raw:
        print()
        print("原始节点输出：")
        print(_pretty_json(node_output))


# 定义函数 _build_context，负责组装当前步骤需要的对象或参数。
def _build_context(db, rep_id: int | None) -> tuple[dict[str, Any], MemoryService]:
    """
    作用：执行_build_context对应的业务逻辑。
    参数：db、rep_id。
    返回：函数执行后的结果。
    """
    settings = get_settings()
    current_user = build_user_from_rep(rep_id, db) if rep_id is not None else None
    tools = SalesTools(SalesQueryService(db, current_user, get_redis_client()))
    memory_service = MemoryService(db)
    context = {
        "current_user": current_user,
        "settings": settings,
        "tools": tools,
        "memory_service": memory_service,
        "today": date.today().isoformat(),
        "request_id": uuid4().hex,
    }
    return context, memory_service


# 定义函数 _merge_state_patch，作为当前文件内部的辅助函数，给主流程提供支撑。
def _merge_state_patch(state: dict[str, Any], patch: Any) -> None:
    """
    作用：执行_merge_state_patch对应的业务逻辑。
    参数：state、patch。
    返回：函数执行后的结果。
    """
    if isinstance(patch, dict):
        state.update(patch)


# 定义函数 _parse_args，负责当前文件中的一个关键步骤或对外能力。
def _parse_args() -> argparse.Namespace:
    """
    作用：执行_parse_args对应的业务逻辑。
    参数：无。
    返回：函数执行后的结果。
    """
    parser = argparse.ArgumentParser(description="演示 sales-agent 当前 ReAct 图流程的每个节点输出")
    parser.add_argument("--message", default="本月华东区销售额是多少？", help="要发送给 Agent 的问题")
    parser.add_argument(
        "--session-id",
        default=f"langgraph-demo-{uuid4().hex[:8]}",
        help="本次演示使用的会话 ID，默认自动生成，避免和已有会话混用",
    )
    parser.add_argument("--rep-id", type=int, default=None, help="可选：模拟某个销售员身份执行问题")
    parser.add_argument("--raw", action="store_true", help="额外打印每个节点的原始输出 JSON")
    parser.add_argument(
        "--keep-session",
        action="store_true",
        help="默认演示完成后会清理本次 session 记忆；传入该参数可保留会话",
    )
    return parser.parse_args()


# 定义函数 main，作为脚本入口，串起当前文件的整体执行流程。
def main() -> int:
    """
    作用：作为脚本入口，串联整体执行流程。
    参数：无。
    返回：函数执行后的结果。
    """
    sys.stdout.reconfigure(encoding="utf-8")
    args = _parse_args()
    db = SessionLocal()
    memory_service: MemoryService | None = None
    final_state: dict[str, Any] = {}

    try:
        context, memory_service = _build_context(db, args.rep_id)
        graph = get_sales_graph()
        initial_state = {
            "session_id": args.session_id,
            "request_text": args.message,
        }

        _print_block_title("LangGraph 节点演示")
        print(f"问题：{args.message}")
        print(f"session_id：{args.session_id}")
        print(f"执行身份：{context['current_user'].username if context['current_user'] else '未登录 / 访客模式'}")

        step = 0
        for event in graph.stream(initial_state, context=context, stream_mode="updates"):
            for node_name, node_output in event.items():
                step += 1
                _merge_state_patch(final_state, node_output)
                _print_node_output(step, node_name, node_output, args.raw)

        _print_block_title("最终汇总")
        print("最终回答：")
        print(final_state.get("final_answer") or "")
        print()
        print(f"ReAct 轮次：{final_state.get('react_round_count')}")
        print(f"工具累计调用次数：{final_state.get('tool_call_count')}")
        print()
        print(f"图表产物数：{len(final_state.get('artifacts') or [])}")
        if final_state.get("artifacts"):
            _print_artifacts_preview(final_state["artifacts"])
        return 0
    except Exception as exc:
        print("演示执行失败：", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        if memory_service is not None and not args.keep_session:
            memory_service.clear_session(args.session_id)
            print()
            print(f"已清理演示 session：{args.session_id}")
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
