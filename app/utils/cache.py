"""
缓存工具
"""

import json
import pickle
from typing import Any, Optional, Union
from functools import wraps

import redis
from loguru import logger

from app.core.config import settings


class RedisCache:
    """Redis缓存类"""

    def __init__(self):
        self.redis_client = None
        self._connect()

    def _connect(self):
        """连接Redis"""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=False,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
            )
            # 测试连接
            self.redis_client.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            self.redis_client = None

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self.redis_client:
            return None

        try:
            value = self.redis_client.get(key)
            if value is None:
                return None

            # 尝试反序列化
            try:
                return pickle.loads(value)
            except:
                # 如果pickle失败，尝试JSON
                try:
                    return json.loads(value.decode("utf-8"))
                except:
                    return value.decode("utf-8")
        except Exception as e:
            logger.error(f"获取缓存失败 {key}: {e}")
            return None

    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """设置缓存"""
        if not self.redis_client:
            return False

        try:
            # 序列化值
            if isinstance(value, (str, int, float)):
                serialized_value = str(value)
            elif isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, ensure_ascii=False)
            else:
                serialized_value = pickle.dumps(value)

            expire = expire or settings.CACHE_EXPIRE_SECONDS
            return self.redis_client.setex(key, expire, serialized_value)
        except Exception as e:
            logger.error(f"设置缓存失败 {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.redis_client:
            return False

        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"删除缓存失败 {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        if not self.redis_client:
            return False

        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"检查缓存失败 {key}: {e}")
            return False

    def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        if not self.redis_client:
            return False

        try:
            return bool(self.redis_client.expire(key, seconds))
        except Exception as e:
            logger.error(f"设置过期时间失败 {key}: {e}")
            return False

    def keys(self, pattern: str = "*") -> list:
        """获取匹配的键"""
        if not self.redis_client:
            return []

        try:
            keys = self.redis_client.keys(pattern)
            return [
                key.decode("utf-8") if isinstance(key, bytes) else key for key in keys
            ]
        except Exception as e:
            logger.error(f"获取键失败 {pattern}: {e}")
            return []

    def flush_all(self) -> bool:
        """清空所有缓存"""
        if not self.redis_client:
            return False

        try:
            return bool(self.redis_client.flushdb())
        except Exception as e:
            logger.error(f"清空缓存失败: {e}")
            return False


# 全局缓存实例
cache = RedisCache()


def cached(key_pattern: str, expire: Optional[int] = None):
    """缓存装饰器"""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = key_pattern.format(*args, **kwargs)

            # 尝试从缓存获取
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_result

            # 执行函数
            result = await func(*args, **kwargs)

            # 存储到缓存
            if result is not None:
                cache.set(cache_key, result, expire)
                logger.debug(f"缓存存储: {cache_key}")

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = key_pattern.format(*args, **kwargs)

            # 尝试从缓存获取
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_result

            # 执行函数
            result = func(*args, **kwargs)

            # 存储到缓存
            if result is not None:
                cache.set(cache_key, result, expire)
                logger.debug(f"缓存存储: {cache_key}")

            return result

        # 检查是否是异步函数
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def cache_key(*args, **kwargs) -> str:
    """生成缓存键"""
    key_parts = []

    # 添加位置参数
    for arg in args:
        if isinstance(arg, (str, int, float)):
            key_parts.append(str(arg))
        else:
            key_parts.append(str(hash(str(arg))))

    # 添加关键字参数
    for k, v in sorted(kwargs.items()):
        if isinstance(v, (str, int, float)):
            key_parts.append(f"{k}:{v}")
        else:
            key_parts.append(f"{k}:{hash(str(v))}")

    return ":".join(key_parts)


class MemoryCache:
    """内存缓存类（用于无Redis环境）"""

    def __init__(self, max_size: int = 1000):
        self._cache = {}
        self._max_size = max_size

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        return self._cache.get(key)

    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """设置缓存"""
        if len(self._cache) >= self._max_size:
            # 简单的LRU：删除第一个元素
            first_key = next(iter(self._cache))
            del self._cache[first_key]

        self._cache[key] = value
        return True

    def delete(self, key: str) -> bool:
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        return key in self._cache

    def flush_all(self) -> bool:
        """清空所有缓存"""
        self._cache.clear()
        return True


# 如果Redis不可用，使用内存缓存作为后备
if not cache.redis_client:
    cache = MemoryCache()
