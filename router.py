"""novelai_image WebUI Router。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.app.plugin_system.base import BaseRouter
from src.kernel.logger import get_logger

from .config import NovelAIImageConfig
from .webui_app import create_app


logger = get_logger("novelai_image.router")


class NovelAIImageWebUIRouter(BaseRouter):
    """将 novelai_image WebUI 挂载到主程序 HTTP 服务器。"""

    router_name = "webui"
    router_description = "NovelAI Image WebUI"

    def __init__(self, plugin: Any) -> None:
        config = getattr(plugin, "config", None)
        if isinstance(config, NovelAIImageConfig):
            route_path = config.webui.route_path.strip()
            self.custom_route_path = route_path or "/plugins/novelai-image"
        self._sub_app = None
        super().__init__(plugin)

    def register_endpoints(self) -> None:
        """挂载现有 WebUI 子应用。"""
        self._sub_app = create_app()
        self.app.mount("/", self._sub_app)

    async def startup(self) -> None:
        """启动 WebUI。"""
        logger.info(f"novelai_image WebUI 已挂载到: {self.get_route_path()}")

    async def shutdown(self) -> None:
        """清理资源。"""
        pass
