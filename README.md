# data-processing

Supervisor + worker-process Python service. One command starts a single
process (the **supervisor**), which starts each **unit** in its own OS
process so a slow or crashed unit cannot block the others. A FastAPI
control plane exposes `/health` and `/units` plus start/stop endpoints.

The service's display name comes from [`config/settings.yaml`](config/settings.yaml)
under `service.name` and is used by the API title and startup log.

## Layout

```
data-processing/
  main.py                 # entry: load config, start supervisor + API
  config/settings.yaml    # service name, which units run, their params
  core/
    base_unit.py          # the BaseUnit contract and child entry point
    supervisor.py         # spawns, watches, restarts and stops units
    registry.py           # maps unit names -> classes
    logging_setup.py      # per-unit rotating log files
  api/control.py          # FastAPI endpoints
  units/
    ingestion/
    pre_processing/
    processing/
    post_processing/
  deploy/
    linux/                # systemd unit + install script
    windows/              # NSSM install script + optional IIS proxy
  tests/
```

## Run it

```bash
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt    # Windows
# or: ./.venv/bin/pip install -r requirements.txt
.\.venv\Scripts\python main.py                     # Windows
```

Then:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/units
curl -X POST http://127.0.0.1:8000/units/ingestion/stop
curl -X POST http://127.0.0.1:8000/units/ingestion/start
```

Logs land in `./logs/` (`supervisor.log`, `unit_<name>.log`).

## Add a unit

1. Create `units/<name>/unit.py` with a `BaseUnit` subclass.
2. Add it to `core/registry.py`.
3. Enable it in `config/settings.yaml`.

Nothing else changes.

## Env vars

| Variable            | Default | Purpose                      |
|---------------------|---------|------------------------------|
| `SERVICE_LOG_DIR`   | `logs`  | Where log files are written  |
| `SERVICE_LOG_LEVEL` | `INFO`  | Root log level               |

See `deploy/README.md` for systemd and Windows service setup.
