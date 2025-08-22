"""
自定义中间件
"""

import time
from typing import Callable
from uuid import uuid4

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求ID
        request_id = str(uuid4())
        request.state.request_id = request_id

        # 记录请求开始
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"

        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "client_ip": client_ip,
                "user_agent": request.headers.get("user-agent", "unknown"),
            },
        )

        # 处理请求
        response = await call_next(request)

        # 记录请求结束
        process_time = time.time() - start_time

        logger.info(
            f"Request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "process_time": process_time,
                "client_ip": client_ip,
            },
        )

        # 添加响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # 添加安全头
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'",
        }

        # 仅在HTTPS环境下添加HSTS头
        if settings.ENVIRONMENT == "production":
            security_headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        for header, value in security_headers.items():
            response.headers[header] = value

        return response


class DatabaseSessionMiddleware(BaseHTTPMiddleware):
    """数据库会话中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 可以在这里添加数据库会话的统一管理逻辑
        response = await call_next(request)
        return response
