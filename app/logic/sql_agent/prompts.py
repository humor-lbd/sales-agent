"""
SQL 生成提示词。
"""

from __future__ import annotations

import json

from app.logic.sql_agent.models import SqlTaskSpec
from app.logic.sql_agent.schema_registry import SqlSchemaRegistry


SQL_GENERATION_SYSTEM_PROMPT = """
你是 sales-agent 项目的 MySQL SQL 生成器。
你只能生成只读 SELECT SQL，不能生成 INSERT、UPDATE、DELETE、DROP、ALTER、TRUNCATE、CREATE、REPLACE、CALL、LOAD、GRANT、REVOKE。
你只能使用给定 schema 中列出的表、字段和 join 关系。
你必须使用命名参数，例如 :start_date、:end_date、:region_id。
不要把参数值直接拼进 SQL。
除 JSON 外不要输出任何解释、Markdown 或代码块。
""".strip()


SQL_GENERATION_USER_PROMPT = """
数据库方言：MySQL 8。

允许访问的表、字段、join 关系：
{schema_context}

业务指标口径：
{metric_context}

当前查询任务：
{task_spec_json}

返回 JSON，格式必须为：
{{
  "sql": "SELECT ...",
  "params": {{"start_date": "YYYY-MM-DD"}},
  "result_columns": ["column_a", "column_b"],
  "reason": "一句话说明选择该 SQL 的原因",
  "confidence": 0.0
}}

硬性要求：
1. SQL 必须是单条 SELECT 或 WITH ... SELECT。
2. 明细查询必须带 LIMIT，订单明细查询不要默认过滤 o.status = 'COMPLETED'，需要返回全部订单状态。
3. 销售额、排名、趋势默认必须过滤 o.status = 'COMPLETED'。
4. 不允许查询 sa_chat_memory。
5. 不允许查询系统库。
6. 不允许使用未给出的字段。
7. 不允许使用 SELECT *。
8. 只返回 JSON。
{repair_instruction}
""".strip()


def build_sql_generation_prompt(
    task: SqlTaskSpec,
    schema: SqlSchemaRegistry,
    errors: list[str] | None = None,
    profile: str = "compact",
) -> str:
    """构造 SQL 生成用户提示词。"""
    repair_instruction = ""
    if errors:
        repair_instruction = "\n上一次 SQL 校验失败，错误如下：\n" + "\n".join(f"- {error}" for error in errors)
    task_instructions = {
        "refund_rates": "当前任务 refund_rates 必须返回 rep_id、refunded、total。refunded 使用 SUM(CASE WHEN o.status = 'REFUNDED' THEN 1 ELSE 0 END)，total 使用 COUNT(o.id)，不要过滤 COMPLETED。",
        "order_detail": "当前任务 order_detail 必须返回订单明细，不能加 o.status = 'COMPLETED' 过滤，必须保留退款和取消订单。",
    }
    if task.task_type in task_instructions:
        repair_instruction += "\n" + task_instructions[task.task_type]
    return SQL_GENERATION_USER_PROMPT.format(
        schema_context=schema.schema_context(task.task_type, profile=profile),
        metric_context=schema.metric_context(task.task_type, profile=profile),
        task_spec_json=json.dumps(task.model_dump(mode="json"), ensure_ascii=False, indent=2),
        repair_instruction=repair_instruction,
    )
