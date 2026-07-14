import os

from langchain.chat_models import init_chat_model

from app.config import get_settings

#全局LLM实例
_llm_instance =None

def get_llm():
    """获取LLM实例"""
    global _llm_instance
    if _llm_instance is None:
        settings = get_settings()

        # 读取LLM配置
        api_key = os.getenv("LLM_API_KEY") or settings.openai_api_key
        base_url = os.getenv("LLM_BASE_URL") or settings.openai_base_url
        model = os.getenv("LLM_MODEL_ID") or settings.openai_model

        if not api_key:
            raise ValueError(
                "LLM API KEY未配置，请配置好"
            )

        # 创建大模型实例
        _llm_instance = init_chat_model(
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

        return _llm_instance

def reset_llm():
    """重置LLM实例"""
    global _llm_instance
    _llm_instance = None