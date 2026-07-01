"""
调用 LLM 生成 SQL JSON。
"""

from __future__ import annotations

import json
import re
import time
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import Settings
from app.core.llm import build_chat_model
from app.core.metrics import runtime_metrics
from app.graph.utils import content_to_text
from app.logic.sql_agent.models import GeneratedSql, SqlTaskSpec
from app.logic.sql_agent.prompts import SQL_GENERATION_SYSTEM_PROMPT, build_sql_generation_prompt
from app.logic.sql_agent.schema_registry import SqlSchemaRegistry


class LlmSqlGenerator:
    """把结构化查询任务转换成候选 SQL。"""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.last_usage: dict[str, int] = {}
        self.last_duration_ms: float = 0.0
        self._llm = None
        self._llm_model_name: str = ""

    def _get_llm(self):
        """获取或缓存 LLM 实例，避免每次 generate 都新建。"""
        model_name = self.settings.llm_sql_model or self.settings.openai_model
        if self._llm is None or self._llm_model_name != model_name:
            self._llm = build_chat_model(
                self.settings,
                temperature=self.settings.llm_sql_temperature,
                model_name=model_name,
            )
            self._llm_model_name = model_name
        return self._llm

    @staticmethod
    def _extract_json(text: str) -> str:
        text = text.strip()
        fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.IGNORECASE | re.DOTALL)
        if fence:
            return fence.group(1)
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return text[start : end + 1]
        return text

    @staticmethod
    def _usage_from_response(response: Any) -> dict[str, int]:
        usage = getattr(response, "usage_metadata", None) or {}
        prompt_tokens = int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("output_tokens") or usage.get("completion_tokens") or 0)
        total_tokens = int(usage.get("total_tokens") or (prompt_tokens + completion_tokens))
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }

    def generate(self, task: SqlTaskSpec, schema: SqlSchemaRegistry, errors: list[str] | None = None) -> GeneratedSql:
        if not self.settings.openai_api_key:
            raise RuntimeError("未配置 OPENAI_API_KEY，无法生成 LLM SQL")

        model_name = self.settings.llm_sql_model or self.settings.openai_model
        llm = self._get_llm()
        messages = [
            SystemMessage(content=SQL_GENERATION_SYSTEM_PROMPT),
            HumanMessage(content=build_sql_generation_prompt(task, schema, errors, profile=self.settings.llm_sql_prompt_profile)),
        ]
        started = time.perf_counter()
        response = llm.invoke(messages)
        self.last_duration_ms = (time.perf_counter() - started) * 1000
        runtime_metrics.record_llm_call("llm_sql", self.last_duration_ms)
        usage = self._usage_from_response(response)
        prompt_tokens = usage["prompt_tokens"]
        completion_tokens = usage["completion_tokens"]
        total_tokens = usage["total_tokens"]
        self.last_usage = usage
        runtime_metrics.record_llm_sql_tokens(prompt_tokens, completion_tokens, total_tokens)
        raw_text = content_to_text(response.content)
        extracted = self._extract_json(raw_text)
        try:
            payload = json.loads(extracted)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"LLM 返回了无法解析的 JSON (长度={len(extracted)}): "
                f"{extracted[:200]}... 原始错误: {exc}"
            ) from exc
        try:
            return GeneratedSql.model_validate(payload)
        except Exception as exc:
            raise RuntimeError(
                f"LLM 返回的 JSON 不符合 GeneratedSql 结构: {payload} 错误: {exc}"
            ) from exc
