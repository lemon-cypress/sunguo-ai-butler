#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/opt/sunguo/ai-butler"
LOG_DIR="/opt/sunguo/logs"
mkdir -p "$LOG_DIR"

cd "$PROJECT_DIR"
echo "==== $(date '+%F %T') refresh start ====" >> "$LOG_DIR/brief-refresh.log"
if ! python3 backend/app/morning_brief_demo.py --save >> "$LOG_DIR/brief-refresh.log" 2>&1; then
    # Optional modules must not prevent the focused news refresh below. The
    # dashboard can keep using the last complete bundle if one subsystem fails.
    echo "==== $(date '+%F %T') full brief returned non-zero; continuing with news refresh ====" >> "$LOG_DIR/brief-refresh.log"
fi

# Rebuild the reader-facing news module from the latest 24-hour fact pool.
# This deliberately excludes weather, TTS, avatar and reminder work.
python3 backend/app/refresh_news_digest.py >> "$LOG_DIR/brief-refresh.log" 2>&1
echo "==== $(date '+%F %T') refresh end ====" >> "$LOG_DIR/brief-refresh.log"
