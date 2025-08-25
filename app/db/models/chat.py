# app/db/models/chat.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class ChatSession(Base):
    """聊天会话模型"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    title = Column(String(200), nullable=False, default="新对话")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    """聊天消息模型"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)  # "user" 或 "assistant"
    content = Column(Text, nullable=False)
    tokens_used = Column(Integer, default=0)
    model_used = Column(String(50), nullable=True)
    response_time = Column(Float, nullable=True)  # 响应时间（秒）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联关系
    session = relationship("ChatSession", back_populates="messages")