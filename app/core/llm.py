"""
LLM 客户端构建工具。

从 app/graph/helpers.py 提取，解决 logic 层反向依赖 graph 层的问题。
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI

from app.core.config import Settings


def build_chat_model(settings: Settings, temperature: float = 0.1, model_name: str | None = None) -> ChatOpenAI:
    """构建 ChatOpenAI 实例。"""
    return ChatOpenAI(
        model=model_name or settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        timeout=settings.openai_timeout_seconds,
        temperature=temperature,
    )
