"""
Redis客户端管理模块

该模块负责集中创建和缓存Redis客户端，方便业务层做缓存复用。
使用lru_cache装饰器确保Redis客户端只被创建一次，提高性能。
"""

from __future__ import annotations

from functools import lru_cache

from redis import Redis

from app.core.config import get_settings


@lru_cache
def get_redis_client() -> Redis | None:
    """
    获取Redis客户端实例
    
    从配置中读取Redis连接信息，创建并返回Redis客户端实例。
    如果Redis未启用，则返回None。
    
    Returns:
        Redis | None: Redis客户端实例或None
    """
    settings = get_settings()
    if not settings.redis_enabled:
        return None
    return Redis.from_url(settings.redis_url, decode_responses=True)

