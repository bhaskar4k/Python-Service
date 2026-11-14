#!/usr/bin/env bash
# Install data-processing as a systemd service. Run as root.
set -euo pipefail

SERVICE_NAME=${SERVICE_NAME:-data-processing}
APP_DIR=${APP_DIR:-/opt/${SERVICE_NAME}}
USER_NAME=${USER_NAME:-${SERVICE_NAME}}
LOG_DIR=${LOG_DIR:-/var/log/${SERVICE_NAME}}

id -u "$USER_NAME" >/dev/null 2>&1 || useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin "$USER_NAME"
mkdir -p "$APP_DIR" "$LOG_DIR"
chown -R "$USER_NAME:$USER_NAME" "$APP_DIR" "$LOG_DIR"

python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

install -m 644 "$(dirname "$0")/${SERVICE_NAME}.service" "/etc/systemd/system/${SERVICE_NAME}.service"
systemctl daemon-reload
systemctl enable --now "${SERVICE_NAME}"
systemctl --no-pager status "${SERVICE_NAME}"
