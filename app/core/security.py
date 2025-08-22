"""
安全认证相关功能
"""

import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, validator

from app.core.config import settings
from app.core.exceptions import AuthenticationException


# 密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Token(BaseModel):
    """JWT令牌模型"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """JWT令牌数据模型"""

    username: Optional[str] = None
    scopes: list[str] = []


class PasswordValidator(BaseModel):
    """密码验证器"""

    password: str

    @validator("password")
    def validate_password(cls, v: str) -> str:
        """验证密码强度"""
        if len(v) < settings.PASSWORD_MIN_LENGTH:
            raise ValueError(f"密码长度至少为{settings.PASSWORD_MIN_LENGTH}位")

        if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-Z]", v):
            raise ValueError("密码必须包含至少一个大写字母")

        if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r"[a-z]", v):
            raise ValueError("密码必须包含至少一个小写字母")

        if settings.PASSWORD_REQUIRE_NUMBERS and not re.search(r"\d", v):
            raise ValueError("密码必须包含至少一个数字")

        if settings.PASSWORD_REQUIRE_SYMBOLS and not re.search(
            r"[!@#$%^&*(),.?\":{}|<>]", v
        ):
            raise ValueError("密码必须包含至少一个特殊字符")

        return v


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """创建访问令牌"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """创建刷新令牌"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """验证令牌"""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")

        if username is None:
            return None

        # 检查令牌类型
        if token_type == "refresh":
            if payload.get("type") != "refresh":
                return None

        return username
    except JWTError:
        return None


def create_token_pair(subject: Union[str, Any]) -> Token:
    """创建令牌对（访问令牌和刷新令牌）"""
    access_token = create_access_token(subject)
    refresh_token = create_refresh_token(subject)

    return Token(access_token=access_token, refresh_token=refresh_token)


def generate_password_reset_token(email: str) -> str:
    """生成密码重置令牌"""
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    """验证密码重置令牌"""
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return decoded_token["sub"]
    except JWTError:
        return None


def is_valid_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def sanitize_filename(filename: str) -> str:
    """清理文件名"""
    # 移除危险字符
    sanitized = re.sub(r"[^\w\s-.]", "", filename)
    # 限制长度
    return sanitized[:255]


def is_safe_path(path: str) -> bool:
    """检查路径安全性"""
    # 防止路径遍历攻击
    if ".." in path or path.startswith("/"):
        return False
    return True
