import json
import re
from typing import Optional, List, Dict, Any

from fastmcp import Client

from app.config import get_settings
from app.models.schemas import POIInfo, WeatherInfo, RouteInfo, Location

# 全局MCP客户端实例
_mcp_client: Optional[Client] = None
_mcp_tools: list[str] = []

def _get_mcp_config() -> dict:
    """获取MCP服务器配置"""
    settings = get_settings()

    if not settings.amap_api_key:
        raise ValueError("高德地图API Key未配置,请在.env文件中设置AMAP_API_KEY")

    return{
        "macServers": {
            "amap": {
                "command": "uvx",
                "agrs": ["amap-mcp-server"],
                "env": {"AMAP_MAPS_API_KEY": settings.amap_api_key}
            }
        }
    }

async def init_mcp_client() -> Client:
    """
    初始化MCP客户端

    Returns:
         已连接fastmcp Client实例
    """
    global _mcp_client, _mcp_tools

    if _mcp_client is None:
        config = _get_mcp_config()
        _mcp_client = Client(config)
        await _mcp_client.__aenter__()

        # 获取可用工具列表
        tools = await _mcp_client.list_tools()
        _mcp_tools = [tool.name for tool in tools]

        print(f"✅ 高德地图MCP客户端初始化成功")
        print(f"   工具数量: {len(_mcp_tools)}")
        print(f"   可用工具: {', '.join(_mcp_tools[:5])}")
        if len(_mcp_tools) > 5:
            print(f"   ... 还有 {len(_mcp_tools) - 5} 个工具")

    return _mcp_client


async def close_mcp_client():
    """关闭MCP客户端"""
    global _mcp_client, _mcp_tools
    if _mcp_client is not None:
        await _mcp_client.__aexit__(None, None, None)
        _mcp_client = None
        _mcp_tools = []
        print("👋 高德地图MCP客户端已关闭")


def get_mcp_tools_list() -> List[str]:
    """获取可用工具名称"""
    return _mcp_tools.copy()


class AmapService:
    """高德地图服务封装类"""

    def __init__(self):
        self.client = _mcp_client()

    async def _call_tool(self, tool_name: str, arguments: dict) -> str:
        """
        调用MCP工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具返回的文本结果
        """
        if self.client is None:
            raise RuntimeError("MCP客户端未初始化,请先调用init_mcp_client()")

        result = await self.client.call_tool(tool_name, arguments)

        if result and hasattr(result[0], 'text'):
            return result[0].text
        return str(result)

    async def search_poi(self, keywords: str, city: str, citylimit: bool = True) -> List[POIInfo]:
        """
        搜索POI

        Args:
            keywords: 搜索关键词
            city: 城市
            citylimit: 是否限制在城市范围内

        Returns:
            POI信息列表
        """
        try:
            result = await self._call_tool("maps_text_search",{
                "keywords": keywords,
                "city": city,
                "citylimit": str(citylimit).lower()
            })

            print(f"POI搜索结果：{result[:200]}...")

            # TODO： 解析实际的POI数据
            return []
        except Exception as e:
            print(f"❌ POI搜索失败: {str(e)}")
            return []


    async def get_weather(self, city: str) -> List[WeatherInfo]:
        """
        查询天气

        Args:
            city: 城市名称

        Returns:
            天气信息列表
        """
        try:
            result = await self._call_tool("maps_weather",{
                "city": city
            })
            print(f"天气查询结果: {result[:200]}...")
            # TODO： 解析实际的天气数据
            return []
        except Exception as e:
            print(f"❌ 天气查询失败: {str(e)}")
            return []


    async def plan_route(self, origin_address: str,
                         destination_address: str,
                         origin_city: Optional[str] = None,
                         destination_city: Optional[str] = None,
                         route_type: str = "walking") -> List[RouteInfo]:
        """
        规划路线

        Args:
            origin_address: 起点地址
            destination_address: 终点地址
            origin_city: 起点城市
            destination_city: 终点城市
            route_type: 路线类型 (walking/driving/transit)

        Returns:
            路线信息
        """
        try:
            tool_map = {
                "walking": "maps_direction_walking_by_address",
                "driving": "maps_direction_driving_by_address",
                "transit": "maps_direction_transit_integrated_by_address"
            }
            tool_name = tool_map.get(route_type, "maps_direction_walking_by_address")

            arguments = {
                "origin_address": origin_address,
                "destination_address": destination_address,
            }

            if origin_city:
                arguments["origin_city"] = origin_city
            if destination_city:
                arguments["destination_city"] = destination_city

            result = await self._call_tool(tool_name, arguments)

            print(f"路线规划结果: {result[:200]}...")

             # TODO: 解析实际的路线数据
            return {}

        except Exception as e:
            print(f"❌ 路线规划失败: {str(e)}")
            return {}


    async def geocode(self, address: str, city: Optional[str] = None) -> Optional[Location]:
        """
        地理编码（地理转坐标）

        Args:
            address: 地址
            city: 城市

        Returns:
            经纬度坐标
        """
        try:
            arguments = {"address": address}
            if city:
                arguments["city"] = city
            result = await self._call_tool("maps_geo", arguments)
            print(f"地理编码结果: {result[:200]}...")

            # TODO: 解析实际的坐标数据
            return None

        except Exception as e:
            print(f"❌ 地理编码失败: {str(e)}")
            return None


    async def get_poi_detail(self, poi_id: str) -> Dict[str, Any]:
        """
        获取POI详情

        Args:
            poi_id: POI ID

        Returns:
            POI详情信息
        """
        try:
            result = await self._call_tool("maps_search_detail", {"id": poi_id})
            print(f"POI详情结果: {result[:200]}...")

            # 尝试从结果中提取JSON
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data

            return {"raw": result}

        except Exception as e:
            print(f"❌ 获取POI详情失败: {str(e)}")
            return {}


# 创建全局服务实例
_amap_service = None

def get_amap_service() -> AmapService:
    """获取高德地图服务实例"""
    global _amap_service

    if _amap_service is None:
        _amap_service = AmapService()

    return _amap_service