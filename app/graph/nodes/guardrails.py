"""
文件作用：
- 拦截超出项目边界的请求，避免 Agent 执行不受控操作。
- 阅读这个文件时，建议先看文件头说明，再顺着主要函数或类往下追踪。
"""

from __future__ import annotations

from app.graph.state import GraphState


WRITE_ACTION_KEYWORDS = ["修改", "删除", "新增", "插入", "更新", "写入"]
FORECAST_KEYWORDS = ["预测", "预估", "明年销售", "未来销售"]


# 定义函数 guardrails_node，负责当前文件中的一个关键步骤或对外能力。
def guardrails_node(state: GraphState) -> GraphState:
    """
    作用：执行guardrails_node对应的业务逻辑。
    参数：state。
    返回：函数执行后的结果。
    """
    message = state.get("request_text", "")
    if any(keyword in message for keyword in WRITE_ACTION_KEYWORDS):
        return {
            "rejected": True,
            "final_answer": "我只能帮助查询和分析销售数据，不能修改、删除或新增业务数据。",
            "streamed_final_answer": False,
            "plan": {"intent": "reject", "reason": "write_action"},
        }
    if any(keyword in message for keyword in FORECAST_KEYWORDS):
        return {
            "rejected": True,
            "final_answer": "我可以分析历史销售数据，但不能预测未来销售结果。",
            "streamed_final_answer": False,
            "plan": {"intent": "reject", "reason": "forecast"},
        }
    return {"rejected": False}
