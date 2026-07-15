import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from app.config import get_settings
from app.models.schemas import POIInfo, WeatherInfo, RouteInfo, Location


def _find_uvx() -> str:
    """查找 uvx 可执行文件路径"""
    # 直接从当前 Python 环境的 Scripts 目录获取
    uvx_path = Path(sys.executable).parent / "Scripts" / "uvx.exe"
    if uvx_path.exists():
        return str(uvx_path)
    return "uvx"


# 全局MCP客户端实例
_mcp_client: Optional[MultiServerMCPClient] = None
_mcp_tools: list[BaseTool] = []
_mcp_initialized: bool = False

async def init_mcp_client() -> list:
    """
    初始化MCP客户端

    Returns:
         Langchain BaseTool列表
    """
    global _mcp_client, _mcp_tools, _mcp_initialized

    if _mcp_initialized:
        return _mcp_tools
    _mcp_initialized = True

    settings = get_settings()

    if not settings.amap_api_key:
        raise ValueError("高德地图API Key未配置，请在.env文件中设置AMAP_API_KEY")

    # 创建MCP客户端配置
    uvx_cmd = _find_uvx()
    print(f"  uvx路径: {uvx_cmd}")
    mcp_config = {
        "amap": {
            "command": uvx_cmd,
            "args": ["amap-mcp-server"],
            "env": {"AMAP_MAPS_API_KEY": settings.amap_api_key},
            "transport": "stdio"
        }
    }

    try:
        _mcp_client = MultiServerMCPClient(mcp_config)
        _mcp_tools = await _mcp_client.get_tools()

        print(f"✅ MCP工具加载成功")
        print(f"   工具数量: {len(_mcp_tools)}")
        for tool in _mcp_tools:
            print(f"     - {tool.name}")
    except Exception as e:
        print(f"⚠️  MCP工具初始化失败: {e}")
        _mcp_client = None
        _mcp_tools = []

    return _mcp_tools



async def close_mcp_client():
    """关闭MCP客户端"""
    global _mcp_client, _mcp_tools, _mcp_initialized
    if _mcp_client is not None:
        # langchain-mcp-adapters 0.1.0+ 不再支持 context manager
        # 只需清理引用即可
        _mcp_client = None
        _mcp_tools = []
        _mcp_initialized = False
        print("👋 高德地图MCP客户端已关闭")


def get_mcp_tools_list() -> List[BaseTool]:
    """获取可用工具列表"""
    return _mcp_tools.copy() if _mcp_tools else []

def _find_tool(name: str) -> Optional[BaseTool]:
    """按名称查找工具"""
    for tool in _mcp_tools:
        if tool.name == name:
            return tool
    return None


# ============ 确定性JSON解析工具函数 ============

