"""
物品数据模型
"""

from typing import Optional

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Item(Base):
    """物品模型"""

    # 基本信息
    title: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # 所有者
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=False
    )
    owner = relationship("User", back_populates="items")

    def __repr__(self) -> str:
        return f"<Item(title='{self.title}', owner_id={self.owner_id})>"
