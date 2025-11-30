#!/bin/bash

set -euo pipefail

PY_BIN="${PY_BIN:-python3}"
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PKG_DIR="$ROOT_DIR/lambda_pkg"
ZIP_FILE="$ROOT_DIR/function.zip"

echo "Cleaning old artifacts..."
rm -rf "$PKG_DIR" "$ZIP_FILE"
mkdir -p "$PKG_DIR"

echo "Installing dependencies into package dir..."
"$PY_BIN" -m pip install --upgrade pip >/dev/null
"$PY_BIN" -m pip install -r "$ROOT_DIR/lambda_requirements.txt" -t "$PKG_DIR"

echo "Copying Lambda handler..."
cp "$ROOT_DIR/lambda_function.py" "$PKG_DIR/"

echo "Copying market_data module..."
cp -R "$ROOT_DIR/market_data" "$PKG_DIR/"
find "$PKG_DIR/market_data" -name "__pycache__" -type d -exec rm -rf {} +

echo "Creating ZIP..."
if command -v zip >/dev/null 2>&1; then
  cd "$PKG_DIR"
  zip -r9 "$ZIP_FILE" . >/dev/null
  cd "$ROOT_DIR"
else
  echo "zip not found, using Python zipfile fallback..."
  "$PY_BIN" - <<'PY'
import os, sys, zipfile
root = os.path.dirname(os.path.abspath(__file__))
pkg = os.path.join(root, 'lambda_pkg')
zip_path = os.path.join(root, 'function.zip')
with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
    for base, dirs, files in os.walk(pkg):
        for f in files:
            fp = os.path.join(base, f)
            rp = os.path.relpath(fp, pkg)
            z.write(fp, arcname=rp)
print('Created:', zip_path)
PY
fi
SIZE=$(du -h "$ZIP_FILE" | awk '{print $1}')
echo "Done. Created: $ZIP_FILE ($SIZE)"
echo "Upload this ZIP in the AWS Lambda Console (Code -> Upload from -> .zip file)."


