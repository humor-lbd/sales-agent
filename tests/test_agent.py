"""
文件作用：
- 验证 Agent 主流程，尤其是流式回复和产物持久化行为。
- 阅读这个文件时，建议先看文件头说明，再顺着主要函数或类往下追踪。
"""

import sys
from types import SimpleNamespace

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage

from app.graph.nodes import react_agent as react_agent_module
from app.logic.agent import SalesAgent


# 定义类 FakeMemoryService，把当前文件相关的状态或能力封装起来，便于在其他模块中复用。
class FakeMemoryService:
    def __init__(self):
        """
        作用：执行__init__对应的业务逻辑。
        参数：无。
        返回：函数执行后的结果。
        """
        self.saved_messages = None

    def get_messages(self, session_id):
        """
        作用：获取messages相关数据。
        参数：session_id。
        返回：函数执行后的结果。
        """
        return [{"role": "assistant", "content": "历史回复"}]

    def save_messages(self, session_id, messages):
        """
        作用：保存messages结果。
        参数：session_id、messages。
        返回：函数执行后的结果。
        """
        self.saved_messages = (session_id, messages)


# 定义类 FakeGraph，把当前文件相关的状态或能力封装起来，便于在其他模块中复用。
class FakeGraph:
    def invoke(self, state, context=None):
        """
        作用：执行invoke对应的业务逻辑。
        参数：state、context。
        返回：函数执行后的结果。
        """
        return {
            "session_id": state["session_id"],
            "request_text": state["request_text"],
            "messages": [{"role": "assistant", "content": "历史回复"}],
            "plan": {"intent": "region_ranking", "need_chart": True, "chart_type": "bar"},
            "tool_results": {
                "text": "华东区排名第一，销售额 ¥1,000。",
                "rows": [{"name": "华东区", "value": 1000}],
                "chart_title": "区域排名",
            },
            "final_answer": "华东区排名第一。",
            "artifacts": [
                {
                    "kind": "echarts",
                    "slot": "main_chart",
                    "title": "区域排名",
                    "option": {"xAxis": {"type": "category", "data": ["华东区"]}, "yAxis": {"type": "value"}, "series": [{"type": "bar", "data": [1000]}]},
                }
            ],
        }


class FakeTraceChatModel:
    def __init__(self):
        """
        作用：执行__init__对应的业务逻辑。
        参数：无。
        返回：函数执行后的结果。
        """
        self.call_count = 0
        self.bind_count = 0

    def bind_tools(self, tools):
        """
        作用：模拟模型绑定工具。
        参数：tools。
        返回：自身。
        """
        self.bind_count += 1
        return self

    def invoke(self, messages):
        """
        作用：模拟 ReAct 两轮模型输出：第一轮调工具，第二轮给最终答案。
        参数：messages。
        返回：AIMessage。
        """
        self.call_count += 1
        if self.call_count == 1:
            return AIMessage(
                content="我需要先查询华东区本月销售汇总。",
                tool_calls=[
                    {
                        "name": "get_sales_summary",
                        "args": {"start_date": "2026-04-01", "end_date": "2026-04-30", "region_name": "华东区"},
                        "id": "call-summary",
                    }
                ],
            )
        return AIMessage(content="华东区本月销售额是 ¥1,000，整体表现稳定。")


class FakeStreamingAnswerModel:
    def bind_tools(self, tools):
        return self

    def stream(self, messages):
        yield AIMessageChunk(content="华东区本月销售额是 ")
        yield AIMessageChunk(content="¥1,000，整体表现稳定。")

    def invoke(self, messages):
        return AIMessage(content="华东区本月销售额是 ¥1,000，整体表现稳定。")


class FakeChartStreamingModel:
    def bind_tools(self, tools):
        return self

    def stream(self, messages):
        yield AIMessageChunk(content="近6个月销售趋势先升后降，")
        yield AIMessageChunk(content="已生成折线图，请查看下方。")

    def invoke(self, messages):
        return AIMessage(content="近6个月销售趋势先升后降，已生成折线图，请查看下方。")


class FakeTraceTools:
    def __init__(self):
        """
        作用：执行__init__对应的业务逻辑。
        参数：无。
        返回：函数执行后的结果。
        """
        self.service = SimpleNamespace(current_user=None)

    def query_orders(self, start_date, end_date, region_name=None, rep_name=None, limit=20):
        """
        作用：模拟订单查询工具。
        参数：start_date、end_date、region_name、rep_name、limit。
        返回：工具结果。
        """
        return "订单查询结果"

    def get_sales_summary(self, start_date, end_date, region_name=None):
        """
        作用：模拟销售汇总工具。
        参数：start_date、end_date、region_name。
        返回：工具结果。
        """
        return f"销售额汇总（{start_date} 至 {end_date}，{region_name or '全公司'}）：\n总销售额：¥1,000"

    def get_top_reps(self, start_date, end_date, region_name=None, top_n=5):
        return "销售员排名"

    def get_region_ranking(self, start_date, end_date):
        return "大区排名"

    def get_top_products(self, start_date, end_date, top_n=10, region_name=None):
        return "产品排名"

    def calc_month_over_month(self, current_start, current_end, prev_start=None, prev_end=None, region_name=None):
        return "环比增长 10%"

    def calc_year_over_year(self, start_date, end_date, region_name=None):
        return "同比增长 12%"

    def get_monthly_trend(self, months, region_name=None):
        return "月度趋势"

    def generate_line_chart(self, months, region_name=None, title=None):
        return {"message": "已生成折线图。", "artifact": None}

    def generate_bar_chart(self, dimension, start_date, end_date, title=None, top_n=10):
        return {"message": "已生成柱状图。", "artifact": None}

    def generate_pie_chart(self, dimension, start_date, end_date, title=None, top_n=10):
        return {"message": "已生成饼图。", "artifact": None}

    def detect_all_anomalies(self):
        return "暂无异常"


