# Deployment

## Linux (systemd)

```bash
sudo mkdir -p /opt/my_service
sudo rsync -a ./ /opt/my_service/
sudo deploy/linux/install.sh
sudo systemctl status my_service
```

Logs land in `/var/log/my_service/`. The control API listens on
`127.0.0.1:8000`; put nginx in front if it needs to be public.

## Windows (NSSM)

Install [NSSM](https://nssm.cc/download) first, then from an elevated
PowerShell:

```powershell
# Copy the project to the install directory first.
Copy-Item -Recurse .\* C:\Services\my_service\
cd C:\Services\my_service\deploy\windows
.\install_service.ps1 -AppDir C:\Services\my_service -Nssm C:\tools\nssm.exe
```

The service runs `python main.py`, restarts on failure, and writes logs to
`C:\ProgramData\my_service\logs`. If you need public HTTP, point IIS at
`http://localhost:8000` using `web.config` (reverse proxy only — IIS must
not host the workers).
