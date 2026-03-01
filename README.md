# Network Monitor

Desktop Python application (PySide6) that monitors **reachability of a target** via TCP and tracks network metrics.
When the target can't be reached, it uses a **fallback probe** to distinguish "no internet connectivity" from "target not reachable".

## Demo
https://github.com/user-attachments/assets/4294c08a-38c0-484b-993d-82efdec2127e

# How It Works

The app performs a TCP connection attempt to a configured target:

- **Online**: Target reachable
- **Unreachable**: Target not reachable, but a known-good endpoint is reachable (internet is stable, target is the issue)
- **Offline**: Target and known-good endpoints are unreachable (most likely no internet connectivity)

Latency is measured as the TCP connect time (when `Online`).

## Features

- Three status states: **Online / Offline / Unreachable**
- Configurable target:
    - IP Addresses (`IPv4/IPv6`)
    - Hostnames (e.g., `google.com`)
    - URLs (e.g., `https://www.google.com/`) - Normalized to host:port
- Configurable check interval and timeout (preset radio buttons and optional custom values)
- Metrics:
    - Server (target)
    - Phase: **Online for / Offline for / Unreachable for**
    - Latency (when `Online`)
    - Disconnect count
    - Total uptime / Total downtime
- Visual Indicators via `QSS`:
    - Status pill styling for all three states (Online/Offline/Unreachable)
    - Server pill remains blue
    - Severity styling for latency and disconnects
- Status tooltip (hover) with detailed information

## Tech Stack

- Python 3.11+
- PySide6 (Qt for Python)
- Background worker thread for network checks
- QSettings for persisted configuration
- QSS for styling

## Architecture Notes (v0.8.0)

The monitoring implementation is layered for clarity and testability:

- `services/monitor/probe.py`: Performs TCP connect attempts via `try_connect`
- `services/monitor/engine.py`: Contains logic and returns a `CheckResult`
- `ui/workers/monitor_thread.py`: Runs a `QThread` loop and emits results back to the UI
- `core/monitor/state.py`: Tracks the state of the monitoring metrics

## Setup

### Option A: uv (Recommended)

```bash
uv sync
```

Run with:
```bash
uv run network-monitor
```

### Option B: venv & pip

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
```

## Run

```bash
network-monitor
```

Alternatively, run it as a module:
```bash
python -m network_monitor
```

## Roadmap

- [x] Configurable target (host:port) and interval/timeout (implemented in [v0.2.0](CHANGELOG.md#v020))
- [x] Multiple state connectivity: Online/Offline/Unreachable (implemented in [v0.5.0](CHANGELOG.md#v050))
- [x] UI polish (layout and visual indicators)
- [x] Implement target method in settings (implemented in [v0.6.0](CHANGELOG.md#v060))
- [x] Tooltips for all metrics (more detailed informations) (implemented in [v0.6.1](CHANGELOG.md#v061))
- [ ] Click-to-copy full target (URL) from the server pill
- [x] Light/Dark themes (implemented in [v0.8.1](CHANGELOG.md#v081))
- [ ] Taskbar Functionality
- [ ] Ability to resize application window
- [ ] Disconnect debounce (reduce false disconnects)
- [x] Start / Stop monitoring controls (implemented in [v0.8.2](CHANGELOG.md#v082))
- [ ] Latency statistics (min/avg/max over last N checks)
- [ ] History Viewing (recent checks table)
- [ ] Profiles (switch between configurations more easily)

## Bugs (fixed)

- [x] Statistics keep resetting on status change (fixed in [v0.3.1](CHANGELOG.md#v031))
- [x] Disconnects aren't being incremented/tracked (fixed in [v0.3.2](CHANGELOG.md#v032))
- [x] When changing interval checks and timeout checks, the current phase resets (fixed in [v0.4.0](CHANGELOG.md#v040))
- [x] When pausing the monitoring, the timer continues counting in the background (fixed in [v0.8.2](CHANGELOG.md#v083))

## Assets
- Vectors and icons by <a href="https://www.svgrepo.com" target="_blank">SVG Repo</a>

- Application icon was created by me using Canva.
