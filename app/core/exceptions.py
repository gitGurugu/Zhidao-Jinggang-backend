"""
自定义异常类
"""

from typing import Any, Dict, Optional

from fastapi import HTTPException, status


class CustomHTTPException(HTTPException):
    """自定义HTTP异常基类"""

    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


class AuthenticationException(CustomHTTPException):
    """认证异常"""

    def __init__(self, detail: str = "未授权访问", error_code: str = "AUTH_ERROR"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code=error_code,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationException(CustomHTTPException):
    """授权异常"""

    def __init__(self, detail: str = "权限不足", error_code: str = "PERMISSION_DENIED"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
        )


class ValidationException(CustomHTTPException):
    """验证异常"""

    def __init__(
        self, detail: str = "数据验证失败", error_code: str = "VALIDATION_ERROR"
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code=error_code,
        )


class BusinessException(CustomHTTPException):
    """业务异常"""

    def __init__(
        self, detail: str = "业务处理失败", error_code: str = "BUSINESS_ERROR"
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code,
        )


class ResourceNotFoundException(CustomHTTPException):
    """资源未找到异常"""

    def __init__(
        self, detail: str = "资源不存在", error_code: str = "RESOURCE_NOT_FOUND"
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code=error_code,
        )


class ConflictException(CustomHTTPException):
    """冲突异常"""

    def __init__(self, detail: str = "资源冲突", error_code: str = "RESOURCE_CONFLICT"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code=error_code,
        )


class RateLimitException(CustomHTTPException):
    """速率限制异常"""

    def __init__(
        self, detail: str = "请求过于频繁", error_code: str = "RATE_LIMIT_EXCEEDED"
    ):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code=error_code,
        )


class ServiceUnavailableException(CustomHTTPException):
    """服务不可用异常"""

    def __init__(
        self, detail: str = "服务暂时不可用", error_code: str = "SERVICE_UNAVAILABLE"
    ):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code=error_code,
        )


class InternalServerException(CustomHTTPException):
    """内部服务器异常"""

    def __init__(
        self, detail: str = "内部服务器错误", error_code: str = "INTERNAL_SERVER_ERROR"
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code=error_code,
        )
