# Vision MCP

一个基于 Python 的本地视觉分析 MCP 服务。它可以调用兼容 OpenAI
接口格式的视觉模型，帮助 Claude Desktop、Codex 等支持 MCP 的客户端读取
本地图片、联合分析多张图片，以及识别 PDF 页面内容。

## 主要能力

### `analyze_image`

分析一张本地图片。适用于图片内容描述、OCR 文字提取、截图排错、表格识别、
界面分析和图表解读等任务。

参数：

- `path`：图片文件的绝对路径。
- `prompt`：希望模型执行的分析任务，可选。

### `analyze_images`

一次联合分析多张本地图片。模型会在同一个请求中查看全部图片，因此可以用于
前后对比、连续截图理解、多页扫描件分析和跨图片信息汇总。

参数：

- `paths`：一个或多个图片文件的绝对路径列表。
- `prompt`：希望模型针对所有图片执行的分析任务，可选。

### `analyze_pdf`

把本地 PDF 的前几页渲染成图片，再交给视觉模型分析。适用于扫描版 PDF、
含复杂排版的文档、图文报告和普通文本提取工具难以处理的页面。

参数：

- `path`：PDF 文件的绝对路径。
- `prompt`：希望模型针对 PDF 页面执行的分析任务，可选。

默认只分析 PDF 前 3 页，可以通过 `VISION_PDF_MAX_PAGES` 调整，最多 20 页。

## 环境要求

- Python 3.10 或更高版本
- 一个支持视觉输入、兼容 OpenAI API 格式的模型服务
- Windows、macOS 或 Linux

## 安装

克隆仓库：

```powershell
git clone https://github.com/hpsyyds-sys/vision-mcp.git
cd vision-mcp
```

创建虚拟环境并安装依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

复制环境变量示例：

```powershell
Copy-Item .env.example .env
```

macOS 或 Linux 可以使用：

```bash
cp .env.example .env
```

然后编辑 `.env`：

```env
VISION_API_KEY=你的API密钥
VISION_BASE_URL=https://你的兼容接口地址/v1
VISION_MODEL=支持视觉输入的模型名称
VISION_TIMEOUT_SECONDS=60
VISION_MAX_IMAGE_SIDE=1600
VISION_PDF_MAX_PAGES=3
VISION_PDF_RENDER_DPI=200
```

## MCP 客户端配置

将下面配置中的路径替换为本机 `server.py` 的绝对路径：

```json
{
  "mcpServers": {
    "vision-mcp": {
      "command": "python",
      "args": ["C:\\绝对路径\\vision-mcp\\server.py"]
    }
  }
}
```

如果使用虚拟环境，建议直接指定虚拟环境中的 Python：

```json
{
  "mcpServers": {
    "vision-mcp": {
      "command": "C:\\绝对路径\\vision-mcp\\.venv\\Scripts\\python.exe",
      "args": ["C:\\绝对路径\\vision-mcp\\server.py"]
    }
  }
}
```

也可以不创建 `.env`，直接在 MCP 配置中传入环境变量：

```json
{
  "mcpServers": {
    "vision-mcp": {
      "command": "python",
      "args": ["C:\\绝对路径\\vision-mcp\\server.py"],
      "env": {
        "VISION_API_KEY": "你的API密钥",
        "VISION_BASE_URL": "https://你的兼容接口地址/v1",
        "VISION_MODEL": "支持视觉输入的模型名称"
      }
    }
  }
}
```

重启 MCP 客户端后，客户端应能看到 `analyze_image`、`analyze_images`
和 `analyze_pdf` 三个工具。

## 本地运行与测试

Windows 可直接运行：

```powershell
.\run_vision_mcp.ps1
```

也可以运行：

```powershell
python server.py
```

使用一张本地图片进行冒烟测试：

```powershell
python test_local.py "C:\path\to\image.png" --prompt "提取图片中的全部文字"
```

## 支持的格式

- 图片：`.jpg`、`.jpeg`、`.png`、`.webp`、`.bmp`
- 文档：`.pdf`

为了减少请求体积，过大的图片会按比例缩小，并统一转换为 JPEG 后发送给模型。
透明图片会自动使用白色背景。

## 配置说明

| 环境变量 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `VISION_API_KEY` | 是 | 无 | 模型服务的 API 密钥 |
| `VISION_BASE_URL` | 是 | 无 | 兼容 OpenAI 格式的 API 地址 |
| `VISION_MODEL` | 是 | 无 | 支持视觉输入的模型名称 |
| `VISION_TIMEOUT_SECONDS` | 否 | `60` | API 请求超时时间，单位为秒 |
| `VISION_MAX_IMAGE_SIDE` | 否 | `1600` | 图片最长边的最大像素数 |
| `VISION_PDF_MAX_PAGES` | 否 | `3` | 每次分析的 PDF 最大页数 |
| `VISION_PDF_RENDER_DPI` | 否 | `200` | PDF 页面渲染分辨率 |

## 注意事项

- 本项目不提供视觉模型或免费 API，需要使用者自行配置模型服务。
- 图片和 PDF 页面会发送到你配置的模型接口，请勿处理无权上传的敏感文件。
- PDF 通过视觉方式分析，不等同于专业 PDF 解析或 OCR 软件。
- 模型返回内容的准确性取决于所使用的模型、图片质量和提示词。
- `.env` 已被 Git 忽略，请勿把 API 密钥提交到公开仓库。

## 许可证

本仓库目前未附带开源许可证。在添加许可证之前，默认保留所有权利。
