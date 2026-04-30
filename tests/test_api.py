"""
文件作用：
- 验证接口层是否按约定返回响应和事件流。
- 阅读这个文件时，建议先看文件头说明，再顺着主要函数或类往下追踪。
"""

from fastapi.testclient import TestClient

from app.api import routes
from app.core.metrics import runtime_metrics
from app.main import app


client = TestClient(app)


# 定义函数 test_health，负责当前文件中的一个关键步骤或对外能力。
def test_health():
    """
    作用：验证对应功能是否符合预期。
    参数：无。
    返回：函数执行后的结果。
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# 定义类 FakeAgent，把当前文件相关的状态或能力封装起来，便于在其他模块中复用。
class FakeAgent:
    def chat(self, session_id, message):
        """
        作用：执行chat对应的业务逻辑。
        参数：session_id、message。
        返回：函数执行后的结果。
        """
        return {
            "reply": f"收到：{message}",
            "artifacts": [
                {
                    "kind": "echarts",
                    "slot": "main_chart",
                    "title": "测试图表",
                    "option": {"xAxis": {"type": "category", "data": ["A"]}, "yAxis": {"type": "value"}, "series": [{"type": "bar", "data": [1]}]},
                }
            ],
        }

    def chat_stream(self, session_id, message):
        """
        作用：执行chat_stream对应的业务逻辑。
        参数：session_id、message。
        返回：函数执行后的结果。
        """
        yield {"event": "token", "data": "收"}
        yield {"event": "token", "data": "到"}
        yield {"event": "artifacts", "data": '[{"kind":"echarts","slot":"main_chart","option":{"xAxis":{"type":"category","data":["A"]},"yAxis":{"type":"value"},"series":[{"type":"bar","data":[1]}]}}]'}
        yield {"event": "done", "data": "[DONE]"}


# 定义类 FakeTools，把当前文件相关的状态或能力封装起来，便于在其他模块中复用。
class FakeTools:
    def generate_line_chart(self, months, region_name=None, title=None):
        """
        作用：执行generate_line_chart对应的业务逻辑。
        参数：months、region_name、title。
        返回：函数执行后的结果。
        """
        return {
            "message": "已生成折线图。",
            "artifact": {
                "kind": "echarts",
                "slot": "main_chart",
                "title": title or "测试趋势",
                "option": {"xAxis": {"type": "category", "data": ["2026-03"]}, "yAxis": {"type": "value"}, "series": [{"type": "line", "data": [1]}]},
            },
        }


# 定义函数 test_chat_endpoint，负责当前文件中的一个关键步骤或对外能力。
def test_chat_endpoint(monkeypatch):
    """
    作用：验证对应功能是否符合预期。
    参数：monkeypatch。
    返回：函数执行后的结果。
    """
    monkeypatch.setattr(routes, "build_agent", lambda db, current_user: FakeAgent())

    response = client.post("/agent/chat", json={"sessionId": "api-demo", "message": "测试同步"})

    assert response.status_code == 200
    body = response.json()
    assert body["sessionId"] == "api-demo"
    assert body["reply"] == "收到：测试同步"
    assert body["artifacts"][0]["kind"] == "echarts"
    assert "durationMs" in body


# 定义函数 test_chat_stream_endpoint，负责当前文件中的一个关键步骤或对外能力。
def test_chat_stream_endpoint(monkeypatch):
    """
    作用：验证对应功能是否符合预期。
    参数：monkeypatch。
    返回：函数执行后的结果。
    """
    monkeypatch.setattr(routes, "build_agent", lambda db, current_user: FakeAgent())

    response = client.post("/agent/chat/stream", json={"sessionId": "api-stream", "message": "测试流式"})

    assert response.status_code == 200
    assert "event: token" in response.text
    assert "data: 收" in response.text
    assert "event: artifacts" in response.text
    assert "event: done" in response.text


# 定义函数 test_metrics_endpoint，负责当前文件中的一个关键步骤或对外能力。
def test_metrics_endpoint():
    """
    作用：验证对应功能是否符合预期。
    参数：无。
    返回：函数执行后的结果。
    """
    runtime_metrics.reset()
    client.get("/health")

    response = client.get("/ops/metrics")

    assert response.status_code == 200
    body = response.json()
    assert body["requests"]["total"] >= 1
    assert "GET /health" in body["requests"]["byPath"]


# 定义函数 test_line_chart_tool_endpoint，负责当前文件中的一个关键步骤或对外能力。
def test_line_chart_tool_endpoint(monkeypatch):
    """
    作用：验证对应功能是否符合预期。
    参数：monkeypatch。
    返回：函数执行后的结果。
    """
    monkeypatch.setattr(routes, "build_sales_tools", lambda db, current_user: FakeTools())

    response = client.post("/test/tool/line-chart", json={"months": 3, "regionName": "华东区", "title": "测试趋势"})

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "已生成折线图。"
    assert body["artifact"]["kind"] == "echarts"
    assert body["artifact"]["option"]["series"][0]["type"] == "line"
