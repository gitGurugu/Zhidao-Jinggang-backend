"""
API依赖项
"""

from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_token
from app.core.exceptions import AuthenticationException
from app.db.session import get_db
from app.db.repositories.user_repository import user_repository
from app.db.models.user import User


security = HTTPBearer()


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """获取当前用户"""
    token = credentials.credentials
    username = verify_token(token)

    if username is None:
        raise AuthenticationException("无效的认证令牌")

    user = await user_repository.get_by_username(db, username=username)
    if user is None:
        raise AuthenticationException("用户不存在")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise AuthenticationException("用户账号已被禁用")
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前超级用户"""
    if not current_user.is_superuser:
        raise AuthenticationException("权限不足")
    return current_user


def get_pagination_params(page: int = 1, page_size: int = 20) -> dict:
    """获取分页参数"""
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > settings.MAX_PAGE_SIZE:
        page_size = settings.MAX_PAGE_SIZE

    return {
        "skip": (page - 1) * page_size,
        "limit": page_size,
        "page": page,
        "page_size": page_size,
    }
