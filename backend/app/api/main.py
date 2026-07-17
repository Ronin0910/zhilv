"""FastAPI主应用"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents.rag_agent import init_rag_agent
from app.services.memory_service import memory_service
from app.services.vector_store import vector_store_service
from ..config import get_settings, validate_config, print_config
from ..agents.trip_planner_agent import init_trip_planner
from ..services.amap_service import init_mcp_client, close_mcp_client
from .routes import trip, poi, map as map_routes, qa

# 获取配置
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # === 启动 ===
    print("\n" + "="*60)
    print(f"🚀 {settings.app_name} v{settings.app_version}")
    print("="*60)

    # 打印配置信息
    print_config()

    # 验证配置
    try:
        validate_config()
        print("\n✅ 配置验证通过")
    except ValueError as e:
        print(f"\n❌ 配置验证失败:\n{e}")
        print("\n请检查.env文件并确保所有必要的配置项都已设置")
        raise

    # 统一初始化MCP工具（一次连接，全局共享）
    try:
        await init_mcp_client()
        print("✅ MCP工具就绪")
    except Exception as e:
        print(f"⚠️  MCP工具初始化失败: {e}")
        print("   地图相关功能可能不可用")

    # 初始化旅行规划多智能体系统（复用已加载的MCP工具）
    try:
        await init_trip_planner()
        print("✅ 旅行规划系统就绪")
    except Exception as e:
        print(f"⚠️  旅行规划系统初始化失败: {e}")
        print("   /api/trip/plan 接口可能不可用")

    try:
        vector_store_service.get_store()  # 触发 Pinecone 懒初始化
    except Exception as e:
        print(f"⚠️ Pinecone 初始化失败（RAG 功能不可用）: {e}")

    try:
        memory_service.init()
    except Exception as e:
        print(f"⚠️ MongoDB 初始化失败（多轮对话不可用）: {e}")

    try:
        await init_rag_agent()
    except Exception as e:
        print(f"⚠️ RAG Agent 初始化失败（问答功能不可用）: {e}")

    print("\n" + "="*60)
    print("📚 API文档: http://localhost:8000/docs")
    print("📖 ReDoc文档: http://localhost:8000/redoc")
    print("="*60 + "\n")

    yield

    # === 关闭 ===
    print("\n" + "="*60)
    print("👋 应用正在关闭...")
    await close_mcp_client()
    print("="*60 + "\n")


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基于LangChain框架的智能旅行规划助手API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(trip.router, prefix="/api")
app.include_router(poi.router, prefix="/api")
app.include_router(map_routes.router, prefix="/api")
app.include_router(qa.router, prefix="/api")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "framework": "LangChain",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "framework": "LangChain"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
