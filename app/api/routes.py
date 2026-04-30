"""
文件作用：
- 集中定义后端对外接口，并把 HTTP 请求转给 Agent、Tool 和鉴权逻辑处理。
- 阅读这个文件时，建议先看文件头说明，再顺着主要函数或类往下追踪。
"""

from __future__ import annotations

import time
from collections.abc import Iterator

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse, StreamingResponse
from openai import APIError, AuthenticationError, PermissionDeniedError, RateLimitError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.metrics import runtime_metrics
from app.core.redis_client import get_redis_client
from app.core.security import build_user_from_rep, create_access_token, get_login_user
from app.db.database import get_db
from app.logic.agent import SalesAgent
from app.logic.schemas import (
    BarPieChartRequest,
    ChatRequest,
    ChatResponse,
    ChartToolResponse,
    LineChartRequest,
    LoginRequest,
    MomRequest,
    ProductRankRequest,
    QueryRequest,
    RankRequest,
    RangeRequest,
    TrendRequest,
    UserInfo,
    YoyRequest,
)
from app.logic.services import MemoryService, SalesQueryService
from app.logic.tools import SalesTools


router = APIRouter()


def format_sse(event: str, data: object) -> str:
    """
    作用：按 SSE 规范格式化事件，确保多行内容也能被前端正确解析。
    参数：event、data。
    返回：SSE 文本片段。
    """
    text = str(data).replace("\r\n", "\n").replace("\r", "\n")
    data_lines = text.split("\n") if text else [""]
    payload = "\n".join(f"data: {line}" for line in data_lines)
    return f"event: {event}\n{payload}\n\n"


# 定义函数 build_sales_tools，负责组装当前步骤需要的对象或参数。
def build_sales_tools(db: Session, current_user: UserInfo | None) -> SalesTools:
    """
    作用：构建sales_tools对象或结构。
    参数：db、current_user。
    返回：函数执行后的结果。
    """
    return SalesTools(SalesQueryService(db, current_user, get_redis_client()))


# 定义函数 build_agent，负责组装当前步骤需要的对象或参数。
def build_agent(db: Session, current_user: UserInfo | None) -> SalesAgent:
    """
    作用：构建agent对象或结构。
    参数：db、current_user。
    返回：函数执行后的结果。
    """
    return SalesAgent(build_sales_tools(db, current_user), MemoryService(db))


# 定义函数 health，负责当前文件中的一个关键步骤或对外能力。
@router.get("/health")
def health() -> dict[str, str]:
    """
    作用：执行health对应的业务逻辑。
    参数：无。
    返回：函数执行后的结果。
    """
    return {"status": "ok"}


# 定义函数 metrics，负责当前文件中的一个关键步骤或对外能力。
@router.get("/ops/metrics")
def metrics() -> dict:
    """
    作用：执行metrics对应的业务逻辑。
    参数：无。
    返回：函数执行后的结果。
    """
    return runtime_metrics.snapshot()


