"""novelai_image WebUI 应用。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import HTMLResponse, JSONResponse
import uvicorn


def create_app() -> Starlette:
    """创建 WebUI 应用。"""
    from .webui_logic import generate_image_api, get_config_api

    async def homepage(request) -> HTMLResponse:
        """返回 WebUI 页面。"""
        html_path = Path(__file__).parent / "webui" / "index.html"
        if html_path.exists():
            return HTMLResponse(html_path.read_text(encoding="utf-8"))
        return HTMLResponse("<h1>NovelAI Image WebUI</h1><p>HTML file not found</p>")

    routes = [
        Route("/", homepage),
        Route("/api/config", get_config_api),
        Route("/api/generate", generate_image_api),
    ]

    app = Starlette(routes=routes)
    return app
