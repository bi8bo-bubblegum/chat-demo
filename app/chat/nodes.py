from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from app.chat.state import ChatState
from app.common.config import settings

llm = ChatOpenAI(
    model = settings.DEEPSEEK_MODEL,
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL
)

async def chat_node(state: ChatState):
    full_content = ''
    async for chunk in llm.astream(state['messages']):
        if chunk.content:
            full_content += chunk.content
    return {'messages': [AIMessage(content=full_content)]}
