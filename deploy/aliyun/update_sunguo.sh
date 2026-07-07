#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/opt/sunguo/ai-butler"
SERVICE_NAME="sunguo-dashboard"

cd "$PROJECT_DIR"

git pull --ff-only
npm install
sudo systemctl restart "$SERVICE_NAME"
sudo systemctl status "$SERVICE_NAME" --no-pager

if [[ -x "$PROJECT_DIR/deploy/aliyun/refresh_sunguo_brief.sh" ]]; then
    sudo bash "$PROJECT_DIR/deploy/aliyun/refresh_sunguo_brief.sh"
fi
