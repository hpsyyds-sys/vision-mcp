import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from server import analyze_image


DEFAULT_PROMPT = "Analyze this image and extract all visible information."


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a local vision analysis smoke test.")
    parser.add_argument("image_path", help="Path to a local image file.")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="Prompt sent with the image.")
    args = parser.parse_args()

    try:
        content = analyze_image(args.image_path, args.prompt)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    print("\n" + "=" * 60)
    print(content)
    print("=" * 60 + "\n")
    print(f"[INFO] Completed. Returned {len(content)} characters.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
