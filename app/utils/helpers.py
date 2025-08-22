"""
辅助工具函数
"""

import hashlib
import secrets
import string
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pathlib import Path

from app.core.config import settings


def generate_random_string(length: int = 32) -> str:
    """生成随机字符串"""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_uuid() -> str:
    """生成UUID"""
    import uuid

    return str(uuid.uuid4())


def get_timestamp() -> int:
    """获取当前时间戳"""
    return int(datetime.now(timezone.utc).timestamp())


def format_datetime(dt: Optional[datetime] = None) -> str:
    """格式化日期时间"""
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def create_file_hash(file_path: str) -> str:
    """创建文件哈希"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def ensure_dir_exists(dir_path: str) -> None:
    """确保目录存在"""
    Path(dir_path).mkdir(parents=True, exist_ok=True)


def get_file_size(file_path: str) -> int:
    """获取文件大小"""
    return Path(file_path).stat().st_size


def is_valid_file_extension(filename: str) -> bool:
    """检查文件扩展名是否有效"""
    ext = Path(filename).suffix.lower()
    return ext in settings.ALLOWED_EXTENSIONS


def clean_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """清理字典中的None值"""
    return {k: v for k, v in data.items() if v is not None}


def mask_email(email: str) -> str:
    """脱敏邮箱地址"""
    if "@" not in email:
        return email

    local, domain = email.split("@", 1)
    if len(local) <= 2:
        return email

    masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """脱敏手机号"""
    if len(phone) < 7:
        return phone
    return phone[:3] + "****" + phone[-4:]


class Timer:
    """计时器上下文管理器"""

    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        print(f"{self.name} took {duration:.4f} seconds")

    @property
    def elapsed(self) -> float:
        """获取已用时间"""
        if self.start_time is None:
            return 0.0
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
