"""多智能体旅行规划系统 - LangChain版本"""
import json
import traceback
from datetime import timedelta, datetime
from typing import Optional
from wsgiref.util import request_uri

from langchain_classic.agents import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage

from app.models.schemas import TripRequest, TripPlan, DayPlan, Attraction, Location, Meal
from app.services.amap_service import get_mcp_tools_list, init_mcp_client
from app.services.llm_service import get_llm

# ============ Agent提示词 ============

ATTRACTION_AGENT_PROMPT = """你是景点搜索专家。你的任务是根据城市和用户偏好搜索合适的景点。

**重要提示:**
- 你必须使用工具来搜索景点，不要自己编造景点信息!
- 使用 maps_text_search 工具搜索景点，传入 keywords(关键词) 和 city(城市) 参数。
- 搜索完成后，整理并返回景点信息。"""

WEATHER_AGENT_PROMPT = """你是天气查询专家。你的任务是查询指定城市的天气信息。

**重要提示:**
- 你必须使用工具来查询天气，不要自己编造天气信息!
- 使用 maps_weather 工具查询天气，传入 city(城市) 参数。
- 查询完成后，整理并返回天气信息。"""

HOTEL_AGENT_PROMPT = """你是酒店推荐专家。你的任务是根据城市和景点位置推荐合适的酒店。

**重要提示:**
- 你必须使用工具来搜索酒店，不要自己编造酒店信息!
- 使用 maps_text_search 工具搜索酒店，传入 keywords="酒店" 和 city(城市) 参数。
- 搜索完成后，整理并返回酒店信息。"""

PLANNER_AGENT_PROMPT = """你是行程规划专家。你的任务是根据景点信息和天气信息，生成详细的旅行计划。

请严格按照以下JSON格式返回旅行计划:
```json
{
  "city": "城市名称",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "days": [
    {
      "date": "YYYY-MM-DD",
      "day_index": 0,
      "description": "第1天行程概述",
      "transportation": "交通方式",
      "accommodation": "住宿类型",
      "hotel": {
        "name": "酒店名称",
        "address": "酒店地址",
        "location": {"longitude": 116.397128, "latitude": 39.916527},
        "price_range": "300-500元",
        "rating": "4.5",
        "distance": "距离景点2公里",
        "type": "经济型酒店",
        "estimated_cost": 400
      },
      "attractions": [
        {
          "name": "景点名称",
          "address": "详细地址",
          "location": {"longitude": 116.397128, "latitude": 39.916527},
          "visit_duration": 120,
          "description": "景点详细描述",
          "category": "景点类别",
          "ticket_price": 60
        }
      ],
      "meals": [
        {"type": "breakfast", "name": "早餐推荐", "description": "早餐描述", "estimated_cost": 30},
        {"type": "lunch", "name": "午餐推荐", "description": "午餐描述", "estimated_cost": 50},
        {"type": "dinner", "name": "晚餐推荐", "description": "晚餐描述", "estimated_cost": 80}
      ]
    }
  ],
  "weather_info": [
    {
      "date": "YYYY-MM-DD",
      "day_weather": "晴",
      "night_weather": "多云",
      "day_temp": 25,
      "night_temp": 15,
      "wind_direction": "南风",
      "wind_power": "1-3级"
    }
  ],
  "overall_suggestions": "总体建议",
  "budget": {
    "total_attractions": 180,
    "total_hotels": 1200,
    "total_meals": 480,
    "total_transportation": 200,
    "total": 2060
  }
}
```

**重要提示:**
1. weather_info数组必须包含每一天的天气信息
2. 温度必须是纯数字(不要带°C等单位)
3. 每天安排2-3个景点
4. 考虑景点之间的距离和游览时间
5. 每天必须包含早中晚三餐
6. 提供实用的旅行建议
7. **必须包含预算信息**:
   - 景点门票价格(ticket_price)
   - 餐饮预估费用(estimated_cost)
   - 酒店预估费用(estimated_cost)
   - 预算汇总(budget)包含各项总费用"""

