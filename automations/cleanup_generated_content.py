#!/usr/bin/env python3
"""
Cleanup script for generated, NON-source artifacts.

This removes runtime files that should never be committed to git:

- data/harvest/
- data/packs/weekly/
- data/social_queue/
- drafts/local/
- drafts/selected/

It leaves:
- site/static/packs/*.json
- site/static/downloads/*.zip
- site/content/*
untouched.
"""

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


CLEAN_DIRS = [
    ROOT / "data" / "harvest",
    ROOT / "data" / "packs" / "weekly",
    ROOT / "data" / "social_queue",
    ROOT / "drafts" / "local",
    ROOT / "drafts" / "selected",
]


def clean_directory(path: Path):
    if not path.exists():
        return

    if not path.is_dir():
        return

    for child in path.iterdir():
        if child.is_dir():
            shutil.rmtree(child, ignore_errors=True)
        else:
            try:
                child.unlink()
            except FileNotFoundError:
                pass


def run():
    print("[cleanup] Starting cleanup of generated runtime artifacts...")
    for d in CLEAN_DIRS:
        print(f"[cleanup] Cleaning {d}")
        clean_directory(d)

    # Ensure dirs exist (so other scripts don't choke on missing dirs)
    for d in CLEAN_DIRS:
        d.mkdir(parents=True, exist_ok=True)

    print("[cleanup] Done.")


if __name__ == "__main__":
    run()
