"""RAG知识库问答"""
import json
from typing import AsyncGenerator, Optional

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage
from langchain_tavily import TavilySearch
from langchain_core.tools import tool

from app.rag.prompts import build_context_string, RAG_AGENT_PROMPT
from app.services.llm_service import llm_service
from app.services.memory_service import memory_service
from app.services.vector_store import vector_store_service

# ==================== 工具定义 ====================
@tool
def search_knowledge_base(query: str) -> str:
    """
    从旅游知识库中检索相关信息。当用户询问旅游景点、攻略、门票等问题时优先使用此工具。

    Args:
        query:  检索关键词，如景点名称、旅游问题等

    Returns:
        检索到的知识库内容
    """
    docs = vector_store_service.search(query)
    if not docs:
        return "知识库中未找到相关信息"
    return build_context_string(docs)


# ==================== RAG Agent ====================
class RAGAgent:

    def __init__(self, llm):
        self.llm = llm
        self.tools = [search_knowledge_base, TavilySearch(max_results=4)]
        print("- 创建 RAG Agent")

        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=RAG_AGENT_PROMPT
        )
        print("✅RAGAgent初始化成功")

    async def query(self, question: str, session_id: str = None) -> AsyncGenerator[str, None]:
        """
        RAG 完整流程（支持多轮对话）

        Args:
            question: 用户问题
            session_id: 会话 ID（传入则启用短期记忆）

        Yields:
            SSE 格式的字符串：
            - event: token    → 逐字输出
            - event: done     → 完成，携带完整回答和元数据
            - event: error    → 出错
        """
        full_answer = ""
        try:
            # 1. 加载聊天历史（保留原始消息对象，供 MessagesPlaceholder 使用）
            history = []
            if session_id:
                raw_messages = memory_service.get_messages(session_id)
                history = self._to_history_messages(raw_messages)

            # 2. 流式调用 LLM
            async for event in self.agent.astream_events(
                    {
                        "messages": history + [{"role": "user", "content": question}],
                    },
                version="v2"
            ):
                kind = event.get("event", "")

                # 3.捕获生成的token
                if kind == "on_chat_model_stream":
                    chunk = event.get("data",{}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        full_answer += chunk.content
                        yield f"event: token\ndata: {json.dumps({'content':chunk.content}, ensure_ascii=False)}\n\n"

            # 4. 没生成任何内容
            if not full_answer:
                full_answer = "抱歉，无法生成回答，请稍后重试。"
                yield f"event: token\ndata: {json.dumps({'content': full_answer}, ensure_ascii=False)}\n\n"

            # 6. 保存本轮对话到 Redis
            if session_id:
                memory_service.add_qa(session_id, question, full_answer)

            # 7. 发送完成事件
            yield f"event: done\ndata: {json.dumps({'answer': full_answer, 'question': question, 'session_id': session_id}, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    def _to_history_messages(self, messages: list) -> list:
        """将消息列表转换为 agent 可用的消息列表"""
        result = []
        for msg in messages:
            if msg["type"] == "human":
                result.append(HumanMessage(content = msg["content"]))
            elif msg["type"] == "ai":
                result.append(AIMessage(content = msg["content"]))
        return result


# ============ 全局实例管理 ============
rag_agent: Optional[RAGAgent] = None

async def init_rag_agent():
    """初始化全局 RAG Agent"""
    global rag_agent
    if rag_agent is not None:
        return rag_agent

    llm = llm_service.get_llm()
    rag_agent = RAGAgent(llm)
    return rag_agent

def get_rag_agent() -> RAGAgent:
    if rag_agent is None:
        raise RuntimeError("RAG Agent 尚未初始化。请确保在 FastAPI startup 事件中调用了init_rag_agent()")
    return rag_agent