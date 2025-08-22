"""
工具函数单元测试
"""

import pytest
from datetime import datetime

from app.utils.helpers import (
    generate_random_string,
    generate_uuid,
    get_timestamp,
    format_datetime,
    mask_email,
    mask_phone,
    Timer,
)
from app.utils.validators import Validator


class TestHelpers:
    """工具函数测试"""

    def test_generate_random_string(self):
        """测试生成随机字符串"""
        # 默认长度
        random_str = generate_random_string()
        assert len(random_str) == 32
        assert random_str.isalnum() or "_" in random_str or "-" in random_str

        # 自定义长度
        random_str_10 = generate_random_string(10)
        assert len(random_str_10) == 10

        # 两次生成的字符串应该不同
        str1 = generate_random_string()
        str2 = generate_random_string()
        assert str1 != str2

    def test_generate_uuid(self):
        """测试生成UUID"""
        uuid_str = generate_uuid()
        assert len(uuid_str) == 36
        assert uuid_str.count("-") == 4

        # 两次生成的UUID应该不同
        uuid1 = generate_uuid()
        uuid2 = generate_uuid()
        assert uuid1 != uuid2

    def test_get_timestamp(self):
        """测试获取时间戳"""
        timestamp = get_timestamp()
        assert isinstance(timestamp, int)
        assert timestamp > 0

        # 时间戳应该接近当前时间
        now = datetime.now().timestamp()
        assert abs(timestamp - now) < 1  # 误差小于1秒

    def test_format_datetime(self):
        """测试格式化日期时间"""
        # 默认格式化当前时间
        formatted = format_datetime()
        assert len(formatted) == 19  # YYYY-MM-DD HH:MM:SS

        # 格式化指定时间
        dt = datetime(2023, 1, 1, 12, 0, 0)
        formatted = format_datetime(dt)
        assert "2023-01-01 12:00:00" in formatted

    def test_mask_email(self):
        """测试邮箱脱敏"""
        # 正常邮箱
        email = "test@example.com"
        masked = mask_email(email)
        assert masked == "t**t@example.com"

        # 短邮箱
        short_email = "a@b.com"
        masked_short = mask_email(short_email)
        assert masked_short == "a@b.com"  # 太短不脱敏

        # 无效邮箱
        invalid_email = "notanemail"
        masked_invalid = mask_email(invalid_email)
        assert masked_invalid == "notanemail"

    def test_mask_phone(self):
        """测试手机号脱敏"""
        # 正常手机号
        phone = "13812345678"
        masked = mask_phone(phone)
        assert masked == "138****5678"

        # 短号码
        short_phone = "123"
        masked_short = mask_phone(short_phone)
        assert masked_short == "123"  # 太短不脱敏

    def test_timer(self):
        """测试计时器"""
        import time

        with Timer("测试操作") as timer:
            time.sleep(0.1)  # 睡眠100毫秒

        assert timer.elapsed >= 0.1
        assert timer.elapsed < 0.2  # 应该接近0.1秒


class TestValidators:
    """验证器测试"""

    def test_validate_email(self):
        """测试邮箱验证"""
        # 有效邮箱
        assert Validator.validate_email("test@example.com")
        assert Validator.validate_email("user.name@domain.co.uk")

        # 无效邮箱
        assert not Validator.validate_email("invalid-email")
        assert not Validator.validate_email("@example.com")
        assert not Validator.validate_email("test@")

    def test_validate_password(self):
        """测试密码验证"""
        # 强密码
        strong_password = "StrongPass123"
        errors = Validator.validate_password(strong_password)
        assert len(errors) == 0

        # 弱密码
        weak_password = "123"
        errors = Validator.validate_password(weak_password)
        assert len(errors) > 0
        assert any("长度" in error for error in errors)

    def test_validate_username(self):
        """测试用户名验证"""
        # 有效用户名
        valid_usernames = ["test123", "user_name", "test-user"]
        for username in valid_usernames:
            errors = Validator.validate_username(username)
            assert len(errors) == 0

        # 无效用户名
        invalid_usernames = ["ab", "user@name", "-user", "user_", ""]
        for username in invalid_usernames:
            errors = Validator.validate_username(username)
            assert len(errors) > 0

    def test_validate_phone(self):
        """测试手机号验证"""
        # 有效手机号
        valid_phones = ["13812345678", "15987654321", "18666666666"]
        for phone in valid_phones:
            assert Validator.validate_phone(phone)

        # 无效手机号
        invalid_phones = ["12345678901", "1381234567", "abc12345678"]
        for phone in invalid_phones:
            assert not Validator.validate_phone(phone)

    def test_validate_url(self):
        """测试URL验证"""
        # 有效URL
        valid_urls = [
            "https://example.com",
            "http://www.test.com/path",
            "https://api.example.com/v1/users?id=1",
        ]
        for url in valid_urls:
            assert Validator.validate_url(url)

        # 无效URL
        invalid_urls = ["not-a-url", "ftp://example.com", "example.com"]
        for url in invalid_urls:
            assert not Validator.validate_url(url)

    def test_validate_json(self):
        """测试JSON验证"""
        # 有效JSON
        valid_json = '{"name": "test", "age": 25}'
        assert Validator.validate_json(valid_json)

        # 无效JSON
        invalid_json = '{"name": "test", "age":}'
        assert not Validator.validate_json(invalid_json)

    def test_sanitize_input(self):
        """测试输入清理"""
        # 包含危险字符的输入
        dangerous_input = '<script>alert("xss")</script>'
        sanitized = Validator.sanitize_input(dangerous_input)
        assert "<" not in sanitized
        assert ">" not in sanitized
        assert "script" in sanitized  # 单词保留，符号移除

        # 正常输入
        normal_input = "  hello world  "
        sanitized = Validator.sanitize_input(normal_input)
        assert sanitized == "hello world"

    def test_validate_sql_injection(self):
        """测试SQL注入检查"""
        # 安全输入
        safe_inputs = ["hello world", "user123", "normal text"]
        for input_str in safe_inputs:
            assert Validator.validate_sql_injection(input_str)

        # 危险输入
        dangerous_inputs = [
            "'; DROP TABLE users; --",
            "SELECT * FROM users",
            "<script>alert('xss')</script>",
        ]
        for input_str in dangerous_inputs:
            assert not Validator.validate_sql_injection(input_str)
