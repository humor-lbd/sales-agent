"""
销售分析Agent模块

该模块封装了对外可调用的销售分析Agent，负责串起同步和流式对话链路。
主要功能包括：
- 执行同步聊天请求
- 执行流式聊天请求
- 管理会话上下文
- 处理错误情况
- 与LangGraph工作流集成
"""

from __future__ import annotations

import json
import time
from datetime import date
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

from app.core.config import get_settings
from app.core.metrics import runtime_metrics
from app.graph.builder import get_sales_graph, get_sales_stream_graph
from app.graph.helpers import (
    build_fallback_answer,
    stream_text_chunks,
)
from app.graph.middleware import AgentMiddleware
from app.graph.utils import last_ai_message
from app.graph.nodes.bootstrap import bootstrap_node
from app.graph.nodes.error_handler import build_error_state
from app.graph.nodes.guardrails import guardrails_node
from app.graph.nodes.memory import load_memory_node
from app.graph.nodes.react_agent import react_agent_node, stream_react_agent_node
from app.graph.nodes.react_tool_executor import react_tool_executor_node
from app.logic.services import MemoryService
from app.logic.tools import SalesTools


class SalesAgent:
    """
    销售分析Agent
    
    负责处理销售数据分析的对话请求，支持同步和流式响应。
    """
    def __init__(self, tools: SalesTools, memory_service: MemoryService) -> None:
        """
        初始化销售分析Agent
        
        Args:
            tools: 销售工具实例
            memory_service: 记忆服务实例
        """
        self.tools = tools
        self.memory_service = memory_service
        self.settings = get_settings()
        self.graph = get_sales_graph()
        self.stream_graph = get_sales_stream_graph()

    def _build_context(self) -> dict[str, Any]:
        """
        构建上下文信息
        
        Returns:
            包含当前用户、设置、工具等信息的上下文字典
        """
        request_id = uuid4().hex
        return {
            "current_user": self.tools.service.current_user,
            "settings": self.settings,
            "tools": self.tools,
            "memory_service": self.memory_service,
            "today": date.today().isoformat(),
            "request_id": request_id,
            "middleware": AgentMiddleware(self.settings, request_id),
        }

    def _run_graph(self, graph, session_id: str, message: str, context: dict[str, Any], metric_name: str) -> dict[str, Any]:
        """
        运行LangGraph工作流
        
        Args:
            graph: LangGraph实例
            session_id: 会话ID
            message: 用户消息
            context: 上下文信息
            metric_name: 指标名称
        
        Returns:
            工作流执行结果
        """
        started = time.perf_counter()
        initial_state = {
            "session_id": session_id,
            "request_text": message,
        }
        try:
            result = graph.invoke(initial_state, context=context)
            runtime_metrics.record_llm_call(metric_name, (time.perf_counter() - started) * 1000)
            return dict(result)
        except Exception as exc:
            error_state = build_error_state(initial_state, exc)
            history = self.memory_service.get_messages(session_id)
            assistant_message = {"role": "assistant", "content": error_state["final_answer"]}
            self.memory_service.save_messages(
                session_id,
                history + [{"role": "user", "content": message}, assistant_message],
            )
            return error_state

    @classmethod
    def _status_from_graph_update(cls, node_name: str, update: dict[str, Any]) -> str | None:
        """
        把LangGraph节点更新转换成前端可展示的流式状态
        
        Args:
            node_name: 节点名称
            update: 节点更新信息
        
        Returns:
            状态文本或None
        """
        if node_name == "load_memory":
            return "正在读取会话上下文..."
        if node_name == "guardrails":
            return "正在检查问题边界..."
        if node_name == "react_agent":
            ai_message = last_ai_message(update.get("react_messages") or [])
            tool_calls = getattr(ai_message, "tool_calls", None) or []
            if tool_calls:
                names = "、".join(call.get("name", "unknown") for call in tool_calls)
                return f"正在调用工具：{names}"
            return "正在整理最终回答..."
        if node_name == "react_tool_executor":
            return "工具结果已返回，继续分析..."
        return None

    def _stream_graph_result(self, session_id: str, message: str, context: dict[str, Any]):
        """
        流式执行LangGraph，并把节点状态更新同步给调用方
        
        Args:
            session_id: 会话ID
            message: 用户消息
            context: 上下文信息
        
        Yields:
            状态事件
        
        Returns:
            状态字典
        """
        started = time.perf_counter()
        initial_state: dict[str, Any] = {
            "session_id": session_id,
            "request_text": message,
        }

        if not hasattr(self.stream_graph, "stream"):
            yield {"event": "status", "data": "正在分析问题..."}
            result = self._run_graph(self.stream_graph, session_id, message, context, "graph_stream_prep")
            return dict(result)

        yield {"event": "status", "data": "正在分析问题..."}
        try:
            runtime = SimpleNamespace(context=context)
            state = bootstrap_node(initial_state)

            yield {"event": "status", "data": "正在读取会话上下文..."}
            state.update(load_memory_node(state, runtime))

            yield {"event": "status", "data": "正在检查问题边界..."}
            state.update(guardrails_node(state))
            if state.get("rejected"):
                runtime_metrics.record_llm_call("graph_stream_prep", (time.perf_counter() - started) * 1000)
                return state

            while True:
                result = yield from stream_react_agent_node(state, runtime)
                if result:
                    state.update(result)
                if state.get("final_answer"):
                    break

                status = self._status_from_graph_update("react_agent", state)
                if status:
                    yield {"event": "status", "data": status}

                tool_update = react_tool_executor_node(state, runtime)
                state.update(tool_update)
                status = self._status_from_graph_update("react_tool_executor", tool_update)
                if status:
                    yield {"event": "status", "data": status}

            runtime_metrics.record_llm_call("graph_stream_prep", (time.perf_counter() - started) * 1000)
            return state
        except Exception as exc:
            error_state = build_error_state(initial_state, exc)
            history = self.memory_service.get_messages(session_id)
            assistant_message = {"role": "assistant", "content": error_state["final_answer"]}
            self.memory_service.save_messages(
                session_id,
                history + [{"role": "user", "content": message}, assistant_message],
            )
            return error_state

    def _save_reply(self, state: dict[str, Any], session_id: str, message: str, reply: str, artifacts: list[dict[str, Any]] | None = None) -> None:
        """
        保存回复到会话历史
        
        Args:
            state: 状态字典
            session_id: 会话ID
            message: 用户消息
            reply: 回复内容
            artifacts: 附件列表
        """
        history = list(state.get("messages") or [])
        history.append({"role": "user", "content": message})
        assistant_message = {"role": "assistant", "content": reply}
        if artifacts:
            assistant_message["artifacts"] = artifacts
        self.memory_service.save_messages(session_id, history + [assistant_message])

    def chat(self, session_id: str, message: str) -> dict[str, Any]:
        """
        执行同步聊天请求
        
        Args:
            session_id: 会话ID
            message: 用户消息
        
        Returns:
            包含回复和附件的字典
        """
        context = self._build_context()
        result = self._run_graph(self.graph, session_id, message, context, "graph_total")
        return {
            "reply": result.get("final_answer", ""),
            "artifacts": result.get("artifacts") or [],
        }

    def chat_stream(self, session_id: str, message: str):
        """
        执行流式聊天请求
        
        Args:
            session_id: 会话ID
            message: 用户消息
        
        Yields:
            事件流，包括状态、token、附件和完成事件
        """
        context = self._build_context()
        stream = self._stream_graph_result(session_id, message, context)
        result = None
        streamed_reply = ""
        while True:
            try:
                event = next(stream)
                if isinstance(event, dict) and event.get("event") == "token":
                    streamed_reply += str(event.get("data", ""))
                yield event
            except StopIteration as stop:
                result = stop.value or {}
                break

        artifacts = result.get("artifacts") or []
        started = time.perf_counter()
        first_token_ms: float | None = None

        if result.get("final_answer") and result.get("streamed_final_answer"):
            reply = result.get("final_answer", "")
            if streamed_reply and reply.startswith(streamed_reply):
                suffix = reply[len(streamed_reply) :]
                for chunk in stream_text_chunks(suffix):
                    if chunk:
                        if first_token_ms is None:
                            first_token_ms = 0.0
                        yield {"event": "token", "data": chunk}
            self._save_reply(result, session_id, message, reply, artifacts)
            if artifacts:
                yield {"event": "artifacts", "data": json.dumps(artifacts, ensure_ascii=False)}
            runtime_metrics.record_llm_call("stream", (time.perf_counter() - started) * 1000, first_token_ms)
            yield {"event": "done", "data": "[DONE]"}
            return

        yield {"event": "status", "data": "正在输出回答..."}
        if result.get("final_answer"):
            reply = result.get("final_answer", "")
            for chunk in stream_text_chunks(reply):
                if first_token_ms is None:
                    first_token_ms = (time.perf_counter() - started) * 1000
                yield {"event": "token", "data": chunk}
            self._save_reply(result, session_id, message, reply, artifacts)
            if artifacts:
                yield {"event": "artifacts", "data": json.dumps(artifacts, ensure_ascii=False)}
            runtime_metrics.record_llm_call("stream", (time.perf_counter() - started) * 1000, first_token_ms)
            yield {"event": "done", "data": "[DONE]"}
            return

        reply = build_fallback_answer(result)
        for chunk in stream_text_chunks(reply):
            if first_token_ms is None:
                first_token_ms = (time.perf_counter() - started) * 1000
            yield {"event": "token", "data": chunk}

        self._save_reply(result, session_id, message, reply, artifacts)
        if artifacts:
            yield {"event": "artifacts", "data": json.dumps(artifacts, ensure_ascii=False)}

        runtime_metrics.record_llm_call("stream", (time.perf_counter() - started) * 1000, first_token_ms)
        yield {"event": "done", "data": "[DONE]"}
