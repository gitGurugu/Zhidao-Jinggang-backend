"""
通用依赖项
"""

from typing import Optional

from fastapi import Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_token
from app.core.exceptions import AuthenticationException, AuthorizationException
from app.db.session import get_db
from app.db.models.user import User
from app.db.repositories.user_repository import user_repository


security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    db: AsyncSession = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[User]:
    """获取当前用户（可选）"""
    if not credentials:
        return None

    token = credentials.credentials
    username = verify_token(token)

    if not username:
        return None

    user = await user_repository.get_by_username(db, username=username)
    return user


async def get_current_user_required(
    db: AsyncSession = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> User:
    """获取当前用户（必需）"""
    if not credentials:
        raise AuthenticationException("需要认证令牌")

    token = credentials.credentials
    username = verify_token(token)

    if not username:
        raise AuthenticationException("无效的认证令牌")

    user = await user_repository.get_by_username(db, username=username)
    if not user:
        raise AuthenticationException("用户不存在")

    if not user.is_active:
        raise AuthenticationException("用户账号已被禁用")

    return user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user_required),
) -> User:
    """获取当前活跃超级用户"""
    if not current_user.is_superuser:
        raise AuthorizationException("需要超级用户权限")
    return current_user


class PaginationParams:
    """分页参数依赖"""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    ):
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class SortParams:
    """排序参数依赖"""

    def __init__(
        self,
        sort_by: Optional[str] = Query(None, description="排序字段"),
        sort_order: str = Query("asc", regex="^(asc|desc)$", description="排序方向"),
    ):
        self.sort_by = sort_by
        self.sort_order = sort_order


class FilterParams:
    """过滤参数依赖"""

    def __init__(
        self,
        search: Optional[str] = Query(None, description="搜索关键词"),
        is_active: Optional[bool] = Query(None, description="是否激活"),
        created_after: Optional[str] = Query(None, description="创建时间（之后）"),
        created_before: Optional[str] = Query(None, description="创建时间（之前）"),
    ):
        self.search = search
        self.is_active = is_active
        self.created_after = created_after
        self.created_before = created_before


def get_request_id(request: Request) -> str:
    """获取请求ID"""
    return getattr(request.state, "request_id", "unknown")


def check_api_key(api_key: Optional[str] = Query(None, alias="api_key")) -> bool:
    """检查API密钥"""
    if not api_key:
        return False
    # 这里可以实现API密钥验证逻辑
    return api_key == settings.API_KEY if hasattr(settings, "API_KEY") else False


async def rate_limit_check(request: Request) -> None:
    """速率限制检查"""
    # 这里可以实现更复杂的速率限制逻辑
    # 比如基于Redis的计数器
    pass
