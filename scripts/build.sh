#!/usr/bin/env bash
# Linux/macOS build: dist/Twinsight/Twinsight (or Twinsight.app on macOS)
set -e
cd "$(dirname "$0")/.."
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python scripts/tools/make_icon.py
pyinstaller twinsight.spec --noconfirm --clean
echo "Done: dist/Twinsight"
