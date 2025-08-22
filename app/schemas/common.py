"""
通用Pydantic模型
"""

from typing import Optional
from pydantic import BaseModel


class Message(BaseModel):
    """通用消息模型"""

    message: str


class Token(BaseModel):
    """JWT令牌模型"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """令牌数据模型"""

    username: Optional[str] = None
    scopes: list[str] = []


class PaginationParams(BaseModel):
    """分页参数模型"""

    page: int = 1
    page_size: int = 20

    class Config:
        validate_assignment = True

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class PaginatedResponse(BaseModel):
    """分页响应模型"""

    items: list
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(cls, items: list, total: int, page: int, page_size: int):
        """创建分页响应"""
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
