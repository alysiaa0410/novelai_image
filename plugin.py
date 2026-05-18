"""novelai_image 插件入口。

提供 NovelAI 文生图功能，支持自定义 API Key 和 URL。
"""

from __future__ import annotations

import os

from src.app.plugin_system.base import BasePlugin, register_plugin
from src.kernel.logger import get_logger

from .action import GenerateImageAction
from .config import NovelAIImageConfig
from .router import NovelAIImageWebUIRouter
from .service import NovelAIImageService

logger = get_logger("novelai_image")


@register_plugin
class NovelAIImagePlugin(BasePlugin):
    """NovelAI Image 插件。"""

    plugin_name: str = "novelai_image"
    plugin_description: str = "NovelAI 文生图插件 - 支持自定义 API Key 和 URL"
    plugin_version: str = "1.0.0"

    configs: list[type] = [NovelAIImageConfig]
    dependent_components: list[str] = []

    def get_components(self) -> list[type]:
        """返回插件提供的组件类列表。"""
        config = self.config if isinstance(self.config, NovelAIImageConfig) else None
        if config is not None and not config.plugin.enabled:
            return []

        components: list[type] = [NovelAIImageService, GenerateImageAction]
        if config is not None and config.webui.mount_on_main_http:
            components.append(NovelAIImageWebUIRouter)
        return components

    async def on_plugin_loaded(self) -> None:
        """插件加载时确保缓存目录存在。"""
        if isinstance(self.config, NovelAIImageConfig) and not self.config.plugin.enabled:
            logger.info("novelai_image 已通过配置禁用")
            return

        if isinstance(self.config, NovelAIImageConfig):
            cache_dir = self.config.storage.cache_dir
            os.makedirs(cache_dir, exist_ok=True)
            logger.debug(f"novelai_image 缓存目录已确认: {cache_dir}")

    async def on_plugin_unloaded(self) -> None:
        """插件卸载时清理资源。"""
        logger.debug("novelai_image 插件已卸载")
