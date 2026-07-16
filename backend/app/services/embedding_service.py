"""Embedding 模型封装"""
import os
from langchain_community.embeddings import DashScopeEmbeddings
from app.config import get_settings

class EmbeddingService:

    def __init__(self):
        self._embedding_llm = None
        self._settings = get_settings()

    def get_embedding(self):
        if self._embedding_llm:
            return self._embedding_llm

        # 读取LLM-embedding配置
        apikey = os.getenv("LLM_API_KEY") or self._settings.openai_api_key
        base_url = os.getenv("LLM_BASE_URL") or self._settings.openai_base_url
        model = os.getenv("LLM_EMBEDDING_MODEL") or self._settings.embedding_model

        if not apikey:
            raise ValueError("LLM API KEY未配置，请配置好")

        # 创建向量大模型实例
        self._embedding_llm = DashScopeEmbeddings(
            model=model,
            dashscope_api_key=apikey
        )

        print(f"✅ LLM-EMBEDDING服务初始化成功")
        print(f"   模型: {model}")
        return self._embedding_llm

    def reset_llm(self):
        """重置向量大模型实例"""
        self._embedding_llm = None

# 全局唯一实例
embedding_service = EmbeddingService()