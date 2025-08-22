"""
物品服务层
"""

from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundException, AuthorizationException
from app.db.repositories.item_repository import item_repository
from app.schemas.item import ItemCreate, ItemUpdate


class ItemService:
    """物品服务"""

    def __init__(self):
        self.item_repo = item_repository

    async def create_item(
        self, db: AsyncSession, *, item_in: ItemCreate, owner_id: int
    ):
        """创建物品"""
        item = await self.item_repo.create_with_owner(
            db, obj_in=item_in, owner_id=owner_id
        )
        return item

    async def get_item(self, db: AsyncSession, *, item_id: int):
        """获取物品"""
        item = await self.item_repo.get(db, id=item_id)
        if not item:
            raise ResourceNotFoundException("物品不存在")
        return item

    async def get_items(self, db: AsyncSession, *, skip: int = 0, limit: int = 100):
        """获取物品列表"""
        items = await self.item_repo.get_multi(db, skip=skip, limit=limit)
        return items

    async def get_active_items(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ):
        """获取活跃物品列表"""
        items = await self.item_repo.get_active_items(db, skip=skip, limit=limit)
        return items

    async def get_user_items(
        self, db: AsyncSession, *, owner_id: int, skip: int = 0, limit: int = 100
    ):
        """获取用户的物品列表"""
        items = await self.item_repo.get_by_owner(
            db, owner_id=owner_id, skip=skip, limit=limit
        )
        return items

    async def update_item(
        self,
        db: AsyncSession,
        *,
        item_id: int,
        item_in: ItemUpdate,
        current_user_id: int,
    ):
        """更新物品"""
        item = await self.item_repo.get(db, id=item_id)
        if not item:
            raise ResourceNotFoundException("物品不存在")

        # 检查权限：只有所有者可以更新
        if item.owner_id != current_user_id:
            raise AuthorizationException("您没有权限更新此物品")

        updated_item = await self.item_repo.update(db, db_obj=item, obj_in=item_in)
        return updated_item

    async def delete_item(
        self, db: AsyncSession, *, item_id: int, current_user_id: int
    ):
        """删除物品"""
        item = await self.item_repo.get(db, id=item_id)
        if not item:
            raise ResourceNotFoundException("物品不存在")

        # 检查权限：只有所有者可以删除
        if item.owner_id != current_user_id:
            raise AuthorizationException("您没有权限删除此物品")

        await self.item_repo.delete(db, id=item_id)
        return {"message": "物品删除成功"}


# 创建全局服务实例
item_service = ItemService()
