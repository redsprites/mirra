#!/usr/bin/env python3
"""Build dashboard JSON from saved_videos transcripts and captions."""

import json
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

SAVED_DIR = Path("saved_videos")
OUT_PATH = Path("web/data.json")

THEMES = {
    "Self & Mindset": [
        "therapy", "mindset", "identity", "depression", "anxiety", "journal",
        "self", "awareness", "belief", "emotion", "mental", "psycholog",
        "repress", "jung", "attachment", "trauma", "heal", "growth",
    ],
    "Relationships": [
        "relationship", "dating", "friend", "love", "partner", "marriage",
        "attachment", "intimacy", "lonely", "connection", "communicat",
    ],
    "Fitness & Health": [
        "gym", "workout", "muscle", "fitness", "health", "posture", "sleep",
        "body", "exercise", "train", "protein", "fat", "run", "injury",
    ],
    "Business & Tech": [
        "startup", "business", "users", "product", "launch", "engineer",
        "code", "gpt", "ai", "llm", "automate", "founder", "build", "app",
    ],
    "Culture & Music": [
        "dance", "music", "dj", "afro", "song", "beat", "tutorial",
    ],
}

INSIGHTS = [
    {
        "title": "Identity adapts to who feels safe",
        "body": "Much of what you save explores how personality shifts around approval, rejection, and belonging — not a fixed self, but a negotiated one.",
        "tags": ["Self & Mindset", "Relationships"],
    },
    {
        "title": "Foundation before ambition",
        "body": "Health, sleep, gym, and emotional regulation show up repeatedly — the through-line is: stabilize the body and mind before chasing the next level.",
        "tags": ["Fitness & Health", "Self & Mindset"],
    },
    {
        "title": "Build, then simplify, then scale",
        "body": "Startup and systems content (Elon’s steps, first 100 users, launch playbooks) pairs with deep introspection — you’re optimizing both the inner and outer game.",
        "tags": ["Business & Tech"],
    },
    {
        "title": "Desire vs. fulfillment",
        "body": "Saved clips on attachment, scarcity, and ‘futile desires’ suggest you’re circling one question: can you want things without needing them to feel whole?",
        "tags": ["Self & Mindset", "Relationships"],
    },
    {
        "title": "Action breaks the loop",
        "body": "Post daily, record yourself, show up reliably — the practical saves push past overthinking into visible consistency.",
        "tags": ["Self & Mindset", "Business & Tech"],
    },
]


def parse_folder_date(name: str):
    match = re.match(r"(\d{4}-\d{2}-\d{2})_", name)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y-%m-%d").date().isoformat()
        except ValueError:
            pass
    return None


def read_caption(txt_path: Path) -> tuple[str, list[str]]:
    if not txt_path.exists():
        return "", []
    text = txt_path.read_text(encoding="utf-8", errors="ignore").strip()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    caption = lines[0] if lines else ""
    hashtags = re.findall(r"#(\w+)", text.lower())
    return caption, hashtags


def read_transcript(folder: Path, stem: str) -> Tuple[str, int, Optional[str]]:
    transcript_path = folder / f"{stem}.transcript.txt"
    json_path = folder / f"{stem}.json"
    text = ""
    word_count = 0
    language = None

    if transcript_path.exists():
        text = transcript_path.read_text(encoding="utf-8", errors="ignore").strip()
        word_count = len(text.split())
    elif json_path.exists():
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            text = (data.get("text") or "").strip()
            word_count = data.get("word_count") or len(text.split())
            language = data.get("language")
        except json.JSONDecodeError:
            pass

    if json_path.exists() and not language:
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            language = data.get("language")
        except json.JSONDecodeError:
            pass

    return text, word_count, language


def classify(text: str, hashtags: list[str]) -> str:
    blob = f"{text} {' '.join(hashtags)}".lower()
    scores = {}
    for theme, keywords in THEMES.items():
        scores[theme] = sum(1 for kw in keywords if kw in blob)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Other"


def excerpt(text: str, limit: int = 180) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rsplit(" ", 1)[0] + "…"


def collect_items():
    items = []
    for folder in sorted(SAVED_DIR.iterdir()):
        if not folder.is_dir():
            continue
        mp4s = list(folder.glob("*.mp4"))
        if not mp4s:
            continue
        stem = mp4s[0].stem
        date = parse_folder_date(folder.name)
        caption, hashtags = read_caption(folder / f"{stem}.txt")
        transcript, word_count, language = read_transcript(folder, stem)
        theme = classify(f"{caption} {transcript}", hashtags)
        items.append({
            "id": folder.name,
            "date": date,
            "caption": caption or "Saved video",
            "theme": theme,
            "hashtags": hashtags[:8],
            "word_count": word_count,
            "language": language,
            "has_transcript": bool(transcript and word_count > 3),
            "excerpt": excerpt(transcript) if transcript else "",
        })
    return items


def build_profile(items: list[dict]) -> dict:
    transcribed = [i for i in items if i["has_transcript"]]
    theme_counts = Counter(i["theme"] for i in transcribed)
    total_words = sum(i["word_count"] for i in transcribed)
    hashtag_counts = Counter(h for i in transcribed for h in i["hashtags"])
    by_month = Counter()
    for i in transcribed:
        if i["date"]:
            by_month[i["date"][:7]] += 1

    featured = sorted(
        [i for i in transcribed if i["word_count"] >= 40],
        key=lambda x: x["word_count"],
        reverse=True,
    )[:12]

    recent = sorted(
        [i for i in transcribed if i["date"]],
        key=lambda x: x["date"],
        reverse=True,
    )[:8]

    themes_pct = []
    total_t = sum(theme_counts.values()) or 1
    for theme, count in theme_counts.most_common():
        themes_pct.append({
            "name": theme,
            "count": count,
            "pct": round(100 * count / total_t, 1),
        })

    return {
        "generated_at": datetime.now().isoformat(),
        "username": os.environ.get("MIRRA_USERNAME", "demo_user"),
        "stats": {
            "total_videos": len(items),
            "transcribed": len(transcribed),
            "pending": len(items) - len(transcribed),
            "total_words": total_words,
            "date_range": {
                "start": min((i["date"] for i in items if i["date"]), default=None),
                "end": max((i["date"] for i in items if i["date"]), default=None),
            },
        },
        "themes": themes_pct,
        "top_hashtags": [{"tag": t, "count": c} for t, c in hashtag_counts.most_common(15)],
        "activity_by_month": [
            {"month": m, "count": c}
            for m, c in sorted(by_month.items())
        ],
        "insights": INSIGHTS,
        "featured_saves": featured,
        "recent_saves": recent,
    }


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    items = collect_items()
    profile = build_profile(items)
    profile["items"] = items
    OUT_PATH.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Wrote {OUT_PATH} ({profile['stats']['transcribed']} transcribed / {profile['stats']['total_videos']} videos)")


if __name__ == "__main__":
    main()
