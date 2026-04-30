"""
文件作用：
- 验证 ReAct 工具包装和工具执行节点的核心行为。
- 阅读这个文件时，建议先看 FakeRuntime，再看两个测试。
"""

from types import SimpleNamespace

from langchain_core.messages import AIMessage, HumanMessage

from app.graph.nodes import react_agent as react_agent_module
from app.graph.nodes.react_tool_executor import react_tool_executor_node
from app.graph.react_tools import build_react_tools


class FakeTools:
    def query_orders(self, start_date, end_date, region_name=None, rep_name=None, limit=20):
        return "订单查询结果"

    def get_sales_summary(self, start_date, end_date, region_name=None):
        return f"{region_name or '全公司'}销售额 ¥1,000"

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
        return {
            "message": "已生成折线图。",
            "artifact": {
                "kind": "echarts",
                "slot": "main_chart",
                "title": title or "趋势图",
                "option": {"series": [{"type": "line", "data": [1]}]},
            },
        }

    def generate_bar_chart(self, dimension, start_date, end_date, title=None, top_n=10):
        return {"message": "已生成柱状图。", "artifact": None}

    def generate_pie_chart(self, dimension, start_date, end_date, title=None, top_n=10):
        return {"message": "已生成饼图。", "artifact": None}

    def detect_all_anomalies(self):
        return "暂无异常"


class FakeRuntime:
    def __init__(self):
        self.context = {
            "tools": FakeTools(),
            "settings": SimpleNamespace(agent_max_tool_calls=6, agent_trace_enabled=True),
            "today": "2026-04-22",
            "current_user": None,
        }


class FakeChatModel:
    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        return AIMessage(
            content="我先查询销售汇总。",
            tool_calls=[
                {
                    "name": "get_sales_summary",
                    "args": {"start_date": "2026-04-01", "end_date": "2026-04-30", "region_name": "华东区"},
                    "id": "call-summary",
                }
            ],
        )


class FakeNoToolModel:
    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        return AIMessage(content="需要明确图表类型后再生成。")


class FakeChartAnalysisModel:
    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        return AIMessage(content="已生成饼状图。苹果占28%，不存在产品占14%。")


def test_build_react_tools_exposes_java_style_tool_groups():
    tools = build_react_tools(FakeTools())
    names = {tool.name for tool in tools}

    assert "query_sales_data" in names
    assert "get_sales_summary" in names
    assert "generate_line_chart" in names
    assert "detect_sales_anomalies" in names


def test_react_agent_prints_llm_output_and_tool_calls(monkeypatch, capsys):
    monkeypatch.setattr(react_agent_module, "build_chat_model", lambda settings, temperature=0.2: FakeChatModel())

    result = react_agent_module.react_agent_node(
        {
            "request_text": "华东区本月销售额是多少？",
            "react_messages": [HumanMessage(content="华东区本月销售额是多少？")],
            "tool_call_count": 0,
        },
        FakeRuntime(),
    )

    output = capsys.readouterr().out
    assert "LLM 第 1 轮输出" in output
    assert "我先查询销售汇总。" in output
    assert "LLM 第 1 轮工具调用" in output
    assert "get_sales_summary" in output
    assert result["final_answer"] is None


def test_react_agent_does_not_force_chart_tool_when_model_does_not_call_one(monkeypatch):
    monkeypatch.setattr(react_agent_module, "build_chat_model", lambda settings, temperature=0.2: FakeNoToolModel())

    result = react_agent_module.react_agent_node(
        {
            "request_text": "图呢",
            "messages": [
                {
                    "role": "assistant",
                    "content": "近6个月销售趋势已分析完成，建议生成折线图查看下方。",
                }
            ],
            "react_messages": [
                HumanMessage(content="近6个月销售趋势"),
                AIMessage(content="近6个月销售趋势已分析完成，建议生成折线图查看下方。"),
                HumanMessage(content="图呢"),
            ],
            "artifacts": [],
            "tool_call_count": 0,
        },
        FakeRuntime(),
    )

    last_message = result["react_messages"][-1]
    assert result["final_answer"] == "需要明确图表类型后再生成。"
    assert not getattr(last_message, "tool_calls", None)


def test_react_agent_uses_short_answer_for_chart_only_followup_with_artifact(monkeypatch):
    monkeypatch.setattr(react_agent_module, "build_chat_model", lambda settings, temperature=0.2: FakeChartAnalysisModel())

    result = react_agent_module.react_agent_node(
        {
            "request_text": "生成饼状图",
            "react_messages": [HumanMessage(content="生成饼状图")],
            "artifacts": [{"kind": "echarts", "option": {"series": [{"type": "pie"}]}}],
            "tool_call_count": 1,
        },
        FakeRuntime(),
    )

    assert result["final_answer"] == "已生成饼状图，请查看下方。"


def test_react_tool_executor_collects_artifact(capsys):
    ai_message = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "generate_line_chart",
                "args": {"months": 6, "region_name": "华东区", "title": "近6个月趋势"},
                "id": "call-1",
            }
        ],
    )

    result = react_tool_executor_node(
        {"react_messages": [ai_message], "artifacts": [], "tool_call_count": 0},
        FakeRuntime(),
    )

    assert result["tool_call_count"] == 1
    assert result["artifacts"][0]["kind"] == "echarts"
    assert result["react_messages"][-1].content == "已生成折线图。"
    output = capsys.readouterr().out
    assert "工具调用开始 #1" in output
    assert "generate_line_chart" in output
    assert "工具调用完成 #1" in output
    assert "已生成折线图。" in output
