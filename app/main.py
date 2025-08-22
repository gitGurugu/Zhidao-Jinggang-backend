"""
FastAPI应用主入口文件
"""

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from prometheus_client import Counter, Histogram, generate_latest
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exceptions import CustomHTTPException
from app.core.logging import setup_logging
from app.db.session import engine
from app.db.base import Base


# 初始化速率限制器
limiter = Limiter(key_func=get_remote_address)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)
REQUEST_DURATION = Histogram(
    "http_request_duration_seconds", "HTTP request duration", ["method", "endpoint"]
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理"""
    # 启动时执行
    logger.info("应用启动中...")

    # 创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("应用启动完成")
    yield

    # 关闭时执行
    logger.info("应用关闭中...")
    await engine.dispose()
    logger.info("应用关闭完成")


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    # 设置日志
    setup_logging()

    # 创建FastAPI应用
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
        openapi_url="/openapi.json" if settings.ENVIRONMENT == "development" else None,
        lifespan=lifespan,
    )

    # 设置速率限制
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # 添加中间件
    setup_middleware(app)

    # 添加路由
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # 添加异常处理
    setup_exception_handlers(app)

    # 添加系统路由
    setup_system_routes(app)

    return app


def setup_middleware(app: FastAPI) -> None:
    """设置中间件"""
    # HTTPS重定向 (生产环境)
    if settings.ENVIRONMENT == "production":
        app.add_middleware(HTTPSRedirectMiddleware)

    # 信任主机
    if settings.ALLOWED_HOSTS:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS,
        )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Gzip压缩
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # 请求日志和指标中间件
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()

        # 处理请求
        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time

        # 记录指标
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
        ).inc()

        REQUEST_DURATION.labels(
            method=request.method, endpoint=request.url.path
        ).observe(process_time)

        # 记录日志
        logger.info(
            f"{request.method} {request.url.path} "
            f"- {response.status_code} - {process_time:.4f}s"
        )

        return response


def setup_exception_handlers(app: FastAPI) -> None:
    """设置异常处理器"""

    @app.exception_handler(CustomHTTPException)
    async def custom_exception_handler(request: Request, exc: CustomHTTPException):
        logger.error(f"自定义异常: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.detail, "error_code": exc.error_code},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"未处理的异常: {exc}", exc_info=True)
        return JSONResponse(status_code=500, content={"message": "内部服务器错误"})


def setup_system_routes(app: FastAPI) -> None:
    """设置系统路由"""

    @app.get("/health")
    async def health_check():
        """健康检查端点"""
        return {"status": "healthy", "timestamp": time.time()}

    @app.get("/metrics")
    async def metrics():
        """Prometheus指标端点"""
        return Response(generate_latest(), media_type="text/plain")

    @app.get("/")
    async def root():
        """根路径"""
        return {
            "message": "知道井冈 - 企业级FastAPI后端服务",
            "version": settings.VERSION,
            "docs_url": "/docs" if settings.ENVIRONMENT == "development" else None,
        }


# 创建应用实例
app = create_app()
