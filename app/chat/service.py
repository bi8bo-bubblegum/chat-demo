import logging
from typing import AsyncGenerator

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.graph import build_graph
from app.chat.schemas import TokenEvent, DoneEvent, ErrorEvent, TitleUpdateEvent
from app.conversation import service as conversation_service
from app.message import service as message_service
from app.message.repository import count_message_by_conversation

logger = logging.getLogger(__name__)


async def chat_stream(
        conversation_id: str,
        message: str,
        user_id: str,
        db: AsyncSession,
        checkpointer: AsyncPostgresSaver
) -> AsyncGenerator[str, None]:
    try:
        await conversation_service.get_conversation(db, user_id, conversation_id)
        await message_service.save_message(db, conversation_id, 'user', message)
        await db.commit()

        # 判断是否首条消息（此时只有刚保存的 user 消息，assistant 还未生成）
        is_first_message = await count_message_by_conversation(db, conversation_id) <= 1

        graph = build_graph(checkpointer)
        config = {'configurable': {'thread_id': conversation_id}}
        input_state = {
            'messages': [HumanMessage(content=message)],
            'conversation_id': conversation_id
        }
        full_response = ''
        async for event in graph.astream_events(input_state, config, version='v2'):
            kind = event['event']
            if kind == 'on_chat_model_stream':
                chunk = event['data']['chunk']
                if hasattr(chunk, 'content') and chunk.content:
                    full_response += chunk.content
                    token_event = TokenEvent(
                        content=chunk.content
                    )
                    yield f'data: {token_event.model_dump_json()}\n\n'

        await message_service.save_message(db, conversation_id, 'assistant', full_response)
        await db.commit()

        # 首条消息时异步生成标题
        if is_first_message:
            title = await conversation_service.generate_and_update_title(db, conversation_id, message)
            if title:
                title_event = TitleUpdateEvent(conversation_id=conversation_id, title=title)
                yield f'data: {title_event.model_dump_json()}\n\n'

        done_event = DoneEvent(conversation_id=conversation_id)
        yield f'data: {done_event.model_dump_json()}\n\n'
    except Exception as e:
        await db.rollback()
        logger.error(f"Chat stream error: {e}", exc_info=True)
        error_event = ErrorEvent(message=str(e))
        yield f'data: {error_event.model_dump_json()}\n\n'