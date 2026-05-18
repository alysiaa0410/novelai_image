"""novelai_image 插件配置。"""

from __future__ import annotations

from typing import ClassVar, Literal

from src.app.plugin_system.base import BaseConfig, Field, SectionBase, config_section


class NovelAIImageConfig(BaseConfig):
    """novelai_image 插件配置类。"""

    config_name: ClassVar[str] = "config"
    config_description: ClassVar[str] = "NovelAI 文生图插件配置"

    @config_section("plugin")
    class PluginSection(SectionBase):
        """插件全局开关。"""

        enabled: bool = Field(default=True, description="是否启用 NovelAI 生图功能")

    @config_section("api")
    class ApiSection(SectionBase):
        """NovelAI API 连接配置。"""

        base_url: str = Field(
            default="https://api.novelai.net",
            description="NovelAI API 基础地址。官方为 https://api.novelai.net，也可使用第三方中转服务",
        )
        api_key: str = Field(default="", description="NovelAI API Key (从 https://novelai.net 获取)")
        model: str = Field(default="nai-diffusion-4-5-full", description="要调用的 NAI 模型名称")
        timeout: float = Field(default=120.0, description="HTTP 请求超时时间（秒）")

    @config_section("generation")
    class GenerationSection(SectionBase):
        """生图参数预设。"""

        default_prompt: str = Field(
            default="1girl, high quality",
            description="默认正向提示词",
        )
        default_negative: str = Field(
            default="lowres, {bad}, {bad feet}, bad hands, error, fewer, extra, missing, worst quality, jpeg artifacts, bad quality, watermark",
            description="默认负向提示词",
        )
        width: int = Field(default=640, description="图片宽度（像素，需为 64 的倍数）")
        height: int = Field(default=960, description="图片高度（像素，需为 64 的倍数）")
        steps: int = Field(default=28, description="采样步数（1-50）")
        scale: float = Field(default=5.0, description="引导系数（1-15）")
        sampler: str = Field(default="k_euler_ancestral", description="采样器")

    @config_section("storage")
    class StorageSection(SectionBase):
        """本地缓存配置。"""

        cache_dir: str = Field(default="data/media_cache/images/novelai_image", description="生成图片的本地缓存目录")
        max_cache: int = Field(default=100, description="最多缓存的图片数量")

    @config_section("webui")
    class WebUISection(SectionBase):
        """WebUI 配置。"""

        mount_on_main_http: bool = Field(
            default=True,
            description="是否将 WebUI 挂载到主程序 HTTP 服务器",
        )
        route_path: str = Field(
            default="/plugins/novelai-image",
            description="挂载到主程序 HTTP 服务器时使用的子路径",
        )

    plugin: PluginSection = Field(default_factory=PluginSection)
    api: ApiSection = Field(default_factory=ApiSection)
    generation: GenerationSection = Field(default_factory=GenerationSection)
    storage: StorageSection = Field(default_factory=StorageSection)
    webui: WebUISection = Field(default_factory=WebUISection)
