"""
用户服务层
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password, create_token_pair
from app.core.exceptions import (
    AuthenticationException,
    ValidationException,
    ConflictException,
    ResourceNotFoundException,
)
from app.db.repositories.user_repository import user_repository
from app.schemas.user import UserCreate, UserUpdate, UserRegister, UserLogin
from app.schemas.common import Token


class UserService:
    """用户服务"""

    def __init__(self):
        self.user_repo = user_repository

    async def register(self, db: AsyncSession, *, user_in: UserRegister) -> dict:
        """用户注册"""
        # 检查用户名是否已存在
        existing_user = await self.user_repo.get_by_username(
            db, username=user_in.username
        )
        if existing_user:
            raise ConflictException("用户名已存在")

        # 检查邮箱是否已存在
        existing_email = await self.user_repo.get_by_email(db, email=user_in.email)
        if existing_email:
            raise ConflictException("邮箱已存在")

        # 创建用户
        hashed_password = get_password_hash(user_in.password)
        user_create = UserCreate(
            username=user_in.username,
            email=user_in.email,
            full_name=user_in.full_name,
            password=user_in.password,
            is_superuser=False,
        )

        user = await self.user_repo.create_with_password(
            db, obj_in=user_create, hashed_password=hashed_password
        )

        # 生成令牌
        token = create_token_pair(user.username)

        return {"user": user, "token": token}

    async def login(self, db: AsyncSession, *, user_in: UserLogin) -> Token:
        """用户登录"""
        user = await self.user_repo.authenticate(
            db, username=user_in.username, password=user_in.password
        )

        if not user:
            raise AuthenticationException("用户名或密码错误")

        if not await self.user_repo.is_active(user):
            raise AuthenticationException("用户账号已被禁用")

        # 生成令牌
        token = create_token_pair(user.username)

        return token

    async def get_current_user(self, db: AsyncSession, *, username: str):
        """获取当前用户"""
        user = await self.user_repo.get_by_username(db, username=username)
        if not user:
            raise ResourceNotFoundException("用户不存在")
        return user

    async def update_user(self, db: AsyncSession, *, current_user, user_in: UserUpdate):
        """更新用户信息"""
        # 如果要更新密码，需要哈希处理
        update_data = user_in.dict(exclude_unset=True)

        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(
                update_data.pop("password")
            )

        user = await self.user_repo.update(db, db_obj=current_user, obj_in=update_data)
        return user

    async def get_user_by_id(self, db: AsyncSession, *, user_id: int):
        """根据ID获取用户"""
        user = await self.user_repo.get(db, id=user_id)
        if not user:
            raise ResourceNotFoundException("用户不存在")
        return user

    async def get_users(self, db: AsyncSession, *, skip: int = 0, limit: int = 100):
        """获取用户列表"""
        users = await self.user_repo.get_multi(db, skip=skip, limit=limit)
        return users

    async def delete_user(self, db: AsyncSession, *, user_id: int):
        """删除用户"""
        user = await self.user_repo.get(db, id=user_id)
        if not user:
            raise ResourceNotFoundException("用户不存在")

        await self.user_repo.delete(db, id=user_id)
        return {"message": "用户删除成功"}


# 创建全局服务实例
user_service = UserService()
