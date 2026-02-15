# Network Monitor

Desktop Python application (PySide6) that monitors basic internet connectivity by periodically checking a known endpoint and tracking uptime/downtime statistics.

## Features
- Connectivity checks to a known server (Default: `1.1.1.1:443`)
- Displays status (UP/DOWN) and latency
- Tracks disconnect count, total uptime, total downtime, and current phase time

## Tech Stack
- Python 3.11+
- PySide6 (Qt for Python)
- Background worker thread for network checks

## Project Structure
```text
.
├── pyproject.toml
├── README.md
└── src
    └── network_monitor
        ├── app.py
        ├── __init__.py
        ├── __main__.py
        ├── monitor
        │   ├── __init.py
        │   └── thread.py
        ├── state.py
        └── ui
            ├── __init__.py
            └── main_window.py
```

## Setup

### Option A: uv (Recommended)

```bash
uv venv
uv pip install -e .
```

### Option B: venv & pip

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Run
```bash
python -m network_monitor
```

## Roadmap
- [ ] Configurable endpoint (server, port) and interval
- [ ] Disconnect debounce (reduce false disconnects)
- [ ] Start / Stop monitoring controls
- [ ] Latency statistics (minimum/average/maximum over last N checks)
- [ ] History Viewing (recent checks table)
- [ ] UI Polish (improved layout and clear visual indicators)

## Changes
- 0.1.0 - Initial working GUI with TCP connectivity checks (`1.1.1.1:443`) and basic network statistics.
