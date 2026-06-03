import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.conversation.models import Conversation


async def create_conversation(db: AsyncSession, conversation: Conversation) -> Conversation:
    db.add(conversation)
    await db.flush()
    return conversation

async def list_active_conversation_by_user(db: AsyncSession, user_id: str) -> list[Conversation]:
    sql = (select(Conversation)
           .where(Conversation.user_id == user_id, Conversation.is_active == True)
           .order_by(Conversation.created_at.desc())
           )
    result = await db.execute(sql)
    return list(result.scalars().all())

async def get_conversation_by_id(db: AsyncSession, conversation_id: str) -> Conversation | None:
    sql = (select(Conversation)
           .where(Conversation.id == conversation_id)
           )
    result = await db.execute(sql)
    return result.scalar_one_or_none()

async def soft_delete_conversation(db: AsyncSession, conversation: Conversation) -> None:
    conversation.is_active = False
    await db.flush()

async def update_title(db: AsyncSession, conversation_id: str, title: str):
    sql = (select(Conversation)
           .where(Conversation.id == conversation_id)
           )
    result = await db.execute(sql)
    conversation = result.scalar_one_or_none()
    if conversation:
        conversation.title = title
        await db.flush()