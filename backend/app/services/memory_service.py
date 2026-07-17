"""短期记忆服务 — 管理多轮对话历史"""
from langchain_mongodb import MongoDBChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
from pymongo import MongoClient
from typing import Optional

from app.config import get_settings


class MemoryService:

    def __init__(self):
        self._client: Optional[MongoClient] = None
        self._db = None
        self._collection = None
        self.settings = get_settings()

    def init(self):
        """初始化MongoDB连接 + TTL索引"""
        if self._client:
            return

        url = self.settings.mongodb_url
        db_name = self.settings.mongodb_database
        collection_name = self.settings.mongodb_collection

        print(f"正在连接 MongoDB...")
        self._client = MongoClient(url, serverSelectionTimeoutMS=1000)

        # 获取数据库和集合
        self._db = self._client[db_name]
        self._collection = self._db[collection_name]

        print(f"✅MongoDB连接成功")
        print(f"   URI: {url}")
        print(f"   数据库: {db_name}")
        print(f"   集合: {collection_name}")


    def get_history(self, session_id: str) -> MongoDBChatMessageHistory:
        """
        获取指定会话的聊天历史对象

        Args:
            session_id: str

        Returns:
            MongoDBChatMessageHistory 实例
        """
        self._check_ready()

        return MongoDBChatMessageHistory(
            connection_string=self.settings.mongodb_url,
            session_id=session_id,
            database_name=self.settings.mongodb_database,
            collection_name=self.settings.mongodb_collection,
        )

    def add_qa(self, session_id: str, question: str, answer: str):
        """
        保存一轮问答到聊天历史

        Args:
            session_id: 会话 ID
            question: 用户问题
            answer: LLM 回答
        """
        history = self.get_history(session_id)
        history.add_message(HumanMessage(question))
        history.add_message(AIMessage(answer))

    def get_messages(self, session_id: str, max_turns: int = 10) -> list:
        """
        获取最近 N 轮聊天历史

        Args:
            session_id: 会话 ID
            max_turns: 最大轮数（每轮 = 1 human + 1 ai）

        Returns:
            消息列表，每条是 HumanMessage 或 AIMessage
        """
        history = self.get_history(session_id)
        messages = history.messages

        # 取最近max_turns轮的消息
        max_messages = max_turns * 2
        if len(messages) > max_messages:
            messages = messages[-max_messages:]
        return messages

    def clear_session(self, session_id: str):
        """清空指定会话的聊天历史"""
        self._check_ready()
        history = self.get_history(session_id)
        history.clear()

    def _check_ready(self):
        if not self._client:
            raise RuntimeError("MongoDB 未初始化，请先调用 init()")

# 全局唯一实例
memory_service = MemoryService()