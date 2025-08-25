# app/schemas/chat.py
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ChatMessageCreate(BaseModel):
    """创建聊天消息请求"""
    message: str = Field(..., min_length=1, max_length=2000, description="用户消息内容")
    session_id: Optional[int] = Field(None, description="会话ID，不提供则创建新会话")

class ChatMessageResponse(BaseModel):
    """聊天消息响应"""
    id: int
    role: str
    content: str
    tokens_used: int
    response_time: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChatSessionCreate(BaseModel):
    """创建聊天会话请求"""
    title: Optional[str] = Field("新对话", max_length=200)

class ChatSessionResponse(BaseModel):
    """聊天会话响应"""
    id: int
    title: str
    created_at: datetime
    updated_at: Optional[datetime]
    message_count: int = 0
    
    class Config:
        from_attributes = True

class ChatCompletionResponse(BaseModel):
    """AI聊天完整响应"""
    session_id: int
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
    total_tokens: int
    total_cost: Optional[float] = None