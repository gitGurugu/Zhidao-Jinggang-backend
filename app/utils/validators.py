"""
验证器工具
"""

import re
from typing import Any, Dict, List, Optional
from email_validator import validate_email, EmailNotValidError

from app.core.config import settings


class ValidationError(Exception):
    """验证错误"""

    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


class Validator:
    """通用验证器"""

    @staticmethod
    def validate_email(email: str) -> bool:
        """验证邮箱格式"""
        try:
            validate_email(email)
            return True
        except EmailNotValidError:
            return False

    @staticmethod
    def validate_password(password: str) -> List[str]:
        """验证密码强度，返回错误信息列表"""
        errors = []

        if len(password) < settings.PASSWORD_MIN_LENGTH:
            errors.append(f"密码长度至少为{settings.PASSWORD_MIN_LENGTH}位")

        if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
            errors.append("密码必须包含至少一个大写字母")

        if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
            errors.append("密码必须包含至少一个小写字母")

        if settings.PASSWORD_REQUIRE_NUMBERS and not re.search(r"\d", password):
            errors.append("密码必须包含至少一个数字")

        if settings.PASSWORD_REQUIRE_SYMBOLS and not re.search(
            r"[!@#$%^&*(),.?\":{}|<>]", password
        ):
            errors.append("密码必须包含至少一个特殊字符")

        return errors

    @staticmethod
    def validate_username(username: str) -> List[str]:
        """验证用户名"""
        errors = []

        if not username:
            errors.append("用户名不能为空")
            return errors

        if len(username) < 3:
            errors.append("用户名长度至少为3位")

        if len(username) > 50:
            errors.append("用户名长度不能超过50位")

        if not re.match(r"^[a-zA-Z0-9_-]+$", username):
            errors.append("用户名只能包含字母、数字、下划线和连字符")

        if username.startswith(("-", "_")) or username.endswith(("-", "_")):
            errors.append("用户名不能以连字符或下划线开始或结束")

        return errors

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """验证手机号格式"""
        # 中国手机号格式
        pattern = r"^1[3-9]\d{9}$"
        return bool(re.match(pattern, phone))

    @staticmethod
    def validate_id_card(id_card: str) -> bool:
        """验证身份证号格式"""
        # 18位身份证号格式
        pattern = r"^[1-9]\d{5}(18|19|20)\d{2}((0[1-9])|(1[0-2]))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$"
        return bool(re.match(pattern, id_card))

    @staticmethod
    def validate_url(url: str) -> bool:
        """验证URL格式"""
        pattern = r"^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$"
        return bool(re.match(pattern, url))

    @staticmethod
    def validate_ip(ip: str) -> bool:
        """验证IP地址格式"""
        # IPv4格式
        ipv4_pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        if re.match(ipv4_pattern, ip):
            return True

        # IPv6格式（简化）
        ipv6_pattern = r"^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$"
        return bool(re.match(ipv6_pattern, ip))

    @staticmethod
    def validate_file_extension(
        filename: str, allowed_extensions: Optional[List[str]] = None
    ) -> bool:
        """验证文件扩展名"""
        if not filename:
            return False

        if allowed_extensions is None:
            allowed_extensions = settings.ALLOWED_EXTENSIONS

        file_ext = "." + filename.rsplit(".", 1)[1].lower() if "." in filename else ""
        return file_ext in allowed_extensions

    @staticmethod
    def validate_file_size(file_size: int, max_size: Optional[int] = None) -> bool:
        """验证文件大小"""
        if max_size is None:
            max_size = settings.MAX_UPLOAD_SIZE

        return file_size <= max_size

    @staticmethod
    def validate_json(data: str) -> bool:
        """验证JSON格式"""
        try:
            import json

            json.loads(data)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def validate_date_format(date_str: str, format_str: str = "%Y-%m-%d") -> bool:
        """验证日期格式"""
        try:
            from datetime import datetime

            datetime.strptime(date_str, format_str)
            return True
        except ValueError:
            return False

    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """清理输入字符串"""
        if not input_str:
            return ""

        # 移除危险字符
        dangerous_chars = ["<", ">", "&", '"', "'", "/", "\\"]
        for char in dangerous_chars:
            input_str = input_str.replace(char, "")

        # 去除首尾空格
        return input_str.strip()

    @staticmethod
    def validate_sql_injection(input_str: str) -> bool:
        """检查SQL注入风险"""
        if not input_str:
            return True

        # SQL注入关键词
        sql_keywords = [
            "select",
            "insert",
            "update",
            "delete",
            "drop",
            "create",
            "alter",
            "union",
            "where",
            "order",
            "group",
            "having",
            "exec",
            "execute",
            "script",
            "javascript",
            "vbscript",
            "onload",
            "onerror",
        ]

        input_lower = input_str.lower()
        for keyword in sql_keywords:
            if keyword in input_lower:
                return False

        return True


def validate_request_data(
    data: Dict[str, Any], rules: Dict[str, Dict[str, Any]]
) -> List[str]:
    """验证请求数据

    Args:
        data: 要验证的数据
        rules: 验证规则
            {
                "field_name": {
                    "required": True,
                    "type": str,
                    "min_length": 3,
                    "max_length": 50,
                    "validator": lambda x: x.isalnum()
                }
            }

    Returns:
        错误信息列表
    """
    errors = []

    for field, rule in rules.items():
        value = data.get(field)

        # 检查必填字段
        if rule.get("required", False) and not value:
            errors.append(f"{field}不能为空")
            continue

        # 如果值为空且非必填，跳过后续验证
        if not value and not rule.get("required", False):
            continue

        # 检查类型
        expected_type = rule.get("type")
        if expected_type and not isinstance(value, expected_type):
            errors.append(f"{field}类型错误，期望{expected_type.__name__}")
            continue

        # 检查字符串长度
        if isinstance(value, str):
            min_length = rule.get("min_length")
            max_length = rule.get("max_length")

            if min_length and len(value) < min_length:
                errors.append(f"{field}长度不能少于{min_length}位")

            if max_length and len(value) > max_length:
                errors.append(f"{field}长度不能超过{max_length}位")

        # 检查数值范围
        if isinstance(value, (int, float)):
            min_value = rule.get("min_value")
            max_value = rule.get("max_value")

            if min_value is not None and value < min_value:
                errors.append(f"{field}不能小于{min_value}")

            if max_value is not None and value > max_value:
                errors.append(f"{field}不能大于{max_value}")

        # 自定义验证器
        validator = rule.get("validator")
        if validator and callable(validator):
            try:
                if not validator(value):
                    errors.append(f"{field}格式不正确")
            except Exception as e:
                errors.append(f"{field}验证失败: {str(e)}")

    return errors
