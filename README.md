# Network Monitor

Desktop Python application (PySide6) that monitors **reachability of a target** via TCP and tracks network metrics.
When the target can't be reached, it uses a **fallback probe** to distinguish "no internet connectivity" from "target not reachable".

## Screenshots

<h3 align="center">Online</h3>
<p align="center">
    <img src="assets/screenshots/online.png" alt="Online">
</p>

<h3 align="center">Unreachable</h3>
<p align="center">
    <img src="assets/screenshots/unreachable.png" alt="Unreachable">
</p>

<h3 align="center">Offline</h3>
<p align="center">
    <img src="assets/screenshots/offline.png" alt="Offline">
</p>

# How It Works

The app performs a TCP connection attempt to a configured target:

- **Online**: Target reachable
- **Unreachable**: Target not reachable, but a known-good endpoint is reachable (internet is stable, target is the issue)
- **Offline**: Target and known-good endpoints are unreachable (most likely no internet connectivity)

Latency is measured as the TCP connect time (when `Online`).

## Features

- Three status states: **Online / Offline / Unreachable**
- Configurable target:
    - IP Addresses (IPv4/IPv6)
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

## Project Structure

```text
.
├── assets
│   ├── icons
│   │   └── network-monitor_256x256.png
│   └── screenshots
│       ├── offline.png
│       ├── online.png
│       └── unreachable.png
├── NetworkMonitor.spec
├── pyproject.toml
├── README.md
├── src
│   └── network_monitor
│       ├── app.py
│       ├── __init__.py
│       ├── __main__.py
│       ├── monitor
│       │   ├── __init__.py
│       │   └── thread.py
│       ├── state.py
│       └── ui
│           ├── __init__.py
│           ├── main_window.py
│           ├── monitor_view.py
│           ├── settings_dialog.py
│           ├── styles
│           │   ├── app.qss
│           │   └── __init__.py
│           └── tooltips.py
└── uv.lock
```

## Setup

### Option A: uv (Recommended)

```bash
uv venv
uv pip install -e .
```

### Option B: venv & pip

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip install -e .
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

- [x] Configurable target (host:port) and interval/timeout (implemented in [0.2.0](#020))
- [x] Multiple state connectivity: Online/Offline/Unreachable (implemented in [0.5.0](#050))
- [x] UI polish (layout and visual indicators)
- [x] Implement target method in settings (implemented in [0.6.0](#060))
- [x] Tooltips for all metrics (more detailed informations) (implemented in [0.6.1](#061))
- [ ] Click-to-copy full target (URL) from the server pill
- [ ] Light/Dark themes
- [ ] Taskbar Functionality
- [ ] Ability to resize application window
- [ ] Disconnect debounce (reduce false disconnects)
- [ ] Start / Stop monitoring controls
- [ ] Latency statistics (min/avg/max over last N checks)
- [ ] History Viewing (recent checks table)
- [ ] Profiles (switch between configurations more easily)

## Bugs (fixed)

- [x] Statistics keep resetting on status change (fixed in [0.3.1](#031))
- [x] Disconnects aren't being incremented/tracked (fixed in [0.3.2](#032))
- [x] When changing interval checks and timeout checks, the current phase resets (fixed in [0.4.0](#040))

## Changelog
### 0.1.0
Initial working GUI with TCP connectivity checks (`1.1.1.1:443`) and basic network statistics.

### 0.2.0
Added a settings dialog to configure the target:
- Server IP
- Port

Added selectable monitoring parameters:
- Check interval (preset radio buttons and optional custom values)
- Timeout (preset radio buttons and optional custom values)

Settings persist between launches.

### 0.3.0
Fixed an issue where configurations weren't persistent.

Improved UI
- Metric rows
- Statistics are now in green, pills
- Tightened the spacing surrounding the settings button and status

### 0.3.1
Fixed issue where the metrics were being reset to default when changing settings.

### 0.3.2
Fixed issue where disconnects wasn't functioning properly.

### 0.3.3
Disconnect severity coloring:
- 0: Green
- 1 - 9: Yellow
- 10+: Red

### 0.3.4
Similar to [0.3.3](#033), latency severity coloring:
- <100ms: Green
- 100 - 199ms: Yellow
- 200+ms: Red

### 0.3.5
Layout refactor and additional UI polishing.

### 0.4.0
Fixed issue where the uptime/downtime was resetting when changing endpoints.
- Phase timers are now preserved on setting change

### 0.5.0
Added a third connectivity state: `Unreachable`
- Uses a fallback probe to distinguish `Offline` (no internet connectivity) from `Unreachable` (internet is stable, target is the issue)

Settings now accepts three methods for configuring a target
- IP Addresses (IPv4/IPv6)
- Hostnames (`google.com`)
- URLs (e.g., `https://www.google.com/`)

Updated UI and styling to support the **Server Unreachable** state 

Added a status tooltip (hover) with extra details

### 0.6.0
Added
- Target Method selection in Settings: **IP Adress, Hostname, or URL**
- Hostname input now supports `host[:port]` (port defaults to 443 if omitted)
- URL input supports full URLs
- Server pill now displays a "clean" target
    - Hides default ports for Hostname/URL unless explicitly provided

Changed
- Server pill text handling
    - Long targets are now middle-elided to prevent UI breaking
    - Full target available on hover

Fixed
- Prevented long hostnames from breaking the layout
- Improved target validation in settings

### 0.6.1
Added
- Shared tooltip system for the UI (`tooltips.py`) with centralized tooltip text for both the monitor metrics and the settings fields.
- Hover tooltips across the monitor view and settins dialog for cleaner, in-application explanations.
- Support for storing a "full target" string for URL targets so long URLs can be shown on hover.

Changed
- URL target parsing now explicitly supports only `http` and `https` schemes and handles invalid ports more safely.
- Hostname validation updated to allow single-label hostnames (device names) that do not contain a dot.

Fixed
- Hostname targets no longer incorrectly require a `.` to be considered valid (e.g., `romanjay-srv` now works).
