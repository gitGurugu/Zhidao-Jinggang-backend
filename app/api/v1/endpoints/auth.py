"""
认证相关API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_token
from app.db.models.user import User as UserModel
from app.db.session import get_db
from app.schemas.common import Message, Token
from app.schemas.user import User, UserLogin, UserRegister
from app.services.user_service import user_service

router = APIRouter()
security = HTTPBearer()


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(security),
) -> UserModel:
    """获取当前用户的依赖注入函数"""
    try:
        # 从Bearer token中提取实际的token
        token_str = token.credentials
        username = verify_token(token_str)
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的令牌"
            )

        user = await user_service.get_current_user(db, username=username)
        return user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/register", response_model=dict, summary="用户注册")
async def register(user_in: UserRegister, db: AsyncSession = Depends(get_db)):
    """
    用户注册

    - **username**: 用户名
    - **email**: 邮箱地址
    - **password**: 密码
    - **full_name**: 全名（可选）
    """
    try:
        result = await user_service.register(db, user_in=user_in)
        return {
            "message": "注册成功",
            "token": result["token"],
            "user": User.model_validate(result["user"]),
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=Token, summary="用户登录")
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    用户登录

    - **username**: 用户名
    - **password**: 密码
    """
    try:
        token = await user_service.login(db, user_in=user_in)
        return token
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=Token, summary="刷新令牌")
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    """
    刷新访问令牌

    - **refresh_token**: 刷新令牌
    """
    try:
        username = verify_token(refresh_token)
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的刷新令牌"
            )
        user = await user_service.get_current_user(db, username=username)
        from app.core.security import create_token_pair

        token = create_token_pair(user.username)
        return token
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/me", response_model=User, summary="获取当前用户信息")
async def get_current_user_info(current_user: UserModel = Depends(get_current_user)):
    """
    获取当前登录用户的信息
    """
    return User.model_validate(current_user)
