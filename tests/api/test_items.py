"""
物品API测试
"""

import pytest
from httpx import AsyncClient


async def get_auth_headers(client: AsyncClient, user_data: dict):
    """获取认证头"""
    await client.post("/api/v1/auth/register", json=user_data)

    login_data = {"username": user_data["username"], "password": user_data["password"]}
    login_response = await client.post("/api/v1/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_item(client: AsyncClient, user_data: dict, item_data: dict):
    """测试创建物品"""
    headers = await get_auth_headers(client, user_data)

    response = await client.post("/api/v1/items/", json=item_data, headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == item_data["title"]
    assert data["description"] == item_data["description"]
    assert data["is_active"] == item_data["is_active"]


@pytest.mark.asyncio
async def test_create_item_without_auth(client: AsyncClient, item_data: dict):
    """测试无认证创建物品"""
    response = await client.post("/api/v1/items/", json=item_data)
    assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_get_items(client: AsyncClient, user_data: dict, item_data: dict):
    """测试获取物品列表"""
    headers = await get_auth_headers(client, user_data)

    # 创建物品
    await client.post("/api/v1/items/", json=item_data, headers=headers)

    # 获取物品列表
    response = await client.get("/api/v1/items/")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["title"] == item_data["title"]


@pytest.mark.asyncio
async def test_get_item_by_id(client: AsyncClient, user_data: dict, item_data: dict):
    """测试根据ID获取物品"""
    headers = await get_auth_headers(client, user_data)

    # 创建物品
    create_response = await client.post(
        "/api/v1/items/", json=item_data, headers=headers
    )
    created_item = create_response.json()

    # 根据ID获取物品
    response = await client.get(f"/api/v1/items/{created_item['id']}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == created_item["id"]
    assert data["title"] == item_data["title"]


@pytest.mark.asyncio
async def test_update_item(client: AsyncClient, user_data: dict, item_data: dict):
    """测试更新物品"""
    headers = await get_auth_headers(client, user_data)

    # 创建物品
    create_response = await client.post(
        "/api/v1/items/", json=item_data, headers=headers
    )
    created_item = create_response.json()

    # 更新物品
    update_data = {"title": "Updated Item"}
    response = await client.put(
        f"/api/v1/items/{created_item['id']}", json=update_data, headers=headers
    )
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == update_data["title"]


@pytest.mark.asyncio
async def test_delete_item(client: AsyncClient, user_data: dict, item_data: dict):
    """测试删除物品"""
    headers = await get_auth_headers(client, user_data)

    # 创建物品
    create_response = await client.post(
        "/api/v1/items/", json=item_data, headers=headers
    )
    created_item = create_response.json()

    # 删除物品
    response = await client.delete(
        f"/api/v1/items/{created_item['id']}", headers=headers
    )
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "物品删除成功"


@pytest.mark.asyncio
async def test_get_my_items(client: AsyncClient, user_data: dict, item_data: dict):
    """测试获取我的物品"""
    headers = await get_auth_headers(client, user_data)

    # 创建物品
    await client.post("/api/v1/items/", json=item_data, headers=headers)

    # 获取我的物品
    response = await client.get("/api/v1/items/my", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["title"] == item_data["title"]
