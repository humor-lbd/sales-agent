"""
日志管理模块

该模块负责初始化日志系统，并记录每次HTTP请求的耗时和结果状态。
主要功能包括：
- 配置日志格式和级别
- 注册HTTP请求日志中间件
- 记录请求处理时间和状态码
- 与运行时指标系统集成
"""

from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request

from app.core.metrics import runtime_metrics


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_logging() -> None:
    """
    配置日志系统
    
    初始化日志系统，设置日志级别为INFO，使用预定义的日志格式。
    """
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


def register_request_logging(app: FastAPI) -> None:
    """
    注册HTTP请求日志中间件
    
    为FastAPI应用注册HTTP请求日志中间件，记录每个请求的处理时间和状态码。
    
    Args:
        app: FastAPI应用实例
    """
    logger = logging.getLogger("sales-agent.http")

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """
        HTTP请求日志中间件
        
        记录每个HTTP请求的处理时间和状态码，并将请求信息添加到运行时指标中。
        
        Args:
            request: HTTP请求对象
            call_next: 下一个中间件或路由处理函数
        
        Returns:
            响应对象
        """
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            # 记录异常请求
            duration_ms = int((time.perf_counter() - start) * 1000)
            runtime_metrics.record_request(request.method, request.url.path, 500, duration_ms)
            logger.exception("%s %s -> 500 (%sms)", request.method, request.url.path, duration_ms)
            raise

        # 记录正常请求
        duration_ms = int((time.perf_counter() - start) * 1000)
        runtime_metrics.record_request(request.method, request.url.path, response.status_code, duration_ms)
        logger.info("%s %s -> %s (%sms)", request.method, request.url.path, response.status_code, duration_ms)
        return response