# 定义函数 test_agent_chat_stream_emits_react_answer，负责当前文件中的一个关键步骤或对外能力。
def test_agent_chat_stream_emits_react_answer():
    """
    作用：验证对应功能是否符合预期。
    参数：无。
    返回：函数执行后的结果。
    """
    memory = FakeMemoryService()
    tools = SimpleNamespace(service=SimpleNamespace(current_user=None))
    agent = SalesAgent(tools, memory)
    agent.stream_graph = FakeGraph()

    events = list(agent.chat_stream("stream-demo", "请画出区域排名图"))
    token_events = [event for event in events if event["event"] == "token"]
    artifact_events = [event for event in events if event["event"] == "artifacts"]
    status_events = [event for event in events if event["event"] == "status"]

    assert status_events
    assert token_events[0] == {"event": "token", "data": "华东区排名第一。"}
    assert artifact_events[0]["event"] == "artifacts"
    assert events[-1] == {"event": "done", "data": "[DONE]"}
    assert memory.saved_messages is not None
    assert memory.saved_messages[0] == "stream-demo"
    assert memory.saved_messages[1][-1]["content"] == "华东区排名第一。"
    assert memory.saved_messages[1][-1]["artifacts"][0]["kind"] == "echarts"


def test_agent_chat_stream_prints_each_react_round(monkeypatch, capsys):
    """
    作用：验证单独运行 test_agent.py 时能看到每轮模型输出和工具调用打印。
    参数：monkeypatch、capsys。
    返回：无。
    """
    fake_model = FakeTraceChatModel()
    build_calls = {"count": 0}

    def fake_builder(settings, temperature=0.2):
        build_calls["count"] += 1
        return fake_model

    monkeypatch.setattr(react_agent_module, "build_chat_model", fake_builder)

    memory = FakeMemoryService()
    agent = SalesAgent(FakeTraceTools(), memory)

    events = list(agent.chat_stream("trace-demo", "华东区本月销售额是多少？"))
    output = capsys.readouterr().out
    with capsys.disabled():
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        print(output.encode(encoding, errors="replace").decode(encoding, errors="replace"), end="")

    assert "LLM 第 1 轮输出" in output
    assert "我需要先查询华东区本月销售汇总。" in output
    assert "LLM 第 1 轮工具调用" in output
    assert "get_sales_summary" in output
    assert "工具调用开始 #1" in output
    assert "工具调用完成 #1" in output
    assert "LLM 第 2 轮输出" in output
    assert "华东区本月销售额是 ¥1,000" in output
    reply = "".join(event["data"] for event in events if event["event"] == "token")
    assert reply == "华东区本月销售额是 ¥1,000，整体表现稳定。"
    assert build_calls["count"] == 1
    assert fake_model.bind_count == 1
    assert events[-1] == {"event": "done", "data": "[DONE]"}


def test_agent_chat_stream_streams_llm_tokens_without_post_chunking(monkeypatch):
    """
    作用：验证流式问答会直接使用模型 stream 输出 token，而不是在末尾再切片。
    参数：monkeypatch。
    返回：无。
    """
    monkeypatch.setattr(react_agent_module, "build_chat_model", lambda settings, temperature=0.2: FakeStreamingAnswerModel())

    memory = FakeMemoryService()
    agent = SalesAgent(FakeTraceTools(), memory)

    events = list(agent.chat_stream("stream-llm", "华东区本月销售额是多少？"))

    token_events = [event["data"] for event in events if event["event"] == "token"]
    assert token_events == ["华东区本月销售额是 ", "¥1,000，整体表现稳定。"]
    assert events[-1] == {"event": "done", "data": "[DONE]"}


def test_stream_react_agent_node_streams_artifact_summary_after_tool_loop(monkeypatch):
    """
    作用：验证带 artifact 的分析收尾在 tool-loop 之后也会直接流式输出。
    参数：monkeypatch。
    返回：无。
    """
    monkeypatch.setattr(react_agent_module, "build_chat_model", lambda settings, temperature=0.2: FakeChartStreamingModel())

    runtime = SimpleNamespace(
        context={
            "settings": SimpleNamespace(
                agent_max_tool_calls=6,
                agent_trace_enabled=False,
                openai_model="fake-model",
                openai_api_key="test-key",
                openai_base_url="http://localhost",
                openai_timeout_seconds=30,
            ),
            "today": "2026-04-25",
            "current_user": None,
            "tools": FakeTraceTools(),
            "request_id": "chart-followup-stream",
        }
    )
    state = {
        "request_text": "请结合图表总结近6个月销售趋势",
        "react_messages": [HumanMessage(content="请结合图表总结近6个月销售趋势")],
        "tool_results": {"text": "2026-01 达到峰值，随后持续回落。"},
        "artifacts": [{"kind": "echarts", "title": "近6个月销售趋势分析"}],
        "tool_call_count": 1,
        "react_round_count": 1,
    }

    stream = react_agent_module.stream_react_agent_node(state, runtime)
    events = []
    while True:
        try:
            events.append(next(stream))
        except StopIteration as stop:
            result = stop.value
            break

    assert [event["event"] for event in events] == ["status", "token", "token"]
    assert [event["data"] for event in events if event["event"] == "token"] == ["近6个月销售趋势先升后降，", "已生成折线图，请查看下方。"]
    assert result["streamed_final_answer"] is True
    assert result["final_answer"] == "近6个月销售趋势先升后降，已生成折线图，请查看下方。"
