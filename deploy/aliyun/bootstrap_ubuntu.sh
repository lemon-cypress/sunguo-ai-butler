#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/lemon-cypress/sunguo-ai-butler.git"
PROJECT_ROOT="/opt/sunguo"
PROJECT_DIR="/opt/sunguo/ai-butler"
SERVICE_NAME="sunguo-dashboard"
NGINX_SOURCE="deploy/aliyun/sunguo.nginx.conf"
SERVICE_SOURCE="deploy/aliyun/sunguo-dashboard.service"

sudo apt update
sudo apt install -y python3 python3-pip nginx git nodejs npm

sudo mkdir -p "$PROJECT_ROOT"
sudo chown -R "$USER":"$USER" "$PROJECT_ROOT"

if [ ! -d "$PROJECT_DIR/.git" ]; then
  cd "$PROJECT_ROOT"
  git clone "$REPO_URL" ai-butler
fi

cd "$PROJECT_DIR"
git pull
npm install

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Please edit it before public use."
fi

sudo cp "$SERVICE_SOURCE" /etc/systemd/system/${SERVICE_NAME}.service

if [ -d /etc/nginx/sites-available ]; then
  sudo cp "$NGINX_SOURCE" /etc/nginx/sites-available/sunguo
  if [ ! -L /etc/nginx/sites-enabled/sunguo ]; then
    sudo ln -s /etc/nginx/sites-available/sunguo /etc/nginx/sites-enabled/sunguo
  fi
else
  sudo cp "$NGINX_SOURCE" /etc/nginx/conf.d/sunguo.conf
fi

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"
sudo nginx -t
sudo systemctl reload nginx

sudo systemctl status "$SERVICE_NAME" --no-pager
