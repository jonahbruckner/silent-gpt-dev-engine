#!/usr/bin/env python
"""
Generate or update long_description for each pack JSON using OpenAI.

Usage (from repo root):

    export OPENAI_API_KEY="sk-..."
    python automations/generate_pack_descriptions.py

Only packs without `long_description` are updated by default.
Use `--force` to overwrite existing descriptions.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
import textwrap

import requests


ROOT_DIR = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT_DIR / "site"
PACKS_DIR = SITE_DIR / "static" / "packs"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")


def call_openai(prompt: str) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set in environment.")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a concise copywriter. "
                    "Write a compelling 3–4 sentence product description for a digital pack. "
                    "Target: intermediate developers / engineers. "
                    "Tone: friendly, clear, slightly opinionated, no marketing fluff. "
                    "Output plain text, no markdown headings or bullet lists."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "max_tokens": 260,
        "temperature": 0.7,
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def build_prompt(pack: dict) -> str:
    title = pack.get("title", "")
    topic = pack.get("topic", "")
    short_desc = pack.get("description", "")
    items = pack.get("items", [])

    lines = []
    lines.append(f"Pack title: {title}")
    if topic:
        lines.append(f"Topic: {topic}")
    if short_desc:
        lines.append(f"Short description: {short_desc}")
    lines.append("")
    lines.append("Included micro-tutorials (titles):")
    for item in items:
        t = item.get("title", "").strip()
        if t:
            lines.append(f"- {t}")

    return "\n".join(lines)


def process_pack(json_path: Path, force: bool = False):
    data = json.loads(json_path.read_text(encoding="utf-8"))
    slug = data.get("pack_slug") or json_path.stem

    if not force and data.get("long_description"):
        print(f"[generate_pack_descriptions] {slug}: long_description already set, skipping.")
        return

    prompt = build_prompt(data)
    print(f"[generate_pack_descriptions] Generating description for {slug} using {OPENAI_MODEL} ...")

    try:
        long_desc = call_openai(prompt)
    except Exception as exc:
        print(f"  ERROR for {slug}: {exc}")
        return

    data["long_description"] = long_desc
    # Optional: update generated_at
    data["generated_at"] = datetime.now(timezone.utc).isoformat()

    json_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  -> updated {json_path.relative_to(ROOT_DIR)}")


def run(force: bool = False):
    if not PACKS_DIR.exists():
        print(f"[generate_pack_descriptions] Packs dir not found: {PACKS_DIR}")
        return

    files = sorted(PACKS_DIR.glob("*.json"))
    if not files:
        print(f"[generate_pack_descriptions] No JSON files in {PACKS_DIR}")
        return

    for jf in files:
        process_pack(jf, force=force)


if __name__ == "__main__":
    force_flag = "--force" in sys.argv
    run(force=force_flag)
