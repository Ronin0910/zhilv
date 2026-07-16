"""配置管理模块"""

import os
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Settings(BaseSettings):
    """应用配置"""

    # 应用基本配置
    app_name: str = "智能旅行助手"
    app_version: str = "1.0.0"
    debug: bool = False

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS配置 - 使用字符串,在代码中分割
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"

    # 高德地图API配置
    amap_api_key: str = ""

    # Unsplash API配置
    unsplash_access_key: str = ""
    unsplash_secret_key: str = ""

    # LLM配置 (从环境变量读取)
    openai_api_key: str = ""
    openai_base_url: str = "https://ws-p8l69mnu623vlqhb.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
    openai_model: str = "qwen-plus"
    embedding_model: str = "text-embedding-v3"

    # RAG 配置 - Pinecone 向量数据库
    pinecone_api_key: str = ""
    pinecone_index_name: str = "travel-knowledge"
    pinecone_namespace: str = "travel"

    # RAG 配置 - 知识库
    knowledge_dir: str = "./knowledge"

    # RAG 配置 - 检索参数
    rag_top_k: int = 5
    rag_chunk_size: int = 512
    rag_chunk_overlap: int = 50
    rag_enable_reranker: bool = False

    # 日志配置
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # 忽略额外的环境变量

    def get_cors_origins_list(self) -> List[str]:
        """获取CORS origins列表"""
        return [origin.strip() for origin in self.cors_origins.split(',')]

    def get_embedding_config(self) -> dict:
        """获取 Embedding 模型配置（供 RAG 模块使用）"""
        return {
            "model": os.getenv("LLM_EMBEDDING_MODEL") or self.embedding_model,
            "api_key": os.getenv("LLM_API_KEY") or self.openai_api_key,
            "base_url": os.getenv("LLM_BASE_URL") or self.openai_base_url,
        }

    def get_pinecone_config(self) -> dict:
        """获取 Pinecone 配置（供 RAG 模块使用）"""
        return {
            "api_key": self.pinecone_api_key,
            "index_name": self.pinecone_index_name,
            "namespace": self.pinecone_namespace,
        }


# 创建全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings


# 验证必要的配置
def validate_config():
    """验证配置是否完整"""
    errors = []
    warnings = []

    if not settings.amap_api_key:
        errors.append("AMAP_API_KEY未配置")

    # LLM API Key: 优先读取LLM_API_KEY,其次OPENAI_API_KEY
    llm_api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not llm_api_key:
        warnings.append("LLM_API_KEY或OPENAI_API_KEY未配置,LLM功能可能无法使用")

    # RAG 配置验证
    if not settings.pinecone_api_key:
        warnings.append("PINECONE_API_KEY未配置,RAG问答功能将不可用")

    if errors:
        error_msg = "配置错误:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_msg)

    if warnings:
        print("\n⚠️  配置警告:")
        for w in warnings:
            print(f"  - {w}")

    return True


# 打印配置信息(用于调试)
def print_config():
    """打印当前配置(隐藏敏感信息)"""
    print(f"应用名称: {settings.app_name}")
    print(f"版本: {settings.app_version}")
    print(f"服务器: {settings.host}:{settings.port}")
    print(f"高德地图API Key: {'已配置' if settings.amap_api_key else '未配置'}")

    # 检查LLM配置
    llm_api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    llm_base_url = os.getenv("LLM_BASE_URL") or settings.openai_base_url
    llm_model = os.getenv("LLM_MODEL_ID") or settings.openai_model

    print(f"LLM API Key: {'已配置' if llm_api_key else '未配置'}")
    print(f"LLM Base URL: {llm_base_url}")
    print(f"LLM Model: {llm_model}")

    # RAG 配置
    print(f"Pinecone API Key: {'已配置' if settings.pinecone_api_key else '未配置'}")
    print(f"Pinecone 索引: {settings.pinecone_index_name}")
    print(f"知识库目录: {settings.knowledge_dir}")

    print(f"日志级别: {settings.log_level}")

