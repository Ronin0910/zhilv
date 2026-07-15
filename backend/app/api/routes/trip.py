"""旅行规划API路由"""
import traceback

from fastapi import APIRouter, HTTPException

from app.agents.trip_planner_agent import get_trip_planner_agent, get_planner_info
from app.models.schemas import TripPlan, TripRequest, TripPlanResponse

router = APIRouter(prefix="/trip", tags=["旅行规划"])

@router.post(
    "/plan",
    response_model=TripPlanResponse,
    summary="生成旅行计划",
    description="根据用户输入的旅行需求，生成详细的旅行计划"
)
async def plan_trip(request: TripRequest):
    """
    生成旅行计划

    Args:
        request: 旅行请求参数

    Returns:
        旅行计划响应
    """
    try:
        print(f"📥 收到旅行规划请求")

        # 获取agent实例
        agent = get_trip_planner_agent()

        # 生成旅行计划
        print("🚀 开始生成旅行计划...")
        trip_plan = await agent.plan_trip(request)

        return TripPlanResponse(
            success=True,
            message="旅行计划生成成功",
            data=trip_plan
        )
    except Exception as e:
        print(f"❌ 生成旅行计划失败: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"生成旅行计划失败: {str(e)}"
        )

@router.get(
    "/health",
    summary="健康检查",
    description="检查旅行规划服务是否正常"
)
async def health_check():
    """健康检查"""
    try:
        info = get_planner_info()

        if not info.get("initialized"):
            raise HTTPException(
                status_code=503,
                detail="旅行规划系统尚未初始化"
            )

        return {
            "status": "healthy",
            "service": "trip-planner",
            "agent_name": "MultiAgentTripPlanner (LangChain)",
            "tools_count": info.get("tools_count", 0),
            "tool_names": info.get("tool_names", []),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"服务不可用: {str(e)}"
        )