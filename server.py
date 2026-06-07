import base64
import io
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from openai import OpenAI, APIConnectionError, APITimeoutError, RateLimitError, APIStatusError
from PIL import Image, ImageOps, UnidentifiedImageError

try:
    import fitz
except Exception:
    fitz = None


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vision-mcp")

mcp = FastMCP("vision-mcp")

ALLOWED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def _env_required(key: str) -> str:
    value = os.environ.get(key, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


def _env_int(key: str, default: int, *, min_value: int, max_value: int | None = None) -> int:
    raw_value = os.environ.get(key, "").strip()
    if not raw_value:
        return default
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"{key} must be an integer, got {raw_value!r}.") from exc
    if value < min_value:
        raise RuntimeError(f"{key} must be at least {min_value}, got {value}.")
    if max_value is not None and value > max_value:
        raise RuntimeError(f"{key} must be at most {max_value}, got {value}.")
    return value


_client_instance: OpenAI | None = None


def _client() -> OpenAI:
    global _client_instance
    if _client_instance is None:
        _client_instance = OpenAI(
            api_key=_env_required("VISION_API_KEY"),
            base_url=_env_required("VISION_BASE_URL"),
            timeout=_env_int("VISION_TIMEOUT_SECONDS", 60, min_value=1, max_value=600),
        )
    return _client_instance


def _normalize_image(image: Image.Image) -> Image.Image:
    max_side = _env_int("VISION_MAX_IMAGE_SIDE", 1600, min_value=128, max_value=4096)
    image = ImageOps.exif_transpose(image)
    if max(image.size) > max_side:
        scale = max_side / max(image.size)
        image = image.resize((int(image.width * scale), int(image.height * scale)), Image.LANCZOS)
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return image.convert("RGB")


def _image_to_data_url(image: Image.Image) -> str:
    image = _normalize_image(image)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def _file_image_to_data_url(path: Path) -> str:
    try:
        with Image.open(path) as image:
            return _image_to_data_url(image)
    except UnidentifiedImageError as exc:
        raise ValueError(f"Invalid or corrupted image file: {path}") from exc


def _validate_image_path(path: str) -> Path:
    image_path = Path(path).expanduser().resolve()
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    if not image_path.is_file():
        raise ValueError(f"Image path is not a file: {image_path}")
    if image_path.suffix.lower() not in ALLOWED_IMAGE_SUFFIXES:
        raise ValueError(f"Unsupported image format: {image_path.suffix}")
    return image_path


def _analyze_data_urls(data_urls: list[str], prompt: str) -> str:
    if not data_urls:
        raise ValueError("No images were provided for analysis.")
    content = [{"type": "text", "text": prompt}]
    content.extend({"type": "image_url", "image_url": {"url": url}} for url in data_urls)
    model = _env_required("VISION_MODEL")
    logger.info("Calling vision model %s with %d image(s)", model, len(data_urls))
    try:
        response = _client().chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You extract visible information from images accurately and structurally.",
                },
                {"role": "user", "content": content},
            ],
            max_tokens=4096,
        )
    except APITimeoutError:
        raise RuntimeError("Vision API request timed out. Try increasing VISION_TIMEOUT_SECONDS.")
    except APIConnectionError:
        raise RuntimeError("Cannot connect to vision API. Check VISION_BASE_URL and network.")
    except RateLimitError:
        raise RuntimeError("Vision API rate limit exceeded. Wait and retry.")
    except APIStatusError as e:
        raise RuntimeError(f"Vision API returned status {e.status_code}: {e.message}")
    except Exception as e:
        raise RuntimeError(f"Vision API call failed: {e}")
    result = response.choices[0].message.content or ""
    logger.info("Vision model returned %d characters", len(result))
    return result


@mcp.tool()
def analyze_image(path: str, prompt: str = "Analyze this image and extract all visible information.") -> str:
    """使用视觉模型分析一张本地图片。

    可用于图片描述、OCR 文字提取、截图排错、表格识别、界面分析和图表解读。
    path 必须是本机图片的绝对路径，支持 JPEG、PNG、WebP 和 BMP。prompt 用于
    指定分析目标；函数返回视觉模型生成的文本结果。
    """
    image_path = _validate_image_path(path)
    return _analyze_data_urls([_file_image_to_data_url(image_path)], prompt)


@mcp.tool()
def analyze_images(
    paths: list[str],
    prompt: str = "Analyze these images together and extract all visible information.",
) -> str:
    """使用视觉模型在同一次请求中联合分析多张本地图片。

    适合比较前后变化、理解连续截图、分析多页扫描件，或汇总分散在多张图片中的
    信息。paths 必须是非空的本机图片绝对路径列表，prompt 用于说明需要跨图片
    完成的任务；函数返回统一的文本分析结果。
    """
    if not paths:
        raise ValueError("At least one image path is required.")
    image_paths = [_validate_image_path(path) for path in paths]
    return _analyze_data_urls([_file_image_to_data_url(path) for path in image_paths], prompt)


@mcp.tool()
def analyze_pdf(path: str, prompt: str = "Analyze these PDF pages and extract all visible information.") -> str:
    """将本地 PDF 页面渲染为图片并交给视觉模型分析。

    适合扫描版 PDF、复杂图文排版、报告和普通文本提取工具难以处理的文档。
    path 必须是本机 PDF 的绝对路径。默认分析前 3 页，页数和渲染清晰度可通过
    环境变量调整；函数返回模型对所渲染页面的文本分析结果。
    """
    if fitz is None:
        raise RuntimeError("PyMuPDF is not installed.")
    pdf_path = Path(path).expanduser().resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if not pdf_path.is_file():
        raise ValueError(f"PDF path is not a file: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Unsupported PDF format: {pdf_path.suffix}")
    max_pages = _env_int("VISION_PDF_MAX_PAGES", 3, min_value=1, max_value=20)
    dpi = _env_int("VISION_PDF_RENDER_DPI", 200, min_value=72, max_value=300)
    data_urls: list[str] = []
    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:
        raise ValueError(f"Cannot open PDF: {pdf_path}") from exc
    with doc:
        if doc.is_encrypted:
            raise ValueError("Encrypted PDFs are not supported.")
        if doc.page_count == 0:
            raise ValueError("PDF has no pages.")
        for page_number in range(min(max_pages, doc.page_count)):
            page = doc.load_page(page_number)
            pix = page.get_pixmap(dpi=dpi, alpha=False)
            with Image.open(io.BytesIO(pix.tobytes("png"))) as image:
                data_urls.append(_image_to_data_url(image))
    return _analyze_data_urls(data_urls, prompt)


if __name__ == "__main__":
    mcp.run()
