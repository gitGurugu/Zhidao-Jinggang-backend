"""
日志配置
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict

from loguru import logger

from app.core.config import settings


def setup_logging() -> None:
    """设置日志配置"""
    # 移除默认处理器
    logger.remove()

    # 创建日志目录
    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # 控制台输出格式
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # 文件输出格式
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )

    # 添加控制台处理器
    logger.add(
        sys.stdout,
        format=console_format,
        level=settings.LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # 添加文件处理器
    logger.add(
        settings.LOG_FILE,
        format=file_format,
        level=settings.LOG_LEVEL,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
    )

    # 错误日志单独文件
    error_log_file = log_dir / "error.log"
    logger.add(
        error_log_file,
        format=file_format,
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
    )

    # 过滤第三方库的日志 - 修复过滤器
    logger.add(
        sys.stdout,
        level="INFO",
        format=console_format,
        filter=filter_third_party_logs,
    )


def filter_third_party_logs(record: Dict[str, Any]) -> bool:
    """过滤第三方库的日志"""
    # 过滤掉过于详细的第三方库日志
    filtered_modules = [
        "uvicorn.access",
        "sqlalchemy.engine",
        "httpx",
        "redis",
    ]

    for module in filtered_modules:
        if record["name"].startswith(module):
            return record["level"].no >= logger.level("WARNING").no

    return True


def get_logger(name: str) -> logger:
    """获取指定名称的日志器"""
    return logger.bind(name=name)
