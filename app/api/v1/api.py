"""
API v1版本主路由
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, items

api_router = APIRouter()

# 认证相关路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])

# 用户相关路由
api_router.include_router(users.router, prefix="/users", tags=["用户"])

# 物品相关路由
api_router.include_router(items.router, prefix="/items", tags=["物品"])
