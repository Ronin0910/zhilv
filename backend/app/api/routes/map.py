"""地图服务API路由"""
from fastapi import APIRouter, Query, HTTPException

from app.models.schemas import POISearchResponse, WeatherResponse, RouteResponse, RouteRequest
from app.services.amap_service import get_amap_service, get_mcp_tools_list

router = APIRouter(prefix="/map", tags=["地图服务"])

@router.get("/poi",
            response_model=POISearchResponse,
            summary="搜索POI",
            description="根据关键词搜索POI（兴趣点）"
)
async def search_poi(
        keywords: str = Query(..., description="搜索关键词", examples="故宫"),
        city: str = Query(..., description="城市", examples="北京"),
        citylimit: bool = Query(True, description="是否限制在城市内")
):
    """
    搜索POI

    Args:
        keywords: 搜索关键词
        city: 城市
        citylimit: 是否限制在城市范围内

    Returns:
        POI搜索结果
    """
    try:
        service = get_amap_service()
        pois = await service.search_poi(keywords, city, citylimit)

        return POISearchResponse(
            success=True,
            message="POI搜索成功",
            data=pois
        )

    except Exception as e:
        print(f"❌ POI搜索失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"POI搜索失败: {str(e)}"
        )

@router.get(
    "/weather",
    response_model=WeatherResponse,
    summary="查询天气",
    description="查询指定城市的天气信息"
)
async def get_weather(city: str = Query(..., description="城市名称", examples="北京")):
    """
    查询天气

    Args:
        city: 城市名称

    Returns:
        天气信息
    """
    try:
        service = get_amap_service()
        weather_info = await service.get_weather(city)
        return WeatherResponse(
            success=True,
            message="天气查询成功",
            data=weather_info
        )

    except Exception as e:
        print(f"❌ 天气查询失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"天气查询失败: {str(e)}"
        )

@router.post(
    "/route",
    response_model=RouteResponse,
    summary = "路线规划",
    description="规划两点之间的距离"
)
async def plan_route(request: RouteRequest):
    """
    路线规划

    Args:
        request: 路线规划请求

    Returns:
        路线信息
    """

    try:
        service = get_amap_service()
        route_info = await service.plan_route(
            origin_address=request.origin_address,
            destination_address=request.destination_address,
            origin_city=request.origin_city,
            destination_city=request.destination_city,
            route_type=request.route_type
        )
        return RouteResponse(
            success=True,
            message="路线规划成功",
            data=[route_info] if route_info else []
        )

    except Exception as e:
        print(f"❌ 路线规划失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"路线规划失败: {str(e)}"
        )

@router.get(
    "/static-map",
    summary="获取静态地图图片",
    description="根据景点坐标生成静态地图图片URL"
)
async def get_static_map(
    locations: str = Query(..., description="景点坐标，格式: lng1,lat1|lng2,lat2|..."),
    names: str = Query("", description="景点名称，用|分隔"),
    zoom: int = Query(12, description="地图缩放级别")
):
    """
    获取静态地图图片URL

    Args:
        locations: 景点坐标字符串，用|分隔
        names: 景点名称字符串，用|分隔
        zoom: 地图缩放级别

    Returns:
        静态地图图片URL
    """
    try:
        from app.config import get_settings
        settings = get_settings()

        # 构建静态图URL
        base_url = "https://restapi.amap.com/v3/staticmap"

        # 构建markers参数
        location_list = locations.split("|")
        name_list = names.split("|") if names else []

        markers = []
        for i, loc in enumerate(location_list):
            name = name_list[i] if i < len(name_list) else str(i + 1)
            # 绿色标记，带编号
            markers.append(f"large,0x4CAF50,{i + 1}:{loc}")

        markers_str = "|".join(markers)

        # 计算中心点（所有坐标的平均值）
        lngs = []
        lats = []
        for loc in location_list:
            parts = loc.split(",")
            if len(parts) == 2:
                lngs.append(float(parts[0]))
                lats.append(float(parts[1]))

        center_lng = sum(lngs) / len(lngs) if lngs else 116.397128
        center_lat = sum(lats) / len(lats) if lats else 39.916527

        params = {
            "location": f"{center_lng},{center_lat}",
            "zoom": str(zoom),
            "size": "800*500",
            "markers": markers_str,
            "key": settings.amap_api_key
        }

        # 构建完整URL
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        static_map_url = f"{base_url}?{query_string}"

        return {
            "success": True,
            "message": "获取静态地图成功",
            "data": {
                "url": static_map_url,
                "center": {"longitude": center_lng, "latitude": center_lat},
                "zoom": zoom
            }
        }

    except Exception as e:
        print(f"❌ 获取静态地图失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取静态地图失败: {str(e)}"
        )


@router.get(
    "/health",
    summary="健康检查",
    description="检查地图服务是否正常"
)
async def health_check():
    """健康检查"""
    try:
        tools_list = get_mcp_tools_list()
        return {
            "status": "healthy",
            "service": "map-service",
            "mcp_tools_count": len(tools_list)
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"服务不可用: {str(e)}"
        )