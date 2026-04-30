"""
异常处理模块

该模块负责统一注册异常处理器，保证接口报错时返回稳定的结构化响应。
主要处理以下异常：
- ValueError：参数错误
- AuthenticationError：模型鉴权错误
- PermissionDeniedError：模型权限错误
- RateLimitError：模型速率限制错误
- APIError：模型API错误
- Exception：通用异常
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from openai import APIError, AuthenticationError, PermissionDeniedError, RateLimitError


def register_exception_handlers(app: FastAPI) -> None:
    """
    注册项目统一异常处理器
    
    为FastAPI应用注册各种异常处理器，确保所有异常都能返回统一格式的JSON响应。
    
    Args:
        app: FastAPI应用实例
    """
    @app.exception_handler(ValueError)
    async def handle_value_error(request: Request, exc: ValueError) -> JSONResponse:
        """
        处理值错误异常
        
        Args:
            request: 请求对象
            exc: 异常对象
        
        Returns:
            JSONResponse: 包含错误信息的JSON响应
        """
        return JSONResponse(status_code=400, content={"error": str(exc)})

    @app.exception_handler(AuthenticationError)
    async def handle_auth_error(request: Request, exc: AuthenticationError) -> JSONResponse:
        """
        处理认证错误异常
        
        Args:
            request: 请求对象
            exc: 异常对象
        
        Returns:
            JSONResponse: 包含错误信息的JSON响应
        """
        return JSONResponse(status_code=502, content={"error": "模型鉴权失败，请检查 API Key 或网关配置"})

    @app.exception_handler(PermissionDeniedError)
    async def handle_permission_error(request: Request, exc: PermissionDeniedError) -> JSONResponse:
        """
        处理权限错误异常
        
        Args:
            request: 请求对象
            exc: 异常对象
        
        Returns:
            JSONResponse: 包含错误信息的JSON响应
        """
        return JSONResponse(status_code=503, content={"error": "模型服务当前不可用或额度已耗尽，请检查模型平台配额"})

    @app.exception_handler(RateLimitError)
    async def handle_rate_limit_error(request: Request, exc: RateLimitError) -> JSONResponse:
        """
        处理速率限制错误异常
        
        Args:
            request: 请求对象
            exc: 异常对象
        
        Returns:
            JSONResponse: 包含错误信息的JSON响应
        """
        return JSONResponse(status_code=503, content={"error": "模型请求过于频繁或配额受限，请稍后重试"})

    @app.exception_handler(APIError)
    async def handle_openai_error(request: Request, exc: APIError) -> JSONResponse:
        """
        处理OpenAI API错误异常
        
        Args:
            request: 请求对象
            exc: 异常对象
        
        Returns:
            JSONResponse: 包含错误信息的JSON响应
        """
        return JSONResponse(status_code=502, content={"error": "模型服务调用失败，请稍后重试"})

    @app.exception_handler(Exception)
    async def handle_general_error(request: Request, exc: Exception) -> JSONResponse:
        """
        处理通用异常
        
        Args:
            request: 请求对象
            exc: 异常对象
        
        Returns:
            JSONResponse: 包含错误信息的JSON响应
        """
        return JSONResponse(status_code=500, content={"error": "服务器内部错误，请稍后重试"})
