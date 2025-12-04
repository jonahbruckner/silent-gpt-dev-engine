#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path
import logging

ROOT_DIR = Path(__file__).resolve().parents[1]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [weekly_cycle] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_step(label: str, args):
    """
    Führt einen einzelnen Schritt als Subprozess aus.
    Bricht mit Exit-Code ab, wenn ein Schritt fehlschlägt.
    """
    cmd_str = " ".join(args)
    logger.info("Starting step: %s (%s)", label, cmd_str)

    try:
        result = subprocess.run(
            args,
            cwd=ROOT_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            logger.info("[%s stdout]\n%s", label, result.stdout.strip())
        if result.stderr:
            logger.warning("[%s stderr]\n%s", label, result.stderr.strip())
    except subprocess.CalledProcessError as e:
        logger.error(
            "Step '%s' failed with code %s\nSTDOUT:\n%s\nSTDERR:\n%s",
            label,
            e.returncode,
            e.stdout or "",
            e.stderr or "",
        )
        sys.exit(e.returncode)


def main():
    logger.info("=== Weekly cycle started ===")

    # 1) Fragen einsammeln (StackOverflow etc.)
    run_step("harvest", ["python", "automations/harvest.py"])

    # 2) Local-LLM / GPT: Drafts generieren
    run_step("bulk_generate", ["python", "automations/bulk_generate.py"])

    # 3) GPT-Scoring + Social-Snippets
    run_step("quality_filter", ["python", "automations/quality_filter.py"])

    # 4) Blogposts + Microsites syncen
    run_step("sync_microsites", ["python", "automations/sync_microsites.py"])

    # 5) Weekly-Packs aus den ausgewählten Artikeln bauen
    run_step("weekly_pack_builder", ["python", "automations/weekly_pack_builder.py"])

    # 6) Weekly-Packs -> Hugo-Produkte + Pack-JSON
    run_step(
        "sync_packs_from_weekly",
        ["python", "automations/sync_packs_from_weekly.py"],
    )

    # 7) Downloads (ZIPs) für alle Packs generieren
    run_step("build_download_zips", ["python", "automations/build_download_zips.py"])

    # 8) Cleanup: Runtime-Artefakte entfernen, aber Zips/Pack-JSONs behalten
    run_step(
        "cleanup_generated_content",
        ["python", "automations/cleanup_generated_content.py"],
    )

    logger.info("=== Weekly cycle finished successfully ===")


if __name__ == "__main__":
    main()
