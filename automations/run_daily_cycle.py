#!/usr/bin/env bash
set -euo pipefail

# Vom Skript aus ins Repo-Root springen
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

echo "[daily_cycle] Starting SilentGPT Dev Engine daily cycle..."

# 1) Neue Content-Ideen ernten (falls du harvest nutzt)
if [ -f "automations/harvest.py" ]; then
  echo "[daily_cycle] harvest.py..."
  python automations/harvest.py || echo "[daily_cycle] harvest.py failed (continuing)."
fi

# 2) Aus RawQuestions Content generieren (falls vorhanden)
if [ -f "automations/generate_content.py" ]; then
  echo "[daily_cycle] generate_content.py..."
  python automations/generate_content.py || echo "[daily_cycle] generate_content.py failed (continuing)."
fi

# 3) Neue Posts direkt über AI generieren (Phase 3.1)
if [ -f "automations/auto_generate_blogposts.py" ]; then
  echo "[daily_cycle] auto_generate_blogposts.py..."
  python automations/auto_generate_blogposts.py || echo "[daily_cycle] auto_generate_blogposts.py failed (continuing)."
fi

# 4) Blog aus DB nach Hugo schreiben
if [ -f "automations/publish_blog.py" ]; then
  echo "[daily_cycle] publish_blog.py..."
  python automations/publish_blog.py || echo "[daily_cycle] publish_blog.py failed (continuing)."
fi

# 5) Packs + Produktseiten neu bauen
echo "[daily_cycle] build_packs.py..."
python automations/build_packs.py || echo "[daily_cycle] build_packs.py failed (continuing)."

# 6) Download-ZIPs aktualisieren
echo "[daily_cycle] build_download_zips.py..."
python automations/build_download_zips.py || echo "[daily_cycle] build_download_zips.py failed (continuing)."

# 7) QA-Report für frische Inhalte
echo "[daily_cycle] qa_check_content.py..."
python automations/qa_check_content.py || echo "[daily_cycle] qa_check_content.py failed (continuing)."

echo "[daily_cycle] Done."
