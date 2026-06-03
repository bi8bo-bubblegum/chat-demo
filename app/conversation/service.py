from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.config import settings
from app.common.exceptions import NotFoundException, ForbiddenException
from app.conversation.models import Conversation
from app.conversation.repository import create_conversation, list_active_conversation_by_user, get_conversation_by_id, \
    soft_delete_conversation, update_title
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

async def generate_and_update_title(db: AsyncSession, conversation_id: str, first_message: str):
    try:
        title_llm = ChatOpenAI(
            model = settings.DEEPSEEK_MODEL,
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            streaming=False,
            max_tokens=30
        )
        response = await title_llm.ainvoke([
            SystemMessage(content='你是一个标题生产助手，根据以下用户消息，生成一个简短4-8个字的对话标题，只输出标题文本，不要加引号和标点'),
            HumanMessage(content=first_message)
        ])
        title = response.content.strip()
        if title:
            await update_title(db, conversation_id, title)
            await db.commit()
            return title
    except Exception as e:
        await db.rollback()
    return None