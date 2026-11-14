# data-processing

A supervisor + worker-process Python service. One command starts a single
process (the **supervisor**), which launches each **unit** in its own OS
process so a slow or crashed unit cannot block the others. A small FastAPI
**control plane** runs inside the supervisor and exposes health, status,
and per-unit start/stop endpoints.

The service's display name, the HTTP listener, logging, and which units
run are all driven by [`config/settings.yaml`](config/settings.yaml) — no
code change needed to flip a unit on or off or retune cadence.

Default units (four independent pipeline stages, no messaging between
them):

| Unit              | Default cadence | What it does (stub)                          |
|-------------------|-----------------|----------------------------------------------|
| `ingestion`       | every 3 s       | pretends to pull raw data from some source   |
| `pre_processing`  | every 4 s       | pretends to clean and validate it            |
| `processing`      | every 5 s       | pretends to run the main business logic      |
| `post_processing` | every 6 s       | pretends to publish or persist final results |

## Layout

```
data-processing/
├── main.py                       # entry: load config, start supervisor + API
├── config/
│   └── settings.yaml             # service name, logging, API, enabled units
├── core/
│   ├── base_unit.py              # BaseUnit contract + child-process entry point
│   ├── supervisor.py             # spawns, watches, restarts and stops units
│   ├── registry.py               # maps unit names -> classes
│   └── logging_setup.py          # rotating per-unit log files (env/YAML driven)
├── api/
│   └── control.py                # FastAPI endpoints (/health, /units, start, stop)
├── units/
│   ├── ingestion/unit.py
│   ├── pre_processing/unit.py
│   ├── processing/unit.py
│   └── post_processing/unit.py
├── deploy/
│   ├── linux/                    # systemd unit + install.sh
│   └── windows/                  # NSSM install_service.ps1 + IIS web.config
├── shared/                       # reserved for shared helpers
├── tests/
├── requirements.txt
├── pyproject.toml
└── logs/                         # created at runtime (not committed)
```

## Run it (local dev)

**Windows:**

```powershell
cd "E:\Project\Python Service"
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python main.py
```

**Linux / macOS:**

```bash
cd data-processing
python -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python main.py
```

Stop with `Ctrl+C` in that terminal — the supervisor catches the signal,
tells every unit to finish, joins each one with a 10 s timeout, and exits.

Logs land in `./logs/` by default:

- `logs/supervisor.log` — the supervisor's own view
- `logs/unit_<name>.log` — one file per unit process

### Nice-to-have on Windows: named processes

When launched from a venv, the supervisor copies the base Python interpreter
into `.venv\Scripts\` as `unit_<name>.exe` and uses that to spawn each
worker. Task Manager then shows the unit by name instead of a generic
`python.exe`. If the destination isn't writable (e.g. you launched using a
system-wide Python), the fallback works fine but Task Manager keeps the
generic name.

## Control API

Served on `127.0.0.1:8000` by default. The title and version shown at
`/docs` come from `service.name` and `api.version` in
[`config/settings.yaml`](config/settings.yaml).

| Method | Path                       | Purpose                                 |
|--------|----------------------------|-----------------------------------------|
| GET    | `/health`                  | `{"status":"ok","units_alive":N,...}`   |
| GET    | `/units`                   | PID, alive-status, restarts for each    |
| POST   | `/units/{name}/start`      | start a single unit                     |
| POST   | `/units/{name}/stop`       | stop a single unit (service stays up)   |
| GET    | `/docs`                    | Swagger UI                              |

Examples:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/units
curl -X POST http://127.0.0.1:8000/units/ingestion/stop
curl -X POST http://127.0.0.1:8000/units/ingestion/start
```

> ⚠️ The API has no auth and binds to `127.0.0.1` on purpose. If you
> expose it outside the box, put nginx / IIS in front and add auth.

## Configuration — [config/settings.yaml](config/settings.yaml)

```yaml
service:
  name: "data-processing"      # shows up in the API title + startup log

logging:
  dir: "logs"                  # relative paths resolve to the working dir
  level: "INFO"                # DEBUG, INFO, WARNING, ERROR, CRITICAL
  console: true                # also print log lines to the terminal

api:
  host: "127.0.0.1"
  port: 8000
  version: "0.1.0"
  # title: "custom title"      # optional; defaults to "<service.name> control"

units:
  ingestion:
    enabled: true
    cfg:
      interval_seconds: 3.0
  pre_processing:
    enabled: true
    cfg:
      interval_seconds: 4.0
  processing:
    enabled: true
    cfg:
      interval_seconds: 5.0
  post_processing:
    enabled: true
    cfg:
      interval_seconds: 6.0
```

- Flip a unit off: set its `enabled: false` and restart.
- Change a unit's cadence: edit its `interval_seconds`.
- Override logging without touching YAML: set the env vars below.

## Env-var overrides (take precedence over YAML)

| Variable            | Default (YAML value) | Purpose                     |
|---------------------|----------------------|-----------------------------|
| `SERVICE_LOG_DIR`   | `logs`               | Where log files are written |
| `SERVICE_LOG_LEVEL` | `INFO`               | Root log level              |
| `SERVICE_LOG_CONSOLE` | `true`             | Also print log lines to the console (`0` / `false` turns it off) |

The deploy scripts set these per-machine so systemd / NSSM can route logs
into system directories without touching YAML. The Windows service sets
`SERVICE_LOG_CONSOLE=0` so log lines aren't duplicated into NSSM's
`service.err.log`.

## Add a new unit

1. Create `units/<name>/unit.py` with a `BaseUnit` subclass:

   ```python
   from core.base_unit import BaseUnit

   class MyUnit(BaseUnit):
       name = "my_unit"

       def setup(self):
           self._interval = float(self.cfg.get("interval_seconds", 5.0))

       def run(self):
           while not self.stop.is_set():
               self.log.info("hello from my_unit")
               if self.stop.wait(self._interval):
                   return
   ```

2. Register it in [core/registry.py](core/registry.py):

   ```python
   UNIT_PATHS = {
       # ...
       "my_unit": "units.my_unit.unit:MyUnit",
   }
   ```

3. Enable it in [config/settings.yaml](config/settings.yaml):

   ```yaml
   units:
     my_unit:
       enabled: true
       cfg:
         interval_seconds: 5.0
   ```

Restart. Nothing else changes.

## How it fits together

- **Isolation.** `multiprocessing.Process` per unit (spawn start method on
  every OS). No shared GIL, no shared memory — a crash stays inside its
  own process.
- **Supervisor.** Reads config, starts enabled units, polls `is_alive()`
  every 5 s, restarts dead units with exponential backoff (capped at
  60 s), and tears them down cleanly on SIGINT / SIGTERM.
- **Unit contract.** Each unit implements `setup()` / `run()` / `teardown()`
  and watches a shared `stop_event` the supervisor sets at shutdown.
- **No coupling.** Units don't talk to each other. If two need to
  communicate later, the right fix is a real broker (Redis / RabbitMQ) —
  not in-memory queues that die on restart.
- **Cross-platform.** `mp.set_start_method("spawn", force=True)` lives
  inside the `__main__` guard so Windows and Linux behave identically.

## Deploy

See [deploy/README.md](deploy/README.md) for the full writeup. In short:

- **Linux (systemd):** `sudo deploy/linux/install.sh` installs it as the
  `data-processing` unit. Logs to `/var/log/data-processing/`.
- **Windows (NSSM):** `deploy/windows/install_service.ps1` registers it
  as a Windows Service named `data-processing`. Logs to
  `C:\ProgramData\data-processing\logs\`.

Both routes autostart on boot, restart on failure, and expose the same
control API on `127.0.0.1:8000`.

## Stop / kill reference

**Running in a terminal:** `Ctrl+C`.

**Running as a Windows service:**

```powershell
nssm stop data-processing
# or
Stop-Service data-processing
```

**Running as a systemd service:**

```bash
sudo systemctl stop data-processing
```

**Orphaned processes (last resort):**

```powershell
Get-CimInstance Win32_Process |
  Where-Object { $_.Name -eq 'python.exe' -and
                 ($_.CommandLine -match 'Python Service' -or
                  $_.CommandLine -match 'multiprocessing.spawn') } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

## What this design is **not** good at

Small to medium always-on service on one box. It's not meant for:

- durable messaging between units (no persistence — use a broker)
- multi-machine HA (no distributed coordination)
- public-facing admin (no auth on the control API)
- high-throughput message passing (pickle + queue overhead if you add one)

For the limits of this shape and when to outgrow it, see the end of the
design notes or ask.
