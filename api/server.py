#!/usr/bin/env python3
"""SaveDNA API — mock auth, analysis jobs, report, Kiro chat."""

import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
sys.path.insert(0, str(ROOT))

from api.kiro_chat import ask_kiro  # noqa: E402

app = Flask(__name__, static_folder=str(WEB), static_url_path="")
CORS(app)

jobs: dict[str, dict] = {}


def run_generate_insights():
    subprocess.run(
        [sys.executable, str(ROOT / "generate_insights.py")],
        cwd=str(ROOT),
        check=True,
    )


def simulate_job(job_id: str):
    steps = [
        ("connect", "Connecting to Instagram…", 1.5),
        ("fetch", "Scanning saved posts…", 2.5),
        ("transcribe", "Reading transcripts…", 2.0),
        ("analyze", "Building your Save Profile…", 1.0),
    ]
    job = jobs[job_id]
    try:
        for i, (key, label, delay) in enumerate(steps):
            job["step"] = key
            job["label"] = label
            job["progress"] = int((i / len(steps)) * 70)
            time.sleep(delay)

        job["step"] = "analyze"
        job["label"] = "Generating insights…"
        job["progress"] = 85
        run_generate_insights()

        job["progress"] = 100
        job["status"] = "done"
        job["label"] = "Your report is ready"
    except Exception as exc:
        job["status"] = "error"
        job["error"] = str(exc)


@app.route("/")
def index():
    return send_from_directory(WEB, "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(WEB, path)


@app.post("/api/auth/login")
def login():
    body = request.get_json(silent=True) or {}
    username = (body.get("username") or "demo_user").lstrip("@")
    token = uuid.uuid4().hex
    return jsonify({"token": token, "username": username})


@app.post("/api/analyze/start")
def analyze_start():
    job_id = uuid.uuid4().hex[:12]
    jobs[job_id] = {
        "id": job_id,
        "status": "running",
        "progress": 0,
        "step": "connect",
        "label": "Starting…",
    }
    threading.Thread(target=simulate_job, args=(job_id,), daemon=True).start()
    return jsonify(jobs[job_id])


@app.get("/api/analyze/status/<job_id>")
def analyze_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.get("/api/report")
def report():
    path = WEB / "data.json"
    if not path.exists():
        return jsonify({"error": "Report not ready. Run analysis first."}), 404
    return send_from_directory(WEB, "data.json")


@app.post("/api/chat")
def chat():
    body = request.get_json(silent=True) or {}
    message = (body.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Message required"}), 400
    history = body.get("history") or []
    try:
        reply = ask_kiro(message, history)
        return jsonify({"reply": reply})
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Kiro timed out. Try a shorter question."}), 504
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, default=8765)
    args = parser.parse_args()
    print(f"Mirra → http://localhost:{args.port}")
    app.run(host="0.0.0.0", port=args.port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
