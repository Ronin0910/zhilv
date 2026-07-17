"""POI相关路由"""
import base64
from typing import Optional

import httpx
from fastapi import HTTPException, APIRouter
from pydantic import BaseModel

from app.services.amap_service import get_amap_service
from app.services.unsplash_service import get_unsplash_service

router = APIRouter(prefix="/poi", tags=["POI"])

class POIDetailResponse(BaseModel):
    """POI详情响应"""
    success: bool
    message: str
    data: Optional[dict] = None


@router.get(
    "/detail/{poi_id}",
    response_model=POIDetailResponse,
    summary="获取POI详情",
    description="根据POI ID获取详细信息,包括图片"
)
async def get_poi_detail(poi_id: str):
    """
    获取POI详情

    Args:
        poi_id: POI ID

    Returns:
        POI详情响应
    """
    try:
        amap_service = get_amap_service()
        result = await amap_service.get_poi_detail(poi_id)

        return POIDetailResponse(
            success=True,
            message="获取POI详情成功",
            data=result
        )

    except Exception as e:
        print(f"❌ 获取POI详情失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取POI详情失败: {str(e)}"
        )


@router.get(
    "/search",
    summary="搜索POI",
    description="根据关键词搜索POI"
)
async def search_poi(keywords: str, city: str = "北京"):
    """
    搜索POI

    Args:
        keywords: 搜索关键词
        city: 城市名称

    Returns:
        搜索结果
    """
    try:
        amap_service = get_amap_service()
        result = await amap_service.search_poi(keywords, city)

        return POIDetailResponse(
            success=True,
            message="搜索成功",
            data=result
        )

    except Exception as e:
        print(f"❌ 搜索POI失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"搜索POI失败: {str(e)}"
        )


@router.get(
    "/photo",
    summary="获取景点图片",
    description="优先从高德地图POI获取图片，失败时回退到Unsplash"
)
async def get_attraction_photo(name: str, city: str = ""):
    """
    获取景点图片（高德优先，Unsplash兜底）

    Args:
        name: 景点名称
        city: 城市名称（可选，提高高德搜索精度）

    Returns:
        图片URL
    """
    try:
        photo_url = None

        # 1. 优先从高德地图POI搜索获取图片
        if city:
            try:
                amap_service = get_amap_service()
                pois = await amap_service.search_poi_rest(name, city)
                if pois and pois[0].photos:
                    photo_url = pois[0].photos[0]
            except Exception as e:
                print(f"⚠️ 高德POI搜索图片失败，回退到Unsplash: {str(e)}")

        # 2. 高德没有结果时，回退到Unsplash
        if not photo_url:
            unsplash_service = get_unsplash_service()
            photo_url = unsplash_service.get_photo_url(f"{name} China landmark")
            if not photo_url:
                photo_url = unsplash_service.get_photo_url(name)

        return {
            "success": True,
            "message": "获取图片成功",
            "data": {
                "name": name,
                "photo_url": photo_url
            }
        }

    except Exception as e:
        print(f"❌ 获取景点图片失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取景点图片失败: {str(e)}"
        )


@router.get(
    "/proxy-image",
    summary="图片代理",
    description="服务端获取外部图片并返回 base64，解决前端跨域问题"
)
async def proxy_image(url: str):
    """
    代理获取外部图片，返回 base64 data URL

    Args:
        url: 图片的完整 URL

    Returns:
        base64 编码的图片数据
    """
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "image/jpeg")
            b64 = base64.b64encode(resp.content).decode()
            return {
                "success": True,
                "data": {
                    "data_url": f"data:{content_type};base64,{b64}"
                }
            }
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "data": {"data_url": None}
        }
