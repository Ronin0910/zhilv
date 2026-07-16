import os
from langchain.chat_models import init_chat_model
from app.config import get_settings


class LLMService:

    def __init__(self):
        self._llm_instance = None
        self._settings = get_settings()

    def get_llm(self):
        """获取LLM实例"""
        if self._llm_instance:
            return self._llm_instance

        # 读取LLM配置
        api_key = os.getenv("LLM_API_KEY") or self._settings.openai_api_key
        base_url = os.getenv("LLM_BASE_URL") or self._settings.openai_base_url
        model = os.getenv("LLM_MODEL_ID") or self._settings.openai_model

        if not api_key:
            raise ValueError(
                "LLM API KEY未配置，请配置好"
            )

        # 创建大模型实例
        self._llm_instance = init_chat_model(
            model=model,
            model_provider="openai",
            api_key=api_key,
            base_url=base_url,
            temperature=0.7,
            timeout=60
        )

        print(f"✅ LLM服务初始化成功 (LangChain)")
        print(f"   模型: {model}")
        print(f"   Base URL: {base_url}")

        return self._llm_instance

    def reset_llm(self):
        """重置LLM实例"""
        self._llm_instance = None

# 全局唯一实例
llm_service = LLMService()