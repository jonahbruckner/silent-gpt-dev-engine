#!/usr/bin/env python3
import shutil
from pathlib import Path
import logging

ROOT_DIR = Path(__file__).resolve().parents[1]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [cleanup] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Verzeichnisse, die WIRKLICH nur Runtime-Müll enthalten
# WICHTIG: social_queue bleibt draußen, sonst haben die Social-Bots nichts mehr zu fressen.
CLEAN_DIRS = [
    ROOT_DIR / "data" / "harvest",
    ROOT_DIR / "data" / "packs" / "weekly",
    ROOT_DIR / "drafts" / "local",
    ROOT_DIR / "drafts" / "selected",
]


def clean_dir(path: Path):
    if not path.exists():
        return
    logger.info("Cleaning %s", path)
    for child in path.iterdir():
        try:
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                shutil.rmtree(child)
        except Exception as e:
            logger.warning("Failed to remove %s: %s", child, e)


def main():
    logger.info("Starting cleanup of generated runtime artifacts...")
    for d in CLEAN_DIRS:
        clean_dir(d)
    logger.info("Done.")


if __name__ == "__main__":
    main()
