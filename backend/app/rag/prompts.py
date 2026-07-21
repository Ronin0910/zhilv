"""RAG专用 Prompt 模板"""

RAG_AGENT_PROMPT = """你是专业的旅游问答助手。

**回答规则：**
1. 优先使用 search_knowledge_base 工具从旅游知识库中检索相关信息
2. 如果知识库中没有相关信息，使用 TavilySearch 工具搜索互联网
3. 结合聊天历史理解用户的意图，保持对话连贯
4. 回答要简洁、准确、有条理
5. 不要编造信息，只基于工具返回的结果回答"""


def build_context_string(docs: list)-> str:
    """把检索到的文档列表拼成一个字符串"""
    parts = []
    for i, doc in enumerate(docs):
        source = doc.metadata.get("source","未知来源")
        parts.append(f"[来源: {source}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)