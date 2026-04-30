"""
文件作用：
- 验证会话记忆进入 ReAct 消息列表的筛选规则。
"""

from types import SimpleNamespace

from langchain_core.messages import AIMessage, HumanMessage

from app.graph.nodes import memory as memory_module
from app.graph.nodes.memory import _build_summary_context, _history_to_react_messages, load_memory_node


def test_chart_generation_short_request_keeps_followup_history():
    """
    作用：验证“生成饼状图”这类短追问会继承上一轮主题。
    参数：无。
    返回：无。
    """
    messages = [
        {"role": "user", "content": "近6个月销售趋势"},
        {"role": "assistant", "content": "近6个月销售趋势已统计完成。"},
        {"role": "user", "content": "最畅销产品Top10"},
        {"role": "assistant", "content": "最畅销产品Top10已统计完成，时间范围为2026-03-23至2026-04-23。"},
    ]

    react_messages = _history_to_react_messages(messages, "生成饼状图")
    contents = [message.content for message in react_messages]

    assert len(react_messages) == 5
    assert "近6个月销售趋势" in contents[0]
    assert "最畅销产品Top10" in contents[2]
    assert "2026-03-23至2026-04-23" in contents[3]
    assert contents[-1] == "生成饼状图"


def test_chart_generation_short_request_keeps_previous_business_context_after_chart_reply():
    """
    作用：验证“那饼状图呢”不会只看到上一轮图表短回复，而是保留更早业务主题。
    参数：无。
    返回：无。
    """
    messages = [
        {"role": "user", "content": "最畅销产品Top10"},
        {"role": "assistant", "content": "最畅销产品Top10已统计完成，时间范围为2026-03-23至2026-04-23。"},
        {"role": "user", "content": "生成柱状图"},
        {"role": "assistant", "content": "已生成柱状图，请查看下方。"},
    ]

    react_messages = _history_to_react_messages(messages, "那饼状图呢")
    contents = [message.content for message in react_messages]

    assert len(react_messages) == 5
    assert "最畅销产品Top10" in contents[0]
    assert "生成柱状图" in contents[2]
    assert contents[-1] == "那饼状图呢"


def test_independent_request_does_not_keep_previous_context():
    """
    作用：验证新的独立问题不会带入上一轮长回答。
    参数：无。
    返回：无。
    """
    react_messages = _history_to_react_messages(
        [{"role": "assistant", "content": "上一轮是产品Top10。"}],
        "本季度Top5销售员",
    )

    assert len(react_messages) == 1
    assert isinstance(react_messages[0], HumanMessage)
    assert react_messages[0].content == "本季度Top5销售员"


def test_build_summary_context_compresses_older_history():
    """
    作用：验证超出窗口的更早消息会被压缩成摘要文本。
    参数：无。
    返回：无。
    """
    messages = [
        {"role": "user", "content": "先看一季度销售额"},
        {"role": "assistant", "content": "一季度销售额是 ¥10,000。"},
        {"role": "user", "content": "再看二季度趋势"},
        {"role": "assistant", "content": "二季度趋势整体上涨。"},
        {"role": "user", "content": "最后看异常情况"},
        {"role": "assistant", "content": "异常主要集中在华东区。"},
    ]

    summary = _build_summary_context(messages, keep_recent=2, summary_items=3, max_chars=20)

    assert summary is not None
    assert "更早对话摘要" in summary
    assert "用户：" in summary
    assert "助手：" in summary


def test_load_memory_node_prefers_llm_summary_when_triggered(monkeypatch):
    """
    作用：验证超过阈值的更早历史会优先走 LLM 摘要。
    参数：monkeypatch。
    返回：无。
    """
    messages = [
        {"role": "user", "content": "先看最畅销产品Top10"},
        {"role": "assistant", "content": "最畅销产品Top10已统计完成，时间范围为2026-03-23至2026-04-23。"},
        {"role": "user", "content": "再看各大区占比"},
        {"role": "assistant", "content": "各大区占比已统计完成。"},
        {"role": "user", "content": "生成饼状图"},
        {"role": "assistant", "content": "已生成饼状图，请查看下方。", "artifacts": [{"title": "各大区占比"}]},
    ]

    class FakeSummaryModel:
        def invoke(self, prompt):
            return AIMessage(content="1. 用户刚刚先看了最畅销产品Top10。\n2. 已明确时间范围是2026-03-23至2026-04-23。\n3. 后续又查看了各大区占比并生成过饼状图。")

    monkeypatch.setattr(memory_module, "build_chat_model", lambda settings, temperature=0.0, model_name=None: FakeSummaryModel())

    runtime = SimpleNamespace(
        context={
            "settings": SimpleNamespace(
                agent_memory_followup_limit=4,
                agent_memory_window_messages=2,
                agent_memory_llm_summary_enabled=True,
                agent_memory_llm_summary_model="",
                agent_memory_llm_summary_trigger_messages=2,
                agent_memory_summary_messages=3,
                agent_memory_summary_chars=50,
            ),
            "memory_service": SimpleNamespace(get_messages=lambda session_id: messages),
            "middleware": None,
        }
    )

    state = {"session_id": "memory-llm", "request_text": "那产品的饼状图呢"}
    result = load_memory_node(state, runtime)

    assert result["summary_context"] is not None
    assert "更早对话摘要" in result["summary_context"]
    assert "最畅销产品Top10" in result["summary_context"]
    assert "2026-03-23至2026-04-23" in result["summary_context"]


def test_load_memory_node_falls_back_to_rule_summary_when_llm_summary_fails(monkeypatch):
    """
    作用：验证 LLM 摘要失败时会自动回退到规则摘要，不影响主流程。
    参数：monkeypatch。
    返回：无。
    """
    messages = [
        {"role": "user", "content": "先看一季度销售额"},
        {"role": "assistant", "content": "一季度销售额是 ¥10,000。"},
        {"role": "user", "content": "再看二季度趋势"},
        {"role": "assistant", "content": "二季度趋势整体上涨。"},
    ]

    class BrokenSummaryModel:
        def invoke(self, prompt):
            raise RuntimeError("summary gateway down")

    monkeypatch.setattr(memory_module, "build_chat_model", lambda settings, temperature=0.0, model_name=None: BrokenSummaryModel())

    runtime = SimpleNamespace(
        context={
            "settings": SimpleNamespace(
                agent_memory_followup_limit=1,
                agent_memory_window_messages=1,
                agent_memory_llm_summary_enabled=True,
                agent_memory_llm_summary_model="",
                agent_memory_llm_summary_trigger_messages=1,
                agent_memory_summary_messages=3,
                agent_memory_summary_chars=20,
            ),
            "memory_service": SimpleNamespace(get_messages=lambda session_id: messages),
            "middleware": None,
        }
    )

    state = {"session_id": "memory-fallback", "request_text": "继续"}
    result = load_memory_node(state, runtime)

    assert result["summary_context"] is not None
    assert "更早对话摘要" in result["summary_context"]
    assert "用户：" in result["summary_context"]
