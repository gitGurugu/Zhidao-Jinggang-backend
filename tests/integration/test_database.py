"""
数据库集成测试
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.models.item import Item
from app.db.repositories.user_repository import user_repository
from app.db.repositories.item_repository import item_repository
from app.core.security import get_password_hash


@pytest.mark.asyncio
class TestUserRepository:
    """用户仓库测试"""

    async def test_create_user(self, db_session: AsyncSession):
        """测试创建用户"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": get_password_hash("testpass123"),
            "full_name": "Test User",
            "is_active": True,
        }

        user = User(**user_data)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True

    async def test_get_user_by_email(self, db_session: AsyncSession):
        """测试根据邮箱获取用户"""
        # 创建用户
        user = User(
            username="emailtest",
            email="email@test.com",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        # 根据邮箱查找用户
        found_user = await user_repository.get_by_email(
            db_session, email="email@test.com"
        )
        assert found_user is not None
        assert found_user.email == "email@test.com"
        assert found_user.username == "emailtest"

    async def test_get_user_by_username(self, db_session: AsyncSession):
        """测试根据用户名获取用户"""
        # 创建用户
        user = User(
            username="usernametest",
            email="username@test.com",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        # 根据用户名查找用户
        found_user = await user_repository.get_by_username(
            db_session, username="usernametest"
        )
        assert found_user is not None
        assert found_user.username == "usernametest"
        assert found_user.email == "username@test.com"

    async def test_authenticate_user(self, db_session: AsyncSession):
        """测试用户认证"""
        # 创建用户
        password = "authtest123"
        user = User(
            username="authtest",
            email="auth@test.com",
            hashed_password=get_password_hash(password),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        # 正确认证
        authenticated_user = await user_repository.authenticate(
            db_session, username="authtest", password=password
        )
        assert authenticated_user is not None
        assert authenticated_user.username == "authtest"

        # 错误密码
        failed_auth = await user_repository.authenticate(
            db_session, username="authtest", password="wrongpassword"
        )
        assert failed_auth is None


@pytest.mark.asyncio
class TestItemRepository:
    """物品仓库测试"""

    async def test_create_item(self, db_session: AsyncSession):
        """测试创建物品"""
        # 先创建用户
        user = User(
            username="itemowner",
            email="owner@test.com",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 创建物品
        item = Item(
            title="Test Item",
            description="This is a test item",
            owner_id=user.id,
            is_active=True,
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        assert item.id is not None
        assert item.title == "Test Item"
        assert item.owner_id == user.id
        assert item.is_active is True

    async def test_get_items_by_owner(self, db_session: AsyncSession):
        """测试根据所有者获取物品"""
        # 创建用户
        user = User(
            username="multiowner",
            email="multi@test.com",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 创建多个物品
        items = [
            Item(title="Item 1", owner_id=user.id, is_active=True),
            Item(title="Item 2", owner_id=user.id, is_active=True),
            Item(title="Item 3", owner_id=user.id, is_active=False),
        ]

        for item in items:
            db_session.add(item)
        await db_session.commit()

        # 获取用户的所有物品
        user_items = await item_repository.get_by_owner(
            db_session, owner_id=user.id, skip=0, limit=10
        )

        assert len(user_items) == 3
        assert all(item.owner_id == user.id for item in user_items)

    async def test_get_active_items(self, db_session: AsyncSession):
        """测试获取活跃物品"""
        # 创建用户
        user = User(
            username="activeowner",
            email="active@test.com",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 创建物品（部分活跃，部分不活跃）
        items = [
            Item(title="Active Item 1", owner_id=user.id, is_active=True),
            Item(title="Active Item 2", owner_id=user.id, is_active=True),
            Item(title="Inactive Item", owner_id=user.id, is_active=False),
        ]

        for item in items:
            db_session.add(item)
        await db_session.commit()

        # 获取活跃物品
        active_items = await item_repository.get_active_items(
            db_session, skip=0, limit=10
        )

        # 应该只返回活跃的物品
        assert len(active_items) >= 2  # 至少包含我们创建的2个活跃物品
        assert all(item.is_active for item in active_items)


@pytest.mark.asyncio
class TestRelationships:
    """关系测试"""

    async def test_user_items_relationship(self, db_session: AsyncSession):
        """测试用户-物品关系"""
        # 创建用户
        user = User(
            username="relationtest",
            email="relation@test.com",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 创建物品
        item1 = Item(title="Relation Item 1", owner_id=user.id)
        item2 = Item(title="Relation Item 2", owner_id=user.id)

        db_session.add(item1)
        db_session.add(item2)
        await db_session.commit()

        # 刷新用户以加载关系
        await db_session.refresh(user)

        # 检查关系
        user_with_items = await user_repository.get(db_session, id=user.id)
        assert user_with_items is not None

        # 通过仓库获取用户的物品
        user_items = await item_repository.get_by_owner(
            db_session, owner_id=user.id, skip=0, limit=10
        )
        assert len(user_items) == 2
        assert all(item.owner_id == user.id for item in user_items)
