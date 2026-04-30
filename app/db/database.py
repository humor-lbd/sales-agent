"""
文件作用：
- 创建数据库引擎与会话工厂，并向 FastAPI 提供数据库依赖。
- 阅读这个文件时，建议先看文件头说明，再顺着主要函数或类往下追踪。
"""

from collections.abc import Generator
import time

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.metrics import runtime_metrics


settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


# 定义函数 before_cursor_execute，负责当前文件中的一个关键步骤或对外能力。
@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """
    作用：执行before_cursor_execute对应的业务逻辑。
    参数：conn、cursor、statement、parameters、context、executemany。
    返回：函数执行后的结果。
    """
    conn.info.setdefault("query_start_time", []).append(time.perf_counter())


# 定义函数 after_cursor_execute，负责当前文件中的一个关键步骤或对外能力。
@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """
    作用：执行after_cursor_execute对应的业务逻辑。
    参数：conn、cursor、statement、parameters、context、executemany。
    返回：函数执行后的结果。
    """
    started = conn.info.get("query_start_time", []).pop(-1)
    runtime_metrics.record_db_query((time.perf_counter() - started) * 1000)


# 定义函数 get_db，负责读取或返回当前上下文需要的数据。
def get_db() -> Generator[Session, None, None]:
    """
    作用：获取db相关数据。
    参数：无。
    返回：函数执行后的结果。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
