#!/usr/bin/env python3
"""Generate insights and serve the SaveDNA dashboard."""

import argparse
import http.server
import os
import socketserver
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
WEB = ROOT / "web"


def generate():
    subprocess.check_call([sys.executable, str(ROOT / "generate_insights.py")], cwd=ROOT)


def main():
    parser = argparse.ArgumentParser(description="Serve SaveDNA dashboard")
    parser.add_argument("-p", "--port", type=int, default=8080)
    parser.add_argument("--no-generate", action="store_true")
    args = parser.parse_args()

    if not args.no_generate:
        generate()

    os.chdir(WEB)
    with socketserver.TCPServer(("", args.port), http.server.SimpleHTTPRequestHandler) as httpd:
        print(f"SaveDNA dashboard → http://localhost:{args.port}")
        print("Press Ctrl+C to stop")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