# 定义函数 login，负责当前文件中的一个关键步骤或对外能力。
@router.post("/auth/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    作用：执行login对应的业务逻辑。
    参数：request、db。
    返回：函数执行后的结果。
    """
    settings = get_settings()
    user = build_user_from_rep(request.rep_id, db)
    token = create_access_token(user, settings)
    return {"token": token, "username": user.username, "role": user.role}


# 定义函数 logout，负责当前文件中的一个关键步骤或对外能力。
@router.post("/auth/logout")
def logout():
    """
    作用：执行logout对应的业务逻辑。
    参数：无。
    返回：函数执行后的结果。
    """
    return {"message": "已退出登录"}


# 定义函数 chat，负责当前文件中的一个关键步骤或对外能力。
@router.post("/agent/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db), current_user: UserInfo | None = Depends(get_login_user)) -> ChatResponse:
    """
    作用：执行chat对应的业务逻辑。
    参数：request、db、current_user。
    返回：函数执行后的结果。
    """
    agent = build_agent(db, current_user)
    start = time.time()
    result = agent.chat(request.session_id, request.message)
    if isinstance(result, str):
        reply = result
        artifacts = []
    else:
        reply = result.get("reply", "")
        artifacts = result.get("artifacts") or []
    return ChatResponse(sessionId=request.session_id, reply=reply, artifacts=artifacts, durationMs=int((time.time() - start) * 1000))


# 定义函数 chat_stream，负责当前文件中的一个关键步骤或对外能力。
@router.post("/agent/chat/stream")
def chat_stream(request: ChatRequest, db: Session = Depends(get_db), current_user: UserInfo | None = Depends(get_login_user)):
    """
    作用：执行chat_stream对应的业务逻辑。
    参数：request、db、current_user。
    返回：函数执行后的结果。
    """
    agent = build_agent(db, current_user)

    def event_stream() -> Iterator[str]:
        """
        作用：执行event_stream对应的业务逻辑。
        参数：无。
        返回：函数执行后的结果。
        """
        try:
            for item in agent.chat_stream(request.session_id, request.message):
                if isinstance(item, str):
                    yield format_sse("token", item)
                    continue
                event = item.get("event", "token")
                data = item.get("data", "")
                yield format_sse(event, data)
        except AuthenticationError:
            yield format_sse("error", "模型鉴权失败，请检查 API Key 或网关配置")
        except (PermissionDeniedError, RateLimitError):
            yield format_sse("error", "模型服务当前不可用或额度已耗尽，请稍后重试")
        except APIError:
            yield format_sse("error", "模型服务调用失败，请稍后重试")
        except Exception:
            yield format_sse("error", "服务暂时不可用，请稍后重试")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# 定义函数 clear_session，负责清理旧状态，避免影响下一次执行。
@router.delete("/agent/session/{session_id}")
def clear_session(session_id: str, db: Session = Depends(get_db), current_user: UserInfo | None = Depends(get_login_user)):
    """
    作用：执行clear_session对应的业务逻辑。
    参数：session_id、db、current_user。
    返回：函数执行后的结果。
    """
    MemoryService(db).clear_session(session_id)
    return {"message": "会话记忆已清除", "sessionId": session_id}


# 定义函数 query_orders，负责按筛选条件查询业务数据。
@router.post("/test/tool/query-orders", response_class=PlainTextResponse)
def query_orders(request: QueryRequest, db: Session = Depends(get_db), current_user: UserInfo | None = Depends(get_login_user)):
    """
    作用：执行query_orders对应的业务逻辑。
    参数：request、db、current_user。
    返回：函数执行后的结果。
    """
    return build_sales_tools(db, current_user).query_orders(request.start_date, request.end_date, request.region_name, request.rep_name, request.limit)


# 定义函数 top_reps，负责当前文件中的一个关键步骤或对外能力。
@router.post("/test/tool/top-reps", response_class=PlainTextResponse)
def top_reps(request: RankRequest, db: Session = Depends(get_db), current_user: UserInfo | None = Depends(get_login_user)):
    """
    作用：执行top_reps对应的业务逻辑。
    参数：request、db、current_user。
    返回：函数执行后的结果。
    """
    return build_sales_tools(db, current_user).get_top_reps(request.start_date, request.end_date, request.region_name, request.top_n)


# 定义函数 region_ranking，负责当前文件中的一个关键步骤或对外能力。
@router.post("/test/tool/region-ranking", response_class=PlainTextResponse)
def region_ranking(request: RangeRequest, db: Session = Depends(get_db), current_user: UserInfo | None = Depends(get_login_user)):
    """
    作用：执行region_ranking对应的业务逻辑。
    参数：request、db、current_user。
    返回：函数执行后的结果。
    """
    return build_sales_tools(db, current_user).get_region_ranking(request.start_date, request.end_date)


# 定义函数 top_products，负责当前文件中的一个关键步骤或对外能力。
@router.post("/test/tool/top-products", response_class=PlainTextResponse)
def top_products(request: ProductRankRequest, db: Session = Depends(get_db), current_user: UserInfo | None = Depends(get_login_user)):
    """
    作用：执行top_products对应的业务逻辑。
    参数：request、db、current_user。
    返回：函数执行后的结果。
    """
    return build_sales_tools(db, current_user).get_top_products(request.start_date, request.end_date, request.top_n)


# 定义函数 month_over_month，负责当前文件中的一个关键步骤或对外能力。
@router.post("/test/tool/month-over-month", response_class=PlainTextResponse)
def month_over_month(request: MomRequest, db: Session = Depends(get_db), current_user: UserInfo | None = Depends(get_login_user)):
    """
    作用：执行month_over_month对应的业务逻辑。
    参数：request、db、current_user。
    返回：函数执行后的结果。
    """
    return build_sales_tools(db, current_user).calc_month_over_month(request.current_start, request.current_end, request.prev_start, request.prev_end, request.region_name)


# 定义函数 year_over_year，负责当前文件中的一个关键步骤或对外能力。
@router.post("/test/tool/year-over-year", response_class=PlainTextResponse)
def year_over_year(request: YoyRequest, db: Session = Depends(get_db), current_user: UserInfo | None = Depends(get_login_user)):
    """
    作用：执行year_over_year对应的业务逻辑。
    参数：request、db、current_user。
    返回：函数执行后的结果。
    """
    return build_sales_tools(db, current_user).calc_year_over_year(request.start_date, request.end_date, request.region_name)


# 定义函数 monthly_trend，负责当前文件中的一个关键步骤或对外能力。
@router.post("/test/tool/monthly-trend", response_class=PlainTextResponse)
def monthly_trend(request: TrendRequest, db: Session = Depends(get_db), current_user: UserInfo | None = Depends(get_login_user)):
    """
    作用：执行monthly_trend对应的业务逻辑。
    参数：request、db、current_user。
    返回：函数执行后的结果。
    """
    return build_sales_tools(db, current_user).get_monthly_trend(request.months, request.region_name)


# 定义函数 line_chart，负责当前文件中的一个关键步骤或对外能力。
@router.post("/test/tool/line-chart", response_model=ChartToolResponse)
def line_chart(request: LineChartRequest, db: Session = Depends(get_db), current_user: UserInfo | None = Depends(get_login_user)):
    """
    作用：执行line_chart对应的业务逻辑。
    参数：request、db、current_user。
    返回：函数执行后的结果。
    """
    return build_sales_tools(db, current_user).generate_line_chart(request.months, request.region_name, request.title)


# 定义函数 bar_chart，负责当前文件中的一个关键步骤或对外能力。
@router.post("/test/tool/bar-chart", response_model=ChartToolResponse)
def bar_chart(request: BarPieChartRequest, db: Session = Depends(get_db), current_user: UserInfo | None = Depends(get_login_user)):
    """
    作用：执行bar_chart对应的业务逻辑。
    参数：request、db、current_user。
    返回：函数执行后的结果。
    """
    return build_sales_tools(db, current_user).generate_bar_chart(request.dimension, request.start_date, request.end_date, request.title, request.top_n)


# 定义函数 pie_chart，负责当前文件中的一个关键步骤或对外能力。
@router.post("/test/tool/pie-chart", response_model=ChartToolResponse)
def pie_chart(request: BarPieChartRequest, db: Session = Depends(get_db), current_user: UserInfo | None = Depends(get_login_user)):
    """
    作用：执行pie_chart对应的业务逻辑。
    参数：request、db、current_user。
    返回：函数执行后的结果。
    """
    return build_sales_tools(db, current_user).generate_pie_chart(request.dimension, request.start_date, request.end_date, request.title, request.top_n)


# 定义函数 detect_anomalies，负责识别异常、问题或某类特征。
@router.post("/test/tool/detect-anomalies", response_class=PlainTextResponse)
def detect_anomalies(db: Session = Depends(get_db), current_user: UserInfo | None = Depends(get_login_user)):
    """
    作用：执行detect_anomalies对应的业务逻辑。
    参数：db、current_user。
    返回：函数执行后的结果。
    """
    return build_sales_tools(db, current_user).detect_all_anomalies()
