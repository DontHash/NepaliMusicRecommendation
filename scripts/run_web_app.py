"""Launch the Mood Studio web app and open it in the browser.

Usage:
    python scripts/run_web_app.py [--host 127.0.0.1] [--port 8000] [--no-browser]
"""

from __future__ import annotations

import argparse
import sys
import threading
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    url = f"http://{args.host}:{args.port}"
    print(f"[mood-studio] starting at {url}")
    if not args.no_browser:
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    uvicorn.run("web_app.server:app", host=args.host, port=args.port, app_dir=str(PROJECT_ROOT))


if __name__ == "__main__":
    main()
