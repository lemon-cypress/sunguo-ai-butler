#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/opt/sunguo/ai-butler"
LOG_DIR="/opt/sunguo/logs"
mkdir -p "$LOG_DIR"

cd "$PROJECT_DIR"
echo "==== $(date '+%F %T') refresh start ====" >> "$LOG_DIR/brief-refresh.log"
python3 backend/app/morning_brief_demo.py --save >> "$LOG_DIR/brief-refresh.log" 2>&1
echo "==== $(date '+%F %T') refresh end ====" >> "$LOG_DIR/brief-refresh.log"
