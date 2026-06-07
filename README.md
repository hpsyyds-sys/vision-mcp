# vision-mcp

An MCP server for analyzing local images and PDF pages with an
OpenAI-compatible vision API.

## Tools

- `analyze_image`: Analyze one local image.
- `analyze_images`: Analyze multiple local images together.
- `analyze_pdf`: Render and analyze the first pages of a PDF.

## Requirements

- Python 3.10 or newer
- An OpenAI-compatible API endpoint with a vision-capable model

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and provide your API endpoint, key, and model name.

## Run

```powershell
.\run_vision_mcp.ps1
```

You can also run the server directly:

```powershell
python server.py
```

## MCP client configuration

Use an absolute path to `server.py`. For example:

```json
{
  "mcpServers": {
    "vision-mcp": {
      "command": "python",
      "args": ["C:\\absolute\\path\\to\\vision-mcp\\server.py"],
      "env": {
        "VISION_API_KEY": "your-api-key",
        "VISION_BASE_URL": "https://your-openai-compatible-endpoint/v1",
        "VISION_MODEL": "your-vision-model"
      }
    }
  }
}
```

Alternatively, keep these values in a local `.env` file beside `server.py`.
Never commit `.env` or API keys to GitHub.

## Supported files

Images: JPEG, PNG, WebP, and BMP.

PDF analysis renders the first three pages by default. This can be changed
with `VISION_PDF_MAX_PAGES`.
