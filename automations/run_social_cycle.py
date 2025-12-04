#!/usr/bin/env python3
import subprocess
from pathlib import Path
import logging

ROOT_DIR = Path(__file__).resolve().parents[1]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [social_cycle] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_step(label: str, args):
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
        # Social-Fehler sollen den gesamten Run nicht killen
        return


def main():
    logger.info("=== Social cycle started ===")

    run_step("twitter_bot", ["python", "-m", "automations.bots.twitter_bot"])
    run_step("linkedin_bot", ["python", "-m", "automations.bots.linkedin_bot"])
    run_step("devto_bot", ["python", "-m", "automations.bots.devto_bot"])
    run_step("medium_bot", ["python", "-m", "automations.bots.medium_bot"])
    run_step("substack_bot", ["python", "-m", "automations.bots.substack_bot"])

    logger.info("=== Social cycle finished ===")


if __name__ == "__main__":
    main()
