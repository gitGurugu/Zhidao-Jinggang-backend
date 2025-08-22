"""
物品相关API端点
"""

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_pagination_params
from app.db.session import get_db
from app.schemas.item import Item, ItemCreate, ItemUpdate
from app.schemas.user import User
from app.schemas.common import Message
from app.services.item_service import item_service

router = APIRouter()


@router.get("/", response_model=List[Item], summary="获取物品列表")
async def get_items(
    db: AsyncSession = Depends(get_db),
    pagination: dict = Depends(get_pagination_params),
    active_only: bool = Query(False, description="仅显示活跃物品"),
):
    """
    获取物品列表

    - **page**: 页码（默认1）
    - **page_size**: 每页数量（默认20）
    - **active_only**: 仅显示活跃物品
    """
    if active_only:
        items = await item_service.get_active_items(
            db, skip=pagination["skip"], limit=pagination["limit"]
        )
    else:
        items = await item_service.get_items(
            db, skip=pagination["skip"], limit=pagination["limit"]
        )
    return items


@router.post("/", response_model=Item, summary="创建物品")
async def create_item(
    item_in: ItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    创建新物品

    - **title**: 物品标题（必填）
    - **description**: 物品描述（可选）
    - **is_active**: 是否激活（默认True）
    """
    item = await item_service.create_item(db, item_in=item_in, owner_id=current_user.id)
    return item


@router.get("/my", response_model=List[Item], summary="获取我的物品")
async def get_my_items(
    db: AsyncSession = Depends(get_db),
    pagination: dict = Depends(get_pagination_params),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取当前用户的物品列表
    """
    items = await item_service.get_user_items(
        db, owner_id=current_user.id, skip=pagination["skip"], limit=pagination["limit"]
    )
    return items


@router.get("/{item_id}", response_model=Item, summary="获取物品详情")
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    """
    根据ID获取物品详情
    """
    item = await item_service.get_item(db, item_id=item_id)
    return item


@router.put("/{item_id}", response_model=Item, summary="更新物品")
async def update_item(
    item_id: int,
    item_in: ItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    更新物品信息（仅所有者可更新）
    """
    item = await item_service.update_item(
        db, item_id=item_id, item_in=item_in, current_user_id=current_user.id
    )
    return item


@router.delete("/{item_id}", response_model=Message, summary="删除物品")
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    删除物品（仅所有者可删除）
    """
    result = await item_service.delete_item(
        db, item_id=item_id, current_user_id=current_user.id
    )
    return result
