# app/services/chat_service.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.models.chat import ChatSession, ChatMessage
from app.db.models.user import User
from app.schemas.chat import ChatMessageCreate, ChatSessionCreate
from app.services.openai_service import OpenAIService
from loguru import logger

class ChatService:
    """聊天服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.openai_service = OpenAIService()
    
    async def create_session(self, user_id: int, title: str = "新对话") -> ChatSession:
        """创建聊天会话"""
        session = ChatSession(
            user_id=user_id,
            title=title
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session
    
    async def get_user_sessions(self, user_id: int) -> List[ChatSession]:
        """获取用户的聊天会话列表"""
        result = await self.db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
        )
        return result.scalars().all()
    
    async def get_session_messages(self, session_id: int, user_id: int) -> List[ChatMessage]:
        """获取会话的消息历史"""
        # 验证会话所有权
        session = await self.db.get(ChatSession, session_id)
        if not session or session.user_id != user_id:
            raise ValueError("会话不存在或无权限访问")
        
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        return result.scalars().all()
    
    async def chat_completion(self, user_id: int, message_data: ChatMessageCreate) -> dict:
        """处理聊天请求"""
        try:
            # 获取或创建会话
            if message_data.session_id:
                session = await self.db.get(ChatSession, message_data.session_id)
                if not session or session.user_id != user_id:
                    raise ValueError("会话不存在或无权限访问")
            else:
                session = await self.create_session(user_id)
            
            # 获取消息历史作为上下文
            messages_history = await self.get_session_messages(session.id, user_id)
            context = []
            for msg in messages_history[-10:]:  # 只取最近10条消息作为上下文
                context.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # 保存用户消息
            user_message = ChatMessage(
                session_id=session.id,
                role="user",
                content=message_data.message
            )
            self.db.add(user_message)
            await self.db.flush()
            
            # 调用 OpenAI API
            ai_response = await self.openai_service.simple_chat(
                message_data.message, 
                context
            )
            
            # 保存AI响应
            assistant_message = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=ai_response["content"],
                tokens_used=ai_response["tokens_used"],
                model_used=ai_response["model"],
                response_time=ai_response["response_time"]
            )
            self.db.add(assistant_message)
            
            # 更新会话时间
            session.updated_at = func.now()
            
            await self.db.commit()
            await self.db.refresh(user_message)
            await self.db.refresh(assistant_message)
            
            return {
                "session_id": session.id,
                "user_message": user_message,
                "assistant_message": assistant_message,
                "total_tokens": ai_response["tokens_used"]
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"聊天处理失败: {e}")
            raise