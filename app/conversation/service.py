from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundException, ForbiddenException
from app.conversation.models import Conversation
from app.conversation.repository import create_conversation, list_active_conversation_by_user, get_conversation_by_id, \
    soft_delete_conversation
from app.conversation.schemas import ConversationCreate, ConversationResponse


async def create_new_conversation(db: AsyncSession, user_id: str, conversation_create: ConversationCreate) -> ConversationResponse:
    conversation = Conversation(
        title=conversation_create.title or '新对话',
        user_id=user_id
    )
    conversation = await create_conversation(db, conversation)
    return ConversationResponse.model_validate(conversation)

async def list_conversations(db: AsyncSession, user_id: str) -> list[ConversationResponse]:
    conversation_list = await list_active_conversation_by_user(db, user_id)
    return [ConversationResponse.model_validate(conversation) for conversation in conversation_list]

async def get_conversation(db: AsyncSession, user_id: str, conversation_id: str) -> ConversationResponse:
    conversation = await get_conversation_by_id(db, conversation_id)
    if not conversation:
        raise NotFoundException(message='对话不存在')
    if str(conversation.user_id) != str(user_id):
        raise ForbiddenException(message='无权限访问')
    return ConversationResponse.model_validate(conversation)

async def delete_conversation(db: AsyncSession, conversation_id: str, user_id: str) -> None:
    conversation = await get_conversation_by_id(db, conversation_id)
    if not conversation:
        raise NotFoundException(message="会话不存在")
    if str(conversation.user_id) != str(user_id):
        raise ForbiddenException(message="无权删除该会话")
    await soft_delete_conversation(db, conversation)