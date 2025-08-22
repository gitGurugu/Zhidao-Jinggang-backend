"""
物品仓库类
"""

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.item import Item
from app.db.repositories.base_repository import BaseRepository
from app.schemas.item import ItemCreate, ItemUpdate


class ItemRepository(BaseRepository[Item, ItemCreate, ItemUpdate]):
    """物品仓库"""

    def __init__(self):
        super().__init__(Item)

    async def get_by_owner(
        self, db: AsyncSession, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[Item]:
        """根据所有者获取物品列表"""
        result = await db.execute(
            select(Item).where(Item.owner_id == owner_id).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_active_items(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[Item]:
        """获取活跃的物品列表"""
        result = await db.execute(
            select(Item).where(Item.is_active == True).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create_with_owner(
        self, db: AsyncSession, *, obj_in: ItemCreate, owner_id: int
    ) -> Item:
        """创建物品（指定所有者）"""
        db_obj = Item(
            title=obj_in.title,
            description=obj_in.description,
            owner_id=owner_id,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


# 创建全局仓库实例
item_repository = ItemRepository()
