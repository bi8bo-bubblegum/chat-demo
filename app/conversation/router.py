from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.deps import get_current_user, get_db
from app.common.response import success
from app.auth.models import User
from app.conversation.schemas import ConversationCreate
from app.conversation import service

router = APIRouter(prefix="/api/conversations", tags=["会话"])


@router.post("", status_code=201)
async def create_conversation(
    data: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = await service.create_new_conversation(db, str(current_user.id), data)
    return success(data=conversation.model_dump(), message="创建成功", code=201)


@router.get("")
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversations = await service.list_conversations(db, str(current_user.id))
    return success(data=[c.model_dump() for c in conversations])


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = await service.get_conversation(db, conversation_id, str(current_user.id))
    return success(data=conversation.model_dump())


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await service.delete_conversation(db, conversation_id, str(current_user.id))
    return success(message="删除成功")