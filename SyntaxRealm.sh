#!/bin/bash
APP_DIR="${APP_DIR:-/app}"
cd "$APP_DIR" || { echo "[SyntaxRealm] Cannot cd to $APP_DIR"; exit 1; }

echo "[SyntaxRealm] Checking for updates..."
[ -f update.py ] && python3 update.py
echo "[SyntaxRealm] Starting bot..."
exec python3 main.py
