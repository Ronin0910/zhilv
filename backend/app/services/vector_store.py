"""管理向量数据库的增删改查"""
from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from typing import Optional

from app.config import get_settings
from app.services.embedding_service import embedding_service


class VectorStoreService():
    def __init__(self):
        self._pc: Optional[Pinecone] = None
        self._store: Optional[PineconeVectorStore] = None
        self._settings = get_settings()

    def get_store(self) -> PineconeVectorStore:
        """初始化 Pinecone 客户端 + 确保索引存在 + 创建 VectorStore"""
        if self._store:
            return self._store

        pc_config = self._settings.get_pinecone_config()

        if not pc_config["api_key"]:
            raise ValueError("PINECONE_API_KEY 未配置")

        # Pinecone客户端
        self._pc = Pinecone(api_key=pc_config["api_key"])

        # 确保索引存在
        self._ensure_index(pc_config["index_name"])

        # VectorStore
        self._store = PineconeVectorStore(
            index_name=pc_config["index_name"],
            embedding=embedding_service.get_embedding(),
            pinecone_api_key=pc_config["api_key"],
            namespace=pc_config["namespace"]
        )

        print(f"✅ Pinecone 初始化成功")
        print(f"   索引: {pc_config['index_name']}")
        print(f"   命名空间: {pc_config['namespace']}")

        return self._store

    def _ensure_index(self, index_name: str, dimension: int = 1024):
        """索引不存在自动创建"""
        existing = self._pc.list_indexes().names()
        if index_name in existing:
            return

        print(f"  正在创建索引 '{index_name}' (维度={dimension})...")
        self._pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )

    def _check_ready(self):
        """检查是否已初始化"""
        if not self._store:
            raise RuntimeError("VectorStore 未初始化，请先调用 init()")

    def add_documents(self, documents: list[Document]) -> list[str]:
        """上传文档到向量数据库中"""
        self._check_ready()
        ids = self._store.add_documents(documents)
        print(f"  已上传 {len(ids)} 个文档片段")
        return ids

    def search(self, query: str, top_k: int = 5) -> list[Document]:
        """相似度检索"""
        self._check_ready()
        return self._store.similarity_search(query, k=top_k)

    def search_with_score(self, query: str, top_k: int = 5) -> list[tuple[Document, float]]:
        """带分数的检索"""
        self._check_ready()
        return self._store.similarity_search_with_score(query, k=top_k)

    def delete_by_filter(self, filter_dict: dict):
        """按元数据删除"""
        self._check_ready()
        return self._store.delete(filter=filter_dict)

    def get_index_staus(self) -> dict:
        """获取索引统计信息"""
        if not self._pc:
            raise RuntimeError("Pinecone 未初始化")
        index = self._pc.Index(self._settings.pinecone_index_name)
        stats = index.describe_index_stats()
        return {
            "total_vectors": stats.total_vectors_count,
            "dimensions": stats.dimensions
        }

# 全局唯一实例
vector_store_service = VectorStoreService()
