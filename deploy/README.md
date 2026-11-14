# Deployment

Service name: **data-processing**

## Linux (systemd)

```bash
sudo mkdir -p /opt/data-processing
sudo rsync -a ./ /opt/data-processing/
sudo deploy/linux/install.sh
sudo systemctl status data-processing
```

Logs land in `/var/log/data-processing/`. The control API listens on
`127.0.0.1:8000`; put nginx in front if it needs to be public.

## Windows (NSSM)

Install [NSSM](https://nssm.cc/download) first, then from an elevated
PowerShell:

```powershell
# Copy the project to the install directory first.
Copy-Item -Recurse .\* C:\Services\data-processing\
cd C:\Services\data-processing\deploy\windows
.\install_service.ps1 -AppDir C:\Services\data-processing -Nssm C:\tools\nssm.exe
```

The service runs `python main.py`, restarts on failure, and writes logs to
`C:\ProgramData\data-processing\logs`. If you need public HTTP, point IIS
at `http://localhost:8000` using `web.config` (reverse proxy only — IIS
must not host the workers).

## Env vars honored by the service

| Variable            | Default | Purpose                      |
|---------------------|---------|------------------------------|
| `SERVICE_LOG_DIR`   | `logs`  | Where log files are written  |
| `SERVICE_LOG_LEVEL` | `INFO`  | Root log level               |
