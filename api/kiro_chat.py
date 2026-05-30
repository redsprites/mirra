"""Call Kiro CLI for chat responses with SaveDNA context."""

import json
import re
import subprocess
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "web" / "data.json"


def strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", text)


def parse_kiro_output(raw: str) -> str:
    cleaned = strip_ansi(raw)
    lines = []
    for line in cleaned.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("> "):
            lines.append(line[2:].strip())
            continue
        if any(
            skip in line
            for skip in (
                "WARNING:",
                "Checkpoints are enabled",
                "Credits:",
                "MCP server",
                "Popular Subcommands",
            )
        ):
            continue
        if line.startswith("▸"):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def build_context() -> str:
    if not DATA_PATH.exists():
        return "No save profile data yet."
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    themes = ", ".join(f"{t['name']} {t['pct']}%" for t in data.get("themes", [])[:6])
    insights = "\n".join(
        f"- {i['title']}: {i['body']}" for i in data.get("insights", [])[:5]
    )
    featured = data.get("featured_saves", [])[:5]
    samples = "\n".join(
        f"- [{s.get('date', '?')}] {s.get('caption', '')[:100]}"
        for s in featured
    )
    stats = data.get("stats", {})
    return f"""You are SaveDNA, an insightful coach analyzing someone's private Instagram saved videos.

USER SAVE PROFILE (@{data.get('username', 'user')}):
- Videos saved: {stats.get('total_videos', 0)}
- Transcribed: {stats.get('transcribed', 0)}
- Words analyzed: {stats.get('total_words', 0)}
- Date range: {stats.get('date_range', {})}

THEME BREAKDOWN: {themes}

CURATED INSIGHTS:
{insights}

SAMPLE SAVES:
{samples}

Answer warmly and specifically. Reference their save patterns. Be concise unless they ask for depth. Do not mention you are an AI unless asked."""


def ask_kiro(user_message: str, history: Optional[List] = None) -> str:
    context = build_context()
    history = history or []
    history_text = ""
    if history:
        pairs = history[-6:]
        history_text = "\n\nRECENT CHAT:\n" + "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in pairs
        )

    prompt = f"""{context}{history_text}

USER QUESTION: {user_message}

Respond as SaveDNA:"""

    result = subprocess.run(
        ["kiro-cli", "chat", "--no-interactive", prompt],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    output = result.stdout + result.stderr
    reply = parse_kiro_output(output)
    if not reply:
        raise RuntimeError("Kiro returned an empty response")
    return reply
