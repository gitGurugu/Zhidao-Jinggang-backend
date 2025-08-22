"""
用户相关API端点
"""

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_active_user,
    get_current_superuser,
    get_pagination_params,
)
from app.db.session import get_db
from app.schemas.user import User, UserUpdate
from app.schemas.common import Message
from app.services.user_service import user_service

router = APIRouter()


@router.get("/", response_model=List[User], summary="获取用户列表")
async def get_users(
    db: AsyncSession = Depends(get_db),
    pagination: dict = Depends(get_pagination_params),
    current_user: User = Depends(get_current_superuser),
):
    """
    获取用户列表（仅超级用户可访问）
    """
    users = await user_service.get_users(
        db, skip=pagination["skip"], limit=pagination["limit"]
    )
    return users


@router.get("/me", response_model=User, summary="获取当前用户信息")
async def get_current_user(current_user: User = Depends(get_current_active_user)):
    """
    获取当前登录用户的信息
    """
    return current_user


@router.put("/me", response_model=User, summary="更新当前用户信息")
async def update_current_user(
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    更新当前登录用户的信息
    """
    updated_user = await user_service.update_user(
        db, current_user=current_user, user_in=user_in
    )
    return updated_user


@router.get("/{user_id}", response_model=User, summary="根据ID获取用户")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    根据用户ID获取用户信息
    """
    user = await user_service.get_user_by_id(db, user_id=user_id)
    return user


@router.delete("/{user_id}", response_model=Message, summary="删除用户")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """
    删除用户（仅超级用户可访问）
    """
    result = await user_service.delete_user(db, user_id=user_id)
    return result
