"""
物品相关的Pydantic模型
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ItemBase(BaseModel):
    """物品基础模型"""

    title: str
    description: Optional[str] = None
    is_active: bool = True


class ItemCreate(ItemBase):
    """物品创建模型"""

    pass


class ItemUpdate(BaseModel):
    """物品更新模型"""

    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ItemInDBBase(ItemBase):
    """物品数据库基础模型"""

    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class Item(ItemInDBBase):
    """物品响应模型"""

    pass


class ItemInDB(ItemInDBBase):
    """数据库中的物品模型"""

    pass
