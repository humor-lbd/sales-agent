"""
文件作用：
- 作为 FastAPI 服务入口，负责组装应用、初始化数据库并注册全局能力。
- 阅读这个文件时，建议先看文件头说明，再顺着主要函数或类往下追踪。
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, register_request_logging
from app.db.bootstrap import initialize_database


settings = get_settings()
configure_logging()
startup_logger = logging.getLogger("sales-agent.startup")


# 定义函数 lifespan，负责当前文件中的一个关键步骤或对外能力。
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    作用：执行lifespan对应的业务逻辑。
    参数：app。
    返回：函数执行后的结果。
    """
    if not settings.db_bootstrap_enabled:
        startup_logger.info("数据库初始化已关闭，跳过启动引导")
    else:
        try:
            report = initialize_database(settings)
            startup_logger.info(
                "数据库初始化完成: db=%s, schema=%s, seed=%s, skipped=%s",
                report.database_name,
                report.schema_applied,
                report.seed_applied,
                report.skipped_seed_reason,
            )
        except Exception:
            startup_logger.exception("数据库初始化失败")
            if settings.db_bootstrap_fail_fast:
                raise
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
register_exception_handlers(app)
register_request_logging(app)
app.include_router(router)
