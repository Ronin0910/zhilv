"""短期记忆服务 — 管理多轮对话历史(MongoDB)"""
import json
from typing import Optional
import redis

from app.config import get_settings


class MemoryService:

    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self.settings = get_settings()

    def init(self):
        """初始化redis连接"""
        if self._client:
            return

        url = self.settings.redis_url
        ttl = self.settings.session_ttl_seconds

        # 连接
        print("正在连接 Redis...")
        self._client = redis.from_url(url, decode_responses=True)

        # 验证连接
        self._client.ping()
        print(f"✅Redis连接成功")
        print(f"   URL: {url}")
        print(f"   会话过期: {ttl}s")

    def _key(self, session_id: str) -> str:
        """生成 Redis Key"""
        return f"chat:{session_id}:messages"

    def add_qa(self, session_id: str, question: str, answer: str):
        """
        保存一轮问答到聊天历史

        Args:
            session_id: 会话 ID
            question: 用户问题
            answer: LLM 回答
        """
        self._check_ready()
        key = self._key(session_id)
        ttl = self.settings.session_ttl_seconds

        # 添加消息
        self._client.rpush(key, json.dumps({"type": "human", "content": question}, ensure_ascii=False))
        self._client.rpush(key, json.dumps({"type": "ai", "content": answer}, ensure_ascii=False))

        # 每次写入都刷新TTL
        self._client.expire(key, ttl)

    def get_messages(self, session_id: str, max_turns: int = 10) -> list:
        """
        获取最近 N 轮聊天历史（手动截断）

        Args:
            session_id: 会话 ID
            max_turns: 最大轮数（每轮 = 1 human + 1 ai）

        Returns:
            消息列表，每条是 {"type": "human"|"ai", "content": "..."} 的 dict
        """
        self._check_ready()
        key = self._key(session_id)

        # 读取所有信息
        raw_list = self._client.lrange(key, 0, -1)
        messages = [json.loads(item) for item in raw_list]

        # 只保留最近 max_turns 轮
        max_messages = max_turns * 2
        if len(messages) > max_messages:
            messages = messages[-max_messages:]

        return messages

    def clear_messages(self, session_id: str):
        """清空指定会话的聊天记录"""
        self._check_ready()
        key = self._key(session_id)
        self._client.delete(key)

    def _check_ready(self):
        if not self._client:
            raise RuntimeError("Redis 未初始化， 请先初始化")


# 全局唯一实例
memory_service = MemoryService()