from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode

from app.chat.state import ChatState
from app.chat.tool import knowledge_search
from app.common.config import settings

llm = ChatOpenAI(
    model = settings.DEEPSEEK_MODEL,
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL
)

llm_with_tools = ChatOpenAI(
    model=settings.DEEPSEEK_MODEL,
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
    streaming=True,
    extra_body={"enable_thinking": False},
).bind_tools([knowledge_search])


async def chat_node(state: ChatState):
    """主聊天节点：判断是否需要调用工具"""
    kb_ids = state.get('knowledge_base_ids', [])

    if kb_ids:
        # 有关联知识库时，使用带 tools 的 LLM
        system_msg = SystemMessage(
            content=(
                "你是一个智能助手。当用户的问题可能与知识库文档相关时，"
                "请使用 knowledge_search 工具搜索知识库获取相关信息，"
                "然后基于检索到的内容回答用户问题。"
                "只能基于检索到的内容回答，不要额外增添其他内容，"
                "注意：一定不要自己编造问题的答案"
                f"\n\n当前对话关联的知识库ID: {kb_ids}"
            )
        )
        messages = [system_msg] + state['messages']
        response = await llm_with_tools.ainvoke(messages)
    else:
        # 无关联知识库时，直接对话
        full_content = ''
        async for chunk in llm.astream(state['messages']):
            if chunk.content:
                full_content += chunk.content
        return {'messages': [AIMessage(content=full_content)]}

    return {'messages': [response]}

async def tool_node(state: ChatState):
    """工具执行节点：处理 LLM 返回的 tool_calls"""
    tools = [knowledge_search]
    tool_node_instance = ToolNode(tools)
    return await tool_node_instance.ainvoke(state)