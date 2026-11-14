#!/usr/bin/env bash
# Install my_service as a systemd service. Run as root.
set -euo pipefail

APP_DIR=${APP_DIR:-/opt/my_service}
USER_NAME=${USER_NAME:-myservice}

id -u "$USER_NAME" >/dev/null 2>&1 || useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin "$USER_NAME"
mkdir -p "$APP_DIR" /var/log/my_service
chown -R "$USER_NAME:$USER_NAME" "$APP_DIR" /var/log/my_service

python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

install -m 644 "$(dirname "$0")/my_service.service" /etc/systemd/system/my_service.service
systemctl daemon-reload
systemctl enable --now my_service
systemctl --no-pager status my_service