class MultiAgentTripPlanner:
    """多智能体旅行规划系统"""

    def __init__(self, llm, tools: list):
        try:
            self.llm = llm
            self.tools = tools
            self.tool_names = [tool.name for tool in tools]

            # 创建景点搜索Agent
            print("  - 创建景点搜索Agent...")
            self.attraction_agent = create_react_agent(
                model=self.llm,
                tools=self.tools,
                prompt=ATTRACTION_AGENT_PROMPT
            )

            # 创建天气查询Agent
            print("  - 创建天气查询Agent...")
            self.weather_agent = create_react_agent(
                model=self.llm,
                tools=self.tools,
                prompt=WEATHER_AGENT_PROMPT
            )

            # 创建酒店推荐Agent
            print("  - 创建酒店推荐Agent...")
            self.hotel_agent = create_react_agent(
                model=self.llm,
                tools=self.tools,
                prompt=HOTEL_AGENT_PROMPT
            )

            print(f"✅ 多智能体系统初始化成功")
            print(f"   工具数量: {len(self.tools)}")
            print(f"   工具列表: {', '.join(self.tool_names)}")
        except Exception as e:
            print(f"❌ 多智能体系统初始化失败: {str(e)}")
            traceback.print_exc()
            raise

    def _invoke_agent(self, agent, query: str) -> str:
        """
        调用agent并提取响应文本

        Args:
            agnet: 智能体
            query: 用户查询

        Returns:
            Agent响应文本
        """
        result = agent.invoke({
            "messages": [HumanMessage(query)]
        })

        #提取最后一条消息的文本
        messages = result.get("messages", [])
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, "content"):
                return last_message.content
            return str(last_message)
        return str(result)

    def _invoke_planner(self, query: str) -> str:
        """
        调用行程规划agent

        Args:
            query: 包含所有信息的规划查询

        Returns:
            大模型响应文本
        """
        mesages = [
            SystemMessage(PLANNER_AGENT_PROMPT),
            HumanMessage(query)
        ]
        response = self.llm.invoke(mesages)
        return response.content

    def plan_trip(self, request: TripRequest) -> TripPlan:
        """
        使用多智能体写作生成旅行计划

        Args:
            request: 旅行请求

        Returns:
            旅行计划
        """

        try:
            print(f"\n{'=' * 60}")
            print(f"🚀 开始多智能体协作规划旅行 (LangChain)...")



            # 步骤1: 景点搜索Agent搜索景点
            print("📍 步骤1: 搜索景点...")
            attraction_query = self.build_attraction_query(request)
            attraction_response = self._invoke_agent(self.attraction_agent, attraction_query)
            print(f"景点搜索结果: {attraction_response[:200]}...\n")

            # 步骤2: 天气查询Agent查询天气
            print("🌤️  步骤2: 查询天气...")
            weather_query = f"请查询{request.city}的天气信息"
            weather_response = self._invoke_planner(self.weather_agent, weather_query)
            print(f"天气查询结果: {weather_response[:200]}...\n")

            # 步骤3: 酒店推荐Agent搜索酒店
            print("🏨 步骤3: 搜索酒店...")
            hotel_query = f"请搜索{request.city}的{request.accommodation}酒店"
            hotel_response = self._invoke_agent(self.hotel_agent, hotel_query)
            print(f"酒店搜索结果: {hotel_response[:200]}...\n")

            # 步骤4: 行程规划Agent整合信息生成计划
            print("📋 步骤4: 生成行程计划...")
            planner_query = self.build_planner_query(request, attraction_response, weather_response, hotel_response)
            planner_response = self._invoke_planner(planner_query, planner_query)
            print(f"行程规划结果: {planner_response[:300]}...\n")

            # 解析最终计划
            trip_plan = self._parse_response(planner_response, request)

            print(f"{'=' * 60}")
            print(f"✅ 旅行计划生成完成!")
            print(f"{'=' * 60}\n")

            return trip_plan
        except Exception as e:
            print(f"❌ 生成旅行计划失败: {str(e)}")
            traceback.print_exc()
            return self._create_fallback_plan(request)


    def _build_attraction_query(self, request: TripRequest) -> str:
        """构建景点搜索查询"""
        keyword = request.preference[0] if request.preference else "景点"
        return f"请搜索{request.city}的{keyword}相关景点"

    def _build_planner_query(self, request: TripRequest, attractions: str, weather: str, hotels: str = "") -> str:
        """构建行程规划查询"""
        query = f"""请根据以下信息生成{request.city}的{request.travel_days}天旅行计划:

**基本信息:**
- 城市: {request.city}
- 日期: {request.start_date} 至 {request.end_date}
- 天数: {request.travel_days}天
- 交通方式: {request.transportation}
- 住宿: {request.accommodation}
- 偏好: {', '.join(request.preferences) if request.preferences else '无'}

**景点信息:**
{attractions}

**天气信息:**
{weather}

**酒店信息:**
{hotels}

**要求:**
1. 每天安排2-3个景点
2. 每天必须包含早中晚三餐
3. 每天推荐一个具体的酒店(从酒店信息中选择)
4. 考虑景点之间的距离和交通方式
5. 返回完整的JSON格式数据
6. 景点的经纬度坐标要真实准确
"""
        if request.free_text_input:
            query += f"\n**额外要求:** {request.free_text_input}"
        return query

    def _parse_response(self, response: str, request: TripRequest) -> TripPlan:
        """
        解析agent响应

        Args:
            response: agent响应文本
            request: 原始请求

        Returns:
            旅行计划
        """

        try:
            # 尝试从响应中提取json
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
            else:
                raise ValueError("响应中未找到JSON数据")

            data = json.loads(json_str)
            trip_plan = TripPlan(**data)
            return trip_plan
        except Exception as e:
            print(f"⚠️  解析响应失败: {str(e)}")
            print(f"   将使用备用方案生成计划")
            return self._create_fallback_plan(request)

    def _create_fallback_plan(self, request: TripRequest) -> TripPlan:
        """创建备用计划（当agent调用失败时）"""
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")

        days = []
        for i in range(request.travel_days):
            current_date = start_date + timedelta(days=i)

            day_plan = DayPlan(
                date=current_date.strftime("%Y-%m-%d"),
                day_index=i,
                description=f"第{i+1}天行程",
                transportation=request.transportation,
                accommodation=request.accommodation,
                attractions=[
                    Attraction(
                        name=f"{request.city}景点{j+1}",
                        address=f"{request.city}市",
                        location=Location(
                            longitude=116.4 + i*0.01 + j*0.005,
                            latitude=39.9 + i*0.01 + j*0.005
                        ),
                        visit_duration=120,
                        description=f"这是{request.city}的著名景点",
                        category="景点"
                    )
                    for j in range(2)
                ],
                meals=[
                    Meal(type="breakfast", name=f"第{i+1}天早餐", description="当地特色早餐"),
                    Meal(type="lunch", name=f"第{i+1}天午餐", description="午餐推荐"),
                    Meal(type="dinner", name=f"第{i+1}天晚餐", description="晚餐推荐")
                ]
            )
            days.append(day_plan)

        return TripPlan(
            city=request.city,
            start_date=request.start_date,
            end_date=request.end_date,
            days=days,
            weather_info=[],
            overall_suggestions=f"这是为您规划的{request.city}{request.travel_days}日游行程，建议提前查看各景点的开放时间。"
        )

# ============ 全局实例管理 ============
_planner: Optional[MultiAgentTripPlanner] = None

async def init_trip_planner():
    """初始化全局旅行规划系统"""
    global _planner
    if _planner is not None:
        return _planner

    # 1.获取共享的MCP工具
    tools = get_mcp_tools_list()
    if not tools:
        tools = await init_mcp_client()

    # 2.获取LLM实例
    llm = get_llm()

    # 3.创建规划器
    _planner = MultiAgentTripPlanner(tools=tools, llm=llm)
    return _planner

def get_trip_planner_agent() -> MultiAgentTripPlanner:
    """获取多智能体旅行规划系统实例"""
    if _planner is None:
        raise RuntimeError("旅行规划系统尚未初始化。请确保在FastAPI startup事件中调用了init_trip_planner()")
    return _planner

def get_planner_info() -> dict:
    """获取规划器信息"""
    if _planner is None:
        return {"initialized": False}
    return {
        "initialized": True,
        "tools_count": len(_planner.tools),
        "tool_names": _planner.tool_names,
    }