# my_service

Supervisor + worker-process Python service. One command starts a single
process (the **supervisor**), which starts each **unit** in its own OS
process so a slow or crashed unit cannot block the others. A FastAPI
control plane exposes `/health` and `/units` plus start/stop endpoints.

## Layout

```
my_service/
  main.py                 # entry: load config, start supervisor + API
  config/settings.yaml    # which units run and their params
  core/
    base_unit.py          # the BaseUnit contract and child entry point
    supervisor.py         # spawns, watches, restarts and stops units
    registry.py           # maps unit names -> classes
    messaging.py          # multiprocessing.Queue bus between units
    logging_setup.py      # per-unit rotating log files
  api/control.py          # FastAPI endpoints
  units/
    order_sync/           # sample producer unit
    report_gen/           # sample consumer unit
  deploy/
    linux/                # systemd unit + install script
    windows/              # NSSM install script + optional IIS proxy
  tests/
```

## Run it

```bash
python -m venv venv
venv\Scripts\pip install -r requirements.txt    # Windows
# or: ./venv/bin/pip install -r requirements.txt
python main.py
```

Then:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/units
curl -X POST http://127.0.0.1:8000/units/order_sync/stop
curl -X POST http://127.0.0.1:8000/units/order_sync/start
```

Logs land in `./logs/` (`supervisor.log`, `unit_<name>.log`).

## Add a unit

1. Create `units/<name>/unit.py` with a `BaseUnit` subclass.
2. Add it to `core/registry.py`.
3. Enable it in `config/settings.yaml`.

Nothing else changes.

## How it fits together

- **Isolation.** `multiprocessing.Process` per unit. No shared GIL, no
  shared memory — a crash stays inside its own process.
- **Supervisor.** Reads config, starts enabled units, polls `is_alive()`
  every 5 s, restarts dead units with exponential backoff, shuts them
  all down on SIGTERM.
- **Unit contract.** `setup() / run() / teardown()`, with a shared
  `stop_event` the unit checks in its loop.
- **Communication.** `multiprocessing.Queue`-backed bus. Units declare
  `produces` / `consumes` topics in config; the supervisor wires the
  queues. Swap for Redis/RabbitMQ later without changing unit code.
- **Cross-platform.** `mp.set_start_method("spawn")` is called from the
  `__main__` guard so Windows and Linux behave identically.

See `deploy/README.md` for systemd and Windows service setup.
