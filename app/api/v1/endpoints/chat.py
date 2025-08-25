# app/api/v1/endpoints/chat.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_db
from app.db.models.user import User
from app.schemas.chat import (
    ChatMessageCreate, 
    ChatMessageResponse,
    ChatSessionResponse,
    ChatCompletionResponse
)
from app.services.chat_service import ChatService

router = APIRouter()

@router.post("/chat", response_model=ChatCompletionResponse)
async def chat_completion(
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """AI聊天接口"""
    try:
        chat_service = ChatService(db)
        result = await chat_service.chat_completion(current_user.id, message_data)
        
        return ChatCompletionResponse(
            session_id=result["session_id"],
            user_message=result["user_message"],
            assistant_message=result["assistant_message"],
            total_tokens=result["total_tokens"]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="聊天服务暂时不可用"
        )

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的聊天会话列表"""
    chat_service = ChatService(db)
    sessions = await chat_service.get_user_sessions(current_user.id)
    
    return [
        ChatSessionResponse(
            id=session.id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=len(session.messages)
        )
        for session in sessions
    ]

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_session_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取会话的消息历史"""
    try:
        chat_service = ChatService(db)
        messages = await chat_service.get_session_messages(session_id, current_user.id)
        
        return [
            ChatMessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                tokens_used=msg.tokens_used or 0,
                response_time=msg.response_time,
                created_at=msg.created_at
            )
            for msg in messages
        ]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )