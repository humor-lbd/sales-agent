"""
安全认证模块

该模块负责处理登录鉴权、JWT令牌生成和验证、以及当前用户信息解析。
主要功能包括：
- 创建JWT访问令牌
- 解码和验证JWT令牌
- 从请求头获取当前用户信息
- 构建用户信息对象
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.repositories import SalesRepRepository
from app.logic.schemas import UserInfo


ALGORITHM = "HS256"


def create_access_token(user: UserInfo, settings: Settings) -> str:
    """
    创建JWT访问令牌
    
    Args:
        user: 用户信息对象
        settings: 应用配置对象
    
    Returns:
        str: 生成的JWT访问令牌
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": str(user.user_id),
        "username": user.username,
        "role": user.role,
        "region_id": user.region_id,
        "rep_id": user.rep_id,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str, settings: Settings) -> UserInfo:
    """
    解码和验证JWT访问令牌
    
    Args:
        token: JWT令牌字符串
        settings: 应用配置对象
    
    Returns:
        UserInfo: 解码后的用户信息对象
    
    Raises:
        HTTPException: 当令牌无效或已过期时
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token 无效或已过期") from exc
    return UserInfo(
        user_id=int(payload["sub"]),
        username=payload.get("username", ""),
        role=payload.get("role", ""),
        region_id=payload.get("region_id"),
        rep_id=payload.get("rep_id"),
    )

def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
    settings: Settings = Depends(get_settings),
) -> UserInfo | None:
    """
    从请求头获取当前用户信息
    
    Args:
        authorization: 请求头中的Authorization字段
        settings: 应用配置对象
    
    Returns:
        UserInfo | None: 当前用户信息对象或None（如果认证未启用）
    
    Raises:
        HTTPException: 当认证启用但未提供有效的Authorization头时
    """
    if not settings.auth_enabled:
        return None
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录或登录已过期，请重新登录")
    token = authorization.removeprefix("Bearer ").strip()
    return decode_access_token(token, settings)

def get_login_user(
    user: UserInfo | None = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> UserInfo | None:
    """
    获取登录用户信息
    
    Args:
        user: 当前用户信息（由get_current_user依赖注入）
        settings: 应用配置对象
    
    Returns:
        UserInfo | None: 登录用户信息对象或None（如果认证未启用）
    
    Raises:
        HTTPException: 当认证启用但用户未登录时
    """
    if settings.auth_enabled and user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录或登录已过期，请重新登录")
    return user

def build_user_from_rep(rep_id: int, db: Session) -> UserInfo:
    """
    根据销售代表ID构建用户信息
    
    Args:
        rep_id: 销售代表ID
        db: 数据库会话对象
    
    Returns:
        UserInfo: 构建的用户信息对象
    
    Raises:
        HTTPException: 当销售代表不存在时
    """
    rep = SalesRepRepository(db).find_by_id(rep_id)
    if rep is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户不存在")
    return UserInfo(
        user_id=rep.id,
        username=rep.name,
        role=rep.role,
        region_id=rep.region_id,
        rep_id=rep.id,
    )
