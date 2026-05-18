"""novelai_image WebUI 逻辑。"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse


def get_default_config() -> dict[str, Any]:
    """获取默认配置。"""
    return {
        "api": {
            "base_url": "https://api.novelai.net",
            "api_key": "",
            "model": "nai-diffusion-4-5-full",
        },
        "generation": {
            "default_prompt": "1girl, high quality",
            "default_negative": "lowres, bad quality, watermark",
            "width": 640,
            "height": 960,
            "steps": 28,
            "scale": 5.0,
            "sampler": "k_euler_ancestral",
        },
    }


async def get_config_api(request: Request) -> JSONResponse:
    """获取配置 API。"""
    return JSONResponse(get_default_config())


async def generate_image_api(request: Request) -> JSONResponse:
    """生图 API。"""
    try:
        body = await request.json()
        prompt = body.get("prompt", "")
        negative_prompt = body.get("negative_prompt", "")
        width = body.get("width", 832)
        height = body.get("height", 1216)
        steps = body.get("steps", 28)
        scale = body.get("scale", 5.0)
        sampler = body.get("sampler", "k_euler_ancestral")
        model = body.get("model", "nai-diffusion-4-5-full")
        api_key = body.get("api_key", "")
        base_url = body.get("base_url", "https://api.novelai.net")

        if not prompt:
            return JSONResponse({"error": "prompt is required"}, status_code=400)

        if not api_key:
            return JSONResponse({"error": "API key is required"}, status_code=400)

        # 导入并调用 service
        from .service import NovelAIImageService, _build_image_payload
        import httpx

        payload = _build_image_payload(
            model=model,
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            steps=steps,
            scale=scale,
            sampler=sampler,
        )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        url = f"{base_url.rstrip('/')}/ai/generate-image"

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            
            # 详细错误信息
            if not resp.is_success:
                error_detail = resp.text[:500] if resp.text else "No response body"
                return JSONResponse({
                    "error": f"API error {resp.status_code}: {error_detail}",
                    "debug": {
                        "url": url,
                        "model": model,
                        "prompt_length": len(prompt),
                    }
                }, status_code=resp.status_code)
            
            image_bytes = resp.content

        b64_image = base64.b64encode(image_bytes).decode()
        return JSONResponse({
            "success": True,
            "image": f"data:image/png;base64,{b64_image}",
        })

    except httpx.HTTPStatusError as e:
        return JSONResponse({
            "error": f"HTTP error {e.response.status_code}: {e.response.text[:300]}",
        }, status_code=e.response.status_code)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
