"""问答API路由"""
import json
import uuid
import traceback

from fastapi import APIRouter, Request, HTTPException
from starlette.responses import StreamingResponse

from app.agents.rag_agent import get_rag_agent
from app.models.schemas import QARequest
from app.services.memory_service import memory_service

router = APIRouter(prefix="/qa", tags=["旅游问答"])

@router.post("/chat", summary="提问")
async def chat(req: QARequest, request: Request):
    """提交旅游问题，基于知识库检索 + 聊天历史 + Agent 流式生成回答。"""
    session_id = req.session_id or f"session_{uuid.uuid4().hex[:12]}"

    try:
        agent = get_rag_agent()
    except RuntimeError as e:
        # RAG Agent 未初始化，直接返回错误 SSE
        async def not_ready():
            yield f"event: error\ndata: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
        return StreamingResponse(not_ready(), media_type="text/event-stream")

    async def event_stream():
        try:
            async for chunk in agent.query(req.question, session_id):
                if await request.is_disconnected():
                    break
                yield chunk
        except Exception as e:
            # 打印完整堆栈到后端日志，方便排查
            traceback.print_exc()
            error_msg = str(e).replace('"', '\\"').replace('\n', ' ')
            yield f"event: error\ndata: {json.dumps({'error': error_msg}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

@router.delete("/session/{session_id}", summary="清空会话历史")
async def clear_session(session_id: str):
    """清空指定会话的所有聊天历史"""
    try:
        memory_service.clear_session(session_id)
        return {"message": f"会话 {session_id} 已清空"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", summary="RAG 服务健康检查")
async def health_check():
    """检查 RAG + MongoDB 服务是否正常"""
    result = {"status": "ok", "pinecone": None, "mongodb": None}

    # 检查 Pinecone
    try:
        from app.services.vector_store import vector_store_service
        stats = vector_store_service.get_index_stats()
        result["pinecone"] = {"status": "ok", "index": stats}
    except Exception as e:
        result["pinecone"] = {"status": "error", "detail": str(e)}
        result["status"] = "degraded"

    # 检查 MongoDB
    try:
        from pymongo import MongoClient
        client = MongoClient(memory_service.settings.mongodb_url, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
        result["mongodb"] = {"status": "ok"}
    except Exception as e:
        result["mongodb"] = {"status": "error", "detail": str(e)}
        result["status"] = "degraded"

    return result