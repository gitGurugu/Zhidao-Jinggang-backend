"""
数据库初始化脚本
"""

import asyncio
from loguru import logger

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.db.base import Base
from app.db.models.user import User
from app.db.repositories.user_repository import user_repository


async def init_db() -> None:
    """初始化数据库"""
    logger.info("开始初始化数据库...")

    async with AsyncSessionLocal() as session:
        # 检查是否已存在超级用户
        superuser = await user_repository.get_by_email(
            session, email=settings.FIRST_SUPERUSER_EMAIL
        )

        if not superuser:
            logger.info("创建初始超级用户...")

            # 创建超级用户
            hashed_password = get_password_hash(settings.FIRST_SUPERUSER_PASSWORD)
            superuser_obj = User(
                username="admin",
                email=settings.FIRST_SUPERUSER_EMAIL,
                hashed_password=hashed_password,
                full_name="系统管理员",
                is_superuser=True,
                is_active=True,
                is_verified=True,
            )

            session.add(superuser_obj)
            await session.commit()

            logger.info(f"超级用户创建成功: {settings.FIRST_SUPERUSER_EMAIL}")
        else:
            logger.info("超级用户已存在，跳过创建")

    logger.info("数据库初始化完成")


async def create_sample_data() -> None:
    """创建示例数据"""
    logger.info("开始创建示例数据...")

    async with AsyncSessionLocal() as session:
        # 检查是否已有示例数据
        existing_users = await user_repository.get_multi(session, skip=0, limit=10)

        if len(existing_users) <= 1:  # 只有超级用户
            logger.info("创建示例用户...")

            # 创建示例用户
            sample_users = [
                {
                    "username": "testuser1",
                    "email": "test1@example.com",
                    "password": "testpass123",
                    "full_name": "测试用户1",
                },
                {
                    "username": "testuser2",
                    "email": "test2@example.com",
                    "password": "testpass123",
                    "full_name": "测试用户2",
                },
            ]

            for user_data in sample_users:
                hashed_password = get_password_hash(user_data["password"])
                user_obj = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    hashed_password=hashed_password,
                    full_name=user_data["full_name"],
                    is_active=True,
                )

                session.add(user_obj)

            await session.commit()
            logger.info("示例用户创建成功")
        else:
            logger.info("示例数据已存在，跳过创建")

    logger.info("示例数据创建完成")


if __name__ == "__main__":
    asyncio.run(init_db())
    asyncio.run(create_sample_data())
