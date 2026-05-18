"""novelai_image Action：生图并发送。"""

from __future__ import annotations

from typing import Annotated, cast

from src.app.plugin_system.api.send_api import send_image
from src.app.plugin_system.api.service_api import get_service
from src.app.plugin_system.base import BaseAction
from src.kernel.logger import get_logger

from .config import NovelAIImageConfig
from .service import NovelAIImageService

logger = get_logger("novelai_image")


class GenerateImageAction(BaseAction):
    """生成图片 Action。"""

    action_name: str = "generate_image"
    dependencies: list[str] = ["novelai_image:service:novelai_image"]
    action_description: str = """
生图规则

触发条件：
- 用户明确要求生成图片
- 用户发送绘图相关的请求

参数说明：
- prompt: 正向提示词，描述想要生成的画面
- negative_prompt: 负向提示词，描述不想出现的内容（可选）

生成约束：
- 使用配置中的默认参数
- 图片会自动发送到当前对话
"""
    primary_action: bool = True

    async def go_activate(self) -> bool:
        """检查插件是否启用。"""
        config = self.plugin.config
        if isinstance(config, NovelAIImageConfig) and not config.plugin.enabled:
            return False
        return True

    async def execute(
        self,
        prompt: Annotated[str, "正向提示词，描述想要生成的画面"],
        negative_prompt: Annotated[str | None, "负向提示词（可选）"] = None,
    ) -> tuple[bool, str]:
        """执行生图并发送。

        Args:
            prompt: 正向提示词
            negative_prompt: 负向提示词

        Returns:
            (成功标志, 结果说明)
        """
        service = get_service("novelai_image:service:novelai_image")
        if service is None:
            logger.warning("novelai_image service 未加载")
            return False, "novelai_image service 未加载"

        service = cast(NovelAIImageService, service)
        config = cast(NovelAIImageConfig, self.plugin.config)

        neg_prompt = negative_prompt if negative_prompt else config.generation.default_negative

        # 生成图片
        b64_image = await service.generate_image(
            prompt=prompt,
            negative_prompt=neg_prompt,
            config=config,
        )
        if b64_image is None:
            return False, "图片生成失败，请检查 API 配置"

        # 发送图片
        ok = await send_image(
            image_data=b64_image,
            stream_id=self.chat_stream.stream_id,
            platform=self.chat_stream.platform,
        )
        if not ok:
            return False, "图片发送失败"

        return True, "已发送图片"
