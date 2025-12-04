#!/usr/bin/env python3
"""
Harvests new questions/issues into data/harvest/questions.jsonl.

This version does NOT use SQLModel/DB anymore.
It simply loads new raw questions from data/raw_questions/YYYY-MM-DD/
and appends them to questions.jsonl.
"""

import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw_questions"
HARVEST_FILE = ROOT / "data" / "harvest" / "questions.jsonl"


def load_existing_ids():
    """Return all original_id already stored in questions.jsonl."""
    if not HARVEST_FILE.exists():
        return set()

    ids = set()
    with HARVEST_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if "original_id" in obj:
                    ids.add(obj["original_id"])
            except:
                pass
    return ids


def harvest_today():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    day_dir = RAW_DIR / today

    if not day_dir.exists():
        print(f"[harvest] No raw questions for today: {day_dir}")
        return []

    items = []
    for file in sorted(day_dir.glob("*.json")):
        obj = json.loads(file.read_text(encoding="utf-8"))
        items.append(obj)

    print(f"[harvest] Loaded {len(items)} raw items for {today}")
    return items


def append_new_items(new_items, existing_ids):
    added = 0
    with HARVEST_FILE.open("a", encoding="utf-8") as f:
        for item in new_items:
            oid = item.get("original_id")
            if oid not in existing_ids:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
                added += 1
    print(f"[harvest] Added {added} new items.")
    return added


def run():
    existing = load_existing_ids()
    new_items = harvest_today()
    append_new_items(new_items, existing)


if __name__ == "__main__":
    run()
