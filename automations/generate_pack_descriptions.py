#!/usr/bin/env python
"""
Generate or update long_description for each pack JSON using OpenAI.

Usage (from repo root):

    export OPENAI_API_KEY="sk-..."
    python automations/generate_pack_descriptions.py

Only packs without `long_description` are updated by default.
Use `--force` to overwrite existing descriptions.

Neu:
- Liest pack_templates.yaml
- Nutzt für jedes Pack (per pack_slug) das Feld `description_prompt`, um das Prompt
  für die Long-Description zu steuern.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict
import textwrap

import requests
import yaml

ROOT_DIR = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT_DIR / "site"
PACKS_DIR = SITE_DIR / "static" / "packs"
TEMPLATES_PATH = ROOT_DIR / "automations" / "pack_templates.yaml"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")


def load_templates_by_slug() -> Dict[str, Dict[str, Any]]:
    """
    Liest die Pack-Blueprints aus pack_templates.yaml und liefert ein Mapping
    pack_slug -> Template-Dict zurück.
    """
    if not TEMPLATES_PATH.exists():
        print(f"[generate_pack_descriptions] Template file not found: {TEMPLATES_PATH}")
        return {}

    with TEMPLATES_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or []

    if not isinstance(data, list):
        print("[generate_pack_descriptions] pack_templates.yaml must contain a top-level list.")
        return {}

    mapping: Dict[str, Dict[str, Any]] = {}
    for entry in data:
        slug = entry.get("pack_slug")
        if not slug:
            continue
        mapping[slug] = entry
    return mapping


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


def build_prompt(pack: dict, template: Dict[str, Any] | None) -> str:
    """
    Baut das User-Prompt für das LLM.

    Wenn ein Template vorhanden ist und ein `description_prompt` enthält,
    wird dieser Text am Anfang des Prompts verwendet, damit der Ton/Focus
    pro Pack steuerbar ist.
    """
    title = pack.get("title", "")
    topic = pack.get("topic", "")
    short_desc = pack.get("description", "")
    items = pack.get("items", [])

    lines: list[str] = []

    # 1) Template-spezifische Guidance
    if template:
        tpl_prompt = (template.get("description_prompt") or "").strip()
        if tpl_prompt:
            lines.append("High-level description guidance for this pack:")
            lines.append(tpl_prompt)
            lines.append("")

    # 2) Pack-Metadaten
    lines.append(f"Pack title: {title}")
    if topic:
        lines.append(f"Topic: {topic}")
    if short_desc:
        lines.append(f"Existing short description: {short_desc}")

    # 3) Item-Liste
    lines.append("")
    lines.append("Included micro-tutorials (titles):")
    for item in items:
        t = item.get("title", "").strip()
        if t:
            lines.append(f"- {t}")

    # 4) Explizite Aufgabe an das Modell
    lines.append("")
    lines.append(
        "Task: Using the guidance above, write a 3–4 sentence product description "
        "that clearly explains who this pack is for, which recurring problems it solves "
        "and why it is valuable. Return only the final description text."
    )

    return "\n".join(lines)


def process_pack(
    json_path: Path,
    templates_by_slug: Dict[str, Dict[str, Any]],
    force: bool = False,
) -> None:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    slug = data.get("pack_slug") or json_path.stem

    if not force and data.get("long_description"):
        print(f"[generate_pack_descriptions] {slug}: long_description already set, skipping.")
        return

    template = templates_by_slug.get(slug)
    if not template:
        print(f"[generate_pack_descriptions] {slug}: no template found in pack_templates.yaml, using generic prompt.")

    prompt = build_prompt(data, template)
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
    rel = json_path.relative_to(ROOT_DIR)
    print(f"  -> updated {rel}")


def run(force: bool = False):
    templates_by_slug = load_templates_by_slug()

    if not PACKS_DIR.exists():
        print(f"[generate_pack_descriptions] Packs dir not found: {PACKS_DIR}")
        return

    files = sorted(PACKS_DIR.glob("*.json"))
    if not files:
        print(f"[generate_pack_descriptions] No JSON files in {PACKS_DIR}")
        return

    for jf in files:
        process_pack(jf, templates_by_slug, force=force)


if __name__ == "__main__":
    force_flag = "--force" in sys.argv
    run(force=force_flag)
