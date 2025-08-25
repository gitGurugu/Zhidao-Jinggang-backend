# app/services/openai_service.py
import time
from typing import List, Dict, Any, Optional
import openai
from loguru import logger
from app.core.config import settings

class OpenAIService:
    """OpenAI API 服务"""
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 未配置")
        
        self.client = openai.AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT
        )
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        max_tokens: int = None,
        temperature: float = None
    ) -> Dict[str, Any]:
        """
        发送聊天完成请求
        
        Args:
            messages: 消息历史
            model: 使用的模型
            max_tokens: 最大令牌数
            temperature: 温度参数
            
        Returns:
            包含响应内容和元数据的字典
        """
        start_time = time.time()
        
        try:
            response = await self.client.chat.completions.create(
                model=model or settings.OPENAI_MODEL,
                messages=messages,
                max_tokens=max_tokens or settings.OPENAI_MAX_TOKENS,
                temperature=temperature or settings.OPENAI_TEMPERATURE
            )
            
            response_time = time.time() - start_time
            
            return {
                "content": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens,
                "model": response.model,
                "response_time": response_time,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens
            }
            
        except openai.APIError as e:
            logger.error(f"OpenAI API 错误: {e}")
            raise ValueError(f"AI服务暂时不可用: {str(e)}")
        except openai.RateLimitError as e:
            logger.error(f"OpenAI 速率限制: {e}")
            raise ValueError("请求过于频繁，请稍后再试")
        except Exception as e:
            logger.error(f"OpenAI 请求失败: {e}")
            raise ValueError(f"AI服务出现错误: {str(e)}")
    
    async def simple_chat(self, user_message: str, context: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        简单聊天接口
        
        Args:
            user_message: 用户消息
            context: 上下文消息
            
        Returns:
            AI响应结果
        """
        messages = context or []
        messages.append({"role": "user", "content": user_message})
        
        return await self.chat_completion(messages)