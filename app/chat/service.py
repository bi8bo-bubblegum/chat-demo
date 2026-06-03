import logging
from typing import AsyncGenerator

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.graph import build_graph
from app.chat.schemas import TokenEvent, DoneEvent, ErrorEvent
from app.conversation import service as conversation_service
from app.message import service as message_service

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
        done_event = DoneEvent(conversation_id=conversation_id)
        yield f'data: {done_event.model_dump_json()}\n\n'
    except Exception as e:
        await db.rollback()
        logger.error(f"Chat stream error: {e}", exc_info=True)
        error_event = ErrorEvent(message=str(e))
        yield f'data: {error_event.model_dump_json()}\n\n'