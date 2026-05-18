"""novelai_image Service：调用 NovelAI API 生成图片。"""

from __future__ import annotations

import asyncio
import base64
import binascii
import io
import json
import os
import random
import time
import zipfile
from typing import TYPE_CHECKING, Any

import httpx

from src.app.plugin_system.base import BaseService
from src.kernel.logger import get_logger

if TYPE_CHECKING:
    from .config import NovelAIImageConfig

logger = get_logger("novelai_image")


def _build_image_payload(
    *,
    model: str,
    prompt: str,
    negative_prompt: str,
    width: int,
    height: int,
    steps: int,
    scale: float,
    sampler: str,
) -> dict[str, Any]:
    """构造 NovelAI 原生请求体。"""
    is_v4_model = "diffusion-4" in model

    parameters: dict[str, Any] = {
        "width": width,
        "height": height,
        "scale": scale,
        "steps": steps,
        "sampler": sampler,
        "seed": random.randint(0, 9_999_999_999),
        "n_samples": 1,
        "ucPreset": 1,
        "qualityToggle": False,
        "sm": False,
        "sm_dyn": False,
        "noise_schedule": "karras" if is_v4_model else "native",
    }

    if is_v4_model:
        parameters.update({
            "params_version": 3,
            "cfg_rescale": 0,
            "autoSmea": False,
            "legacy": False,
            "legacy_v3_extend": False,
            "legacy_uc": False,
            "add_original_image": True,
            "controlnet_strength": 1,
            "dynamic_thresholding": False,
            "prefer_brownian": True,
            "normalize_reference_strength_multiple": True,
            "use_coords": False,
            "inpaintImg2ImgStrength": 1,
            "deliberate_euler_ancestral_bug": False,
            "skip_cfg_above_sigma": None,
            "characterPrompts": [],
            "reference_image_multiple": [],
            "reference_information_extracted_multiple": [],
            "reference_strength_multiple": [],
        })
    else:
        parameters["negative_prompt"] = negative_prompt

    payload: dict[str, Any] = {
        "input": prompt,
        "model": model,
        "action": "generate",
        "parameters": parameters,
    }
    if is_v4_model:
        payload["use_new_shared_trial"] = True
    return payload


def _guess_image_format(image_bytes: bytes) -> str:
    """根据文件头猜测图片格式。"""
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if image_bytes.startswith(b"GIF87a") or image_bytes.startswith(b"GIF89a"):
        return "gif"
    if image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
        return "webp"
    return "png"


def _extract_image_from_response(raw_data: bytes) -> tuple[bytes, str] | None:
    """从 NovelAI 响应中提取图片。

    NovelAI 官方 API 返回的是 ZIP 压缩包，里面包含图片文件。
    也可能是直接返回的原始图片数据。

    Returns:
        (图片二进制数据, 格式) 或 None
    """
    if not raw_data:
        return None

    # 检查是否是 ZIP 压缩包
    if raw_data.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(io.BytesIO(raw_data)) as zf:
                # 查找第一个图片文件
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    image_data = zf.read(info.filename)
                    if not image_data:
                        continue
                    # 根据文件扩展名判断格式
                    ext = info.filename.lower()
                    if ext.endswith(".png"):
                        fmt = "png"
                    elif ext.endswith((".jpg", ".jpeg")):
                        fmt = "jpg"
                    elif ext.endswith(".gif"):
                        fmt = "gif"
                    elif ext.endswith(".webp"):
                        fmt = "webp"
                    else:
                        fmt = _guess_image_format(image_data)
                    return image_data, fmt
        except (zipfile.BadZipFile, KeyError, OSError):
            pass

    # 直接返回的图片数据
    return raw_data, _guess_image_format(raw_data)


class NovelAIImageService(BaseService):
    """NovelAI 图片生成核心 Service。"""

    service_name: str = "novelai_image"
    service_description: str = "通过 NovelAI API 生成图片"
    version: str = "1.0.0"

    async def generate_image(
        self,
        prompt: str,
        negative_prompt: str,
        config: "NovelAIImageConfig",
        width: int | None = None,
        height: int | None = None,
        steps: int | None = None,
        scale: float | None = None,
        sampler: str | None = None,
        model: str | None = None,
    ) -> str | None:
        """生成一张图片并返回 base64 字符串。

        Args:
            prompt: 正向提示词
            negative_prompt: 负向提示词
            config: 插件配置实例
            width: 图片宽度 (可选)
            height: 图片高度 (可选)
            steps: 采样步数 (可选)
            scale: 引导系数 (可选)
            sampler: 采样器 (可选)
            model: 模型名称 (可选)

        Returns:
            base64 编码的图片字符串；失败时返回 None
        """
        gen_config = config.generation

        width = width or gen_config.width
        height = height or gen_config.height
        steps = steps or gen_config.steps
        scale = scale or gen_config.scale
        sampler = sampler or gen_config.sampler
        model = model or config.api.model

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
            "Authorization": f"Bearer {config.api.api_key}",
        }
        url = f"{config.api.base_url.rstrip('/')}/ai/generate-image"

        try:
            async with httpx.AsyncClient(timeout=config.api.timeout) as client:
                resp = await client.post(url, json=payload, headers=headers)
                
                # 记录详细响应信息用于调试
                logger.debug(f"NovelAI API 响应状态码: {resp.status_code}")
                logger.debug(f"NovelAI API 响应内容前500字符: {resp.text[:500]}")

                if not resp.is_success:
                    logger.warning(f"NovelAI API 错误: {resp.status_code}, 响应: {resp.text[:500]}")
                    return None

                raw_data = resp.content
                if not raw_data:
                    logger.warning("NovelAI 返回了空响应")
                    return None

                # 从响应中提取图片（支持 ZIP 压缩包或直接返回的图片）
                image_result = _extract_image_from_response(raw_data)
                if image_result is None:
                    logger.warning("NovelAI 返回的数据无法解析为图片")
                    return None

                image_bytes, image_fmt = image_result
                b64_data = base64.b64encode(image_bytes).decode()
                self._save_cache(image_bytes, image_fmt, config)
                logger.debug(f"NovelAI 生图成功，格式={image_fmt}，大小={len(image_bytes)}字节")
                return b64_data

        except httpx.HTTPStatusError as e:
            logger.warning(f"NovelAI HTTP 错误: {e.response.status_code}, 内容: {e.response.text[:500]}")
            if e.response.status_code == 401:
                logger.warning("NovelAI API Key 无效或已过期")
            elif e.response.status_code == 400:
                logger.warning("请求参数错误，请检查 prompt 和模型配置")
            elif e.response.status_code == 429:
                logger.warning("NovelAI 请求过于频繁，请稍后重试")
            return None
        except httpx.RequestError as e:
            logger.warning(f"NovelAI 请求失败: {e}")
            return None

    def _save_cache(self, image_bytes: bytes, fmt: str, config: "NovelAIImageConfig") -> None:
        """将图片保存到本地缓存。"""
        cache_dir = config.storage.cache_dir
        os.makedirs(cache_dir, exist_ok=True)

        filename = f"{int(time.time() * 1000)}.{fmt}"
        filepath = os.path.join(cache_dir, filename)
        try:
            with open(filepath, "wb") as f:
                f.write(image_bytes)
        except OSError as e:
            logger.warning(f"NovelAI 缓存写入失败: {e}")
            return

        max_cache = config.storage.max_cache
        if max_cache <= 0:
            return

        try:
            all_files = sorted(
                (
                    os.path.join(cache_dir, fn)
                    for fn in os.listdir(cache_dir)
                    if os.path.isfile(os.path.join(cache_dir, fn))
                ),
                key=os.path.getmtime,
            )
            while len(all_files) > max_cache:
                oldest = all_files.pop(0)
                try:
                    os.remove(oldest)
                    logger.debug(f"NovelAI 缓存清理: {oldest}")
                except OSError:
                    pass
        except OSError as e:
            logger.warning(f"NovelAI 缓存清理失败: {e}")