def _extract_json(text: str) -> Optional[dict]:
    """
    从MCP返回的文本中提取JSON对象。
    处理三种情况：纯JSON、```json代码块、文本中嵌入的JSON。

    Args:
        text: MCP返回的原始文本

    Returns:
        解析后的dict，失败返回None
    """
    if not text or not isinstance(text, str):
        return None

    text = text.strip()

    # 1. 尝试直接解析
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass

    # 2. 尝试从 ```json ... ``` 代码块中提取
    code_block = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if code_block:
        try:
            return json.loads(code_block.group(1))
        except (json.JSONDecodeError, TypeError):
            pass

    # 3. 尝试提取文本中第一个完整的JSON对象（贪婪匹配最外层花括号）
    brace_match = re.search(r'\{.*\}', text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except (json.JSONDecodeError, TypeError):
            pass

    return None


def _parse_location(loc_str: str) -> Optional[Location]:
    """
    解析高德坐标字符串 "lng,lat" 为 Location 对象

    Args:
        loc_str: 坐标字符串，格式 "116.397428,39.90923"

    Returns:
        Location 对象，失败返回 None
    """
    if not loc_str or not isinstance(loc_str, str):
        return None
    parts = loc_str.strip().split(',')
    if len(parts) == 2:
        try:
            lng, lat = float(parts[0]), float(parts[1])
            if -180 <= lng <= 180 and -90 <= lat <= 90:
                return Location(longitude=lng, latitude=lat)
        except (ValueError, TypeError):
            pass
    return None


def _safe_float(val: Any, default: float = 0.0) -> float:
    """安全转换为float"""
    if val is None:
        return default
    try:
        # 移除可能的单位后缀
        if isinstance(val, str):
            val = val.replace('米', '').replace('秒', '').replace('分钟', '').strip()
        return float(val)
    except (ValueError, TypeError):
        return default


def _safe_int(val: Any, default: int = 0) -> int:
    """安全转换为int"""
    if val is None:
        return default
    try:
        if isinstance(val, str):
            val = val.replace('米', '').replace('秒', '').replace('分钟', '').strip()
        return int(float(val))
    except (ValueError, TypeError):
        return default

class AmapService:
    """高德地图服务封装类"""

    def __init__(self):
        global _mcp_client
        self.client = _mcp_client

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

            data = _extract_json(result)
            if not data:
                return []

            pois = []
            # 高德API返回格式: {"pois": [{"id":"...", "name":"...", "type":"...", "address":"...", "location":"lng,lat", "tel":"..."}]}
            raw_pois = data.get("pois", [])
            if not isinstance(raw_pois, list):
                return []

            for item in raw_pois:
                if not isinstance(item, dict):
                    continue
                loc = _parse_location(item.get("location", ""))
                if loc:
                    pois.append(POIInfo(
                        id=str(item.get("id", "")),
                        name=str(item.get("name", "")),
                        type=str(item.get("type", "")),
                        address=str(item.get("address", "")),
                        location=loc,
                        tel=item.get("tel") or None,
                    ))
            return pois
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
            data = _extract_json(result)
            if not data:
                return []

            weather_list = []
            # 高德API返回格式: {"forecasts": [{"date":"...", "dayweather":"晴", "nightweather":"多云", "daytemp":"30", "nighttemp":"20", "daywind":"东南", "daypower":"3-4"}]}
            raw_forecasts = data.get("forecasts", [])
            if not isinstance(raw_forecasts, list):
                return []

            for item in raw_forecasts:
                if not isinstance(item, dict):
                    continue
                weather_list.append(WeatherInfo(
                    date=str(item.get("date", "")),
                    day_weather=str(item.get("dayweather", "")),
                    night_weather=str(item.get("nightweather", "")),
                    day_temp=_safe_int(item.get("daytemp", 0)),
                    night_temp=_safe_int(item.get("nighttemp", 0)),
                    wind_direction=str(item.get("daywind", "")),
                    wind_power=str(item.get("daypower", "")),
                ))
            return weather_list
        except Exception as e:
            print(f"❌ 天气查询失败: {str(e)}")
            return []


    async def plan_route(self, origin_address: str,
                         destination_address: str,
                         origin_city: Optional[str] = None,
                         destination_city: Optional[str] = None,
                         route_type: str = "walking") -> Optional[RouteInfo]:
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

            data = _extract_json(result)
            if not data:
                return None

            route = data.get("route", {})

            if route_type == "transit":
                # 公交路线: {"route": {"transits": [{"distance":"...", "duration":"...", "segments":[...]}]}}
                transits = route.get("transits", [])
                if isinstance(transits, list) and transits:
                    t = transits[0]
                    dist = _safe_float(t.get("distance", 0))
                    dur = _safe_int(t.get("duration", 0))
                    return RouteInfo(
                        distance=dist,
                        duration=dur,
                        route_type=route_type,
                        description=f"公交路线，距离{dist}米，预计{dur // 60}分钟",
                    )
            else:
                # 步行/驾车: {"route": {"paths": [{"distance":"...", "duration":"...", "steps":[...]}]}}
                paths = route.get("paths", [])
                if isinstance(paths, list) and paths:
                    p = paths[0]
                    dist = _safe_float(p.get("distance", 0))
                    dur = _safe_int(p.get("duration", 0))

                    # 提取路线步骤描述
                    steps_desc = ""
                    steps = p.get("steps", [])
                    if isinstance(steps, list):
                        step_names = [
                            s.get("instruction", "")
                            for s in steps[:5]
                            if isinstance(s, dict) and s.get("instruction")
                        ]
                        steps_desc = " → ".join(step_names)

                    return RouteInfo(
                        distance=dist,
                        duration=dur,
                        route_type=route_type,
                        description=steps_desc or f"距离{dist}米，预计{dur // 60}分钟",
                    )

            return None

        except Exception as e:
            print(f"❌ 路线规划失败: {str(e)}")
            return None


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
            data = _extract_json(result)
            if not data:
                return None

            # 高德API返回格式: {"geocodes": [{"formatted_address":"...", "location":"lng,lat"}]}
            geocodes = data.get("geocodes", [])
            if isinstance(geocodes, list) and geocodes:
                return _parse_location(geocodes[0].get("location", ""))

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