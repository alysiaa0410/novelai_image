# NovelAI Image 插件

基于 NovelAI 文生图插件，支持自定义 API Key 和 URL（因为满月月实在是用不了77和不到人的生图插件所以自己手搓了一个）

## 功能特性

- 支持 NovelAI 官方 API 及第三方中转服务（建议还是去整个官方账号，我觉得还是很方便其实）
- 可配置的 API Key 和 API URL
- 多种模型支持 (nai-diffusion-4.5, nai-diffusion-3 等)
- 灵活的生图参数配置
- WebUI 配置面板
- 图片本地缓存

## 文件结构

```
novelai_image/
├── manifest.json      # 插件清单
├── plugin.py          # 插件入口
├── config.py          # 配置类
├── service.py         # 核心服务
├── action.py          # Action组件
├── router.py          # WebUI路由
├── webui_app.py       # WebUI应用
├── webui_logic.py     # WebUI逻辑
└── webui/
    └── index.html     # WebUI页面
```

## 配置项说明

在 `config/plugins/novelai_image/config.toml` 中配置：

```toml
[plugin]
enabled = true

[api]
base_url = "https://api.novelai.net"
api_key = "your_api_key_here"（对的把pst开头的key填在这里）
model = "nai-diffusion-4-5-full"
timeout = 120.0

[generation]
default_prompt = "1girl, high quality"
default_negative = "lowres, bad quality, watermark"
width = 832
height = 1216
steps = 28
scale = 5.0
sampler = "k_euler_ancestral"

[storage]
cache_dir = "data/media_cache/images/novelai_image"
max_cache = 100

[webui]
mount_on_main_http = true
route_path = "/plugins/novelai-image"
```

## 获取 API Key

1. 访问 [https://novelai.net](https://novelai.net) 登录账号
2. 进入 Settings -> API Access
3. 复制你的 API Token（获得apiky需要会员可以去拼车一个还不算太贵）

## 第三方中转服务

如果使用第三方中转服务，只需修改 `base_url`：

- **官方 API**: `https://api.novelai.net`
- **中转服务**: `https://your-gateway.example.com`

## 采样器选项

| 采样器 | 说明 |
|--------|------|
| `k_euler_ancestral` | 推荐，速度与质量平衡 |
| `k_euler` | 快速稳定 |
| `k_dpmpp_2m` | 高质量 |
| `ddim` | 精细控制 |

## 依赖

- httpx
