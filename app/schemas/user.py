"""
用户相关的Pydantic模型
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


class UserBase(BaseModel):
    """用户基础模型"""

    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    """用户创建模型"""

    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("密码长度至少为8位")
        return v


class UserUpdate(BaseModel):
    """用户更新模型"""

    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError("密码长度至少为8位")
        return v


class UserInDBBase(UserBase):
    """用户数据库基础模型"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class User(UserInDBBase):
    """用户响应模型"""

    pass


class UserInDB(UserInDBBase):
    """数据库中的用户模型"""

    hashed_password: str


class UserLogin(BaseModel):
    """用户登录模型"""

    username: str
    password: str


class UserRegister(BaseModel):
    """用户注册模型"""

    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("密码长度至少为8位")
        return v
