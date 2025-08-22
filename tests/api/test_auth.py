"""
认证API测试
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, user_data: dict):
    """测试用户注册"""
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "注册成功"
    assert "user" in data
    assert "token" in data
    assert data["user"]["username"] == user_data["username"]
    assert data["user"]["email"] == user_data["email"]


@pytest.mark.asyncio
async def test_register_duplicate_user(client: AsyncClient, user_data: dict):
    """测试重复用户注册"""
    # 首次注册
    await client.post("/api/v1/auth/register", json=user_data)

    # 重复注册
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 409  # Conflict


@pytest.mark.asyncio
async def test_login_user(client: AsyncClient, user_data: dict):
    """测试用户登录"""
    # 先注册用户
    await client.post("/api/v1/auth/register", json=user_data)

    # 登录
    login_data = {"username": user_data["username"], "password": user_data["password"]}
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient, user_data: dict):
    """测试无效凭证登录"""
    # 先注册用户
    await client.post("/api/v1/auth/register", json=user_data)

    # 使用错误密码登录
    login_data = {"username": user_data["username"], "password": "wrongpassword"}
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, user_data: dict):
    """测试获取当前用户信息"""
    # 注册并登录
    await client.post("/api/v1/auth/register", json=user_data)

    login_data = {"username": user_data["username"], "password": user_data["password"]}
    login_response = await client.post("/api/v1/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    # 获取当前用户信息
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]


@pytest.mark.asyncio
async def test_get_current_user_without_token(client: AsyncClient):
    """测试无令牌获取当前用户信息"""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401  # Unauthorized
