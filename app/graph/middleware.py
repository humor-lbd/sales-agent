"""
文件作用：
- 提供 Agent 执行过程中的统一钩子，收口工具日志、模型轮次和流式事件输出。
- 阅读这个文件时，建议先看 AgentMiddleware，再看每个 hook 方法。
"""

from __future__ import annotations

from typing import Any, Callable

from app.graph.trace import trace_event


class AgentMiddleware:
    """
    统一的 Agent 中间层。

    把日志追踪、流式状态和事件输出集中到一处，避免节点里重复散落同样的逻辑。
    """

    def __init__(self, settings: Any, request_id: str, stream_sink: Callable[[str, Any], None] | None = None) -> None:
        self.settings = settings
        self.request_id = request_id
        self.stream_sink = stream_sink
        self._reply_started = False

    def _payload(self, payload: Any | None = None) -> Any:
        if payload is None:
            return {"request_id": self.request_id}
        return {"request_id": self.request_id, "payload": payload}

    def trace(self, title: str, payload: Any | None = None) -> None:
        """
        作用：输出带 request_id 的统一 trace 日志。
        参数：title、payload。
        返回：无。
        """
        trace_event(self.settings, title, self._payload(payload))

    def emit(self, event: str, data: Any) -> None:
        """
        作用：把事件发送给上层流式调用方。
        参数：event、data。
        返回：无。
        """
        if self.stream_sink is not None:
            self.stream_sink(event, data)

    def emit_token(self, text: str) -> None:
        """
        作用：发送模型 token，并在第一段 token 前自动补一个输出状态。
        参数：text。
        返回：无。
        """
        if not text or self.stream_sink is None:
            return
        if not self._reply_started:
            self.emit("status", "正在输出回答...")
            self._reply_started = True
        self.emit("token", text)

    def on_llm_round(self, round_no: int, response_text: str, tool_calls: list[dict[str, Any]] | str) -> None:
        """
        作用：记录每轮 LLM 输出和工具决策。
        参数：round_no、response_text、tool_calls。
        返回：无。
        """
        self.trace(f"LLM 第 {round_no} 轮输出", response_text or "<空>")
        self.trace(f"LLM 第 {round_no} 轮工具调用", tool_calls)

    def before_tool(self, index: int, name: str | None, args: dict[str, Any]) -> None:
        """
        作用：记录工具调用开始事件。
        参数：index、name、args。
        返回：无。
        """
        self.trace(f"工具调用开始 #{index}", {"name": name, "args": args})

    def after_tool(self, index: int, name: str | None, result: str, has_artifact: bool) -> None:
        """
        作用：记录工具调用完成事件。
        参数：index、name、result、has_artifact。
        返回：无。
        """
        self.trace(f"工具调用完成 #{index}", {"name": name, "result": result, "has_artifact": has_artifact})

    def on_tool_error(self, index: int, name: str | None, error: str) -> None:
        """
        作用：记录工具异常。
        参数：index、name、error。
        返回：无。
        """
        self.trace(f"工具调用异常 #{index}", {"name": name, "error": error})
