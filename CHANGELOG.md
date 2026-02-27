# Changelog

All notable changes to this project are documented in this file.

### v0.8.3
#### Fixed
- Pause now correctly stops counting in the background.

### v0.8.2
### Added
- Play/Pause monitoring control in the footer.
- Play/Pause button behavior:
    - Running: Shows `Pause` button.
    - Paused: Shows `Play` button.
- Paused mode:
    - Status pills shows `Paused`
    - Metric pills are gray and display the text `-` to indicate frozen metrics.
- Paused styling:
    - `paused=true` property on the monitor view.

### Changed
- When paused, the `Online for` label switches to `Paused`.

### Fixed
- Prevented monitor results from updating UI while paused.
- Prevented `refresh_labels()` from overwriting paused placeholders (`-`) while paused.
- Ensured applying settings while paused does not block play/pause.
- Play/Pause button is theme-aware.

### v0.8.1
#### Added
- Light theme support (`light.qss`) in addition to the existing dark theme.
- Theme toggle button in the main window for quick switching.
- Live theme switching (instantly applies without restarting application).
- Initial theme is set based on current system theme.

#### Changed
- Improved light theme styling for better visual consistency.
- Removed default Qt standard-button icons in the settings.
- Minor UI polish for button interactions.

### v0.8.0
#### Changed
- Major internal refactor
    - Monitoring logic split into `services/monitor/probe.py` and `services/monitor/engine.py`.
    - Qt thread moved to `ui/workers/monitor_thread.py`.
    - Monitor state moved under `core/monitor/`.
    - Settings located in `persistence/settings_store.py`.
    - UI reorganized into `dialogs/`, `views/`, `widgets/`, `workers/`, and `themes/`.
- Cleaner imports using `__init__.py` re-exports.

#### Notes
- No intended behavior changes (primarily internal refactoring for long-term maintainability)

### v0.7.2
#### Changed
- Settings dialog styling and colors
- Removed preset option for check interval and timeout interval.
- Radio buttons now render as fully solid.

### v0.7.1
#### Changed
- Settings dialog redesign:
    - Layout reworked into sections (`Target`/`Check Interval`/`Timeout`).
    - Target section: Method Mini-box left-aligned while inputs fill remaining space.
    - Interval/Timeout: Presets moved into a single horizontal row with custom option underneath.
    - Custom Interval/Timeout and port field width reduced to better reflect the valid range.

#### Fixed
- Monitor thread shutdown:
    - Prevented `QThread: Destroyed while thread is still running` crash on close/restart.
    - Monitor loop is now stop-aware (checks during probes and interruptible sleep).
    - Improved timeout detection for socket connections.

#### Notes
- `light.qss` remain **IN PROGRESS** in this release.

### v0.7.0
#### Added
- Theme system groundwork:
    - `base.qss`: Shared structure/layout.
    - `dark.qss`: Dark theme.
    - `light.qss`: Light theme (**WORK IN PROGRESS**).
- `ThemeManager` for centralized theme loading.
- Live QSS reload (UI updates when `*.qss` files are saved).

#### Changed
- Replaced labels with section titles.
- Introduced a completely new settings layout.
- Settings can now be styled to match the rest of the application.
- Consistent pill styling across the UI (application primarily used dark theme at this stage.)

### v0.6.1
#### Added
- Shared tooltip system (`tooltips.py`) with centralized tooltip text for both monitor metrics and settings fields.
- Hover tooltips across the monitor view and settings for cleaner in-application explanations.
- Support for storing a "full target" string for URL targets so long URLs can be shown on hover.

#### Changed
- URL target parsing now explicitly supports only `http` and `https` schemes and handles invalid ports more safely.
- Hostname validation updated to allow single-label hostnames (e.g., `romanjay-srv`) that do not contain a dot.

#### Fixed
- Hostname targets no longer incorrectly require a `.` to be considered valid.

### v0.6.0
#### Added
- Target method selection in settings: `IP Address`, `Hostname`, and `URL`.
- Hostname input now supports `host[:port]` (port will default to scheme).
- URL input supports full URLs.
- Server pill now displays a "clean" target:
    - Hides default ports for `Hostname`/`URL` unless explicitly provided.

#### Changed
- Server pill text handling:
    - Long targets are now middle-elided to prevent layout conflicts.
    - Full target available on hover.

#### Fixed
- Prevented long hostnames from breaking the layout.
- Improved target validation in settings.

### v0.5.0
#### Added
- Third connectivity state: `Unreachable`
    - Uses a fallback probe to distinguish `OFfline` (no internet connectivity) from `Unreachable` (internet appears stable, target is the issue).
- Settings now accepts three methods for configuring a target:
    - IP Address: IPv4 and IPv6 (port spinbox)
    - Hostnames: `google.com` or `TEST-W11-PC`
    - URLs: `https://www.google.com/`
- Added a status tooltip (hover) with extra details.

#### Changed
- Updated UI and styling to support the `Unreachable` state.

### v0.4.0
#### Fixed
- Uptime/downtime no longer reset when changing endpoints.
- Phase timers are preserved on settings change.

### v0.3.5
#### Changed
- Layout refactor and additional UI polishing.

### v0.3.4
#### Changed
- Latency pill now uses severity styling:
    - `<100ms`: Green
    - `100-199ms`: Yellow
    - `>=200ms`: Red

### v0.3.3
#### Changed
- Disconnect pill now uses severity styling:
    - `0`: Green
    - `1-9`: Yellow
    - `>=10`: Red

### v0.3.2
#### Fixed
- Disconnects metric now increments correctly.

### v0.3.1
#### Fixed
- Fixed issue where metrics were being reset to default when changing settings.

### v0.3.0
#### Changed
- UI improvements:
    - Metric rows layout.
    - Statistics shown as green pills.
    - Tightened spacing surrounding the settings button aand status header.

### v0.2.0
#### Added
- Settings to configure the target (`Server IP`/`Port`).
- Selectable monitoring parameters:
    - Check Interval (preset radio buttons and optional custom values).
    - Timeout Interval (preset radio buttons and optional custom values).
- Settings persist between application launches.

### v0.1.0
#### Added
- Initial working GUI with TCP connectivity checks (`1.1.1.1:443`) and basic network statistics.


















### v0.1.0
Initial working GUI with TCP connectivity checks (`1.1.1.1:443`) and basic network statistics.

### v0.2.0
Added a settings dialog to configure the target:
- Server IP
- Port

Added selectable monitoring parameters:
- Check interval (preset radio buttons and optional custom values)
- Timeout (preset radio buttons and optional custom values)

Settings persist between launches.

### v0.3.0
Fixed an issue where configurations weren't persistent.

Improved UI
- Metric rows
- Statistics are now in green, pills
- Tightened the spacing surrounding the settings button and status

### v0.3.1
Fixed issue where the metrics were being reset to default when changing settings.

### v0.3.2
Fixed issue where disconnects wasn't functioning properly.

### v0.3.3
Disconnect severity coloring:
- 0: Green
- 1 - 9: Yellow
- 10+: Red

### v0.3.4
Similar to [v0.3.3](CHANGELOG.md#v033), latency severity coloring:
- <100ms: Green
- 100 - 199ms: Yellow
- 200+ms: Red

### v0.3.5
Layout refactor and additional UI polishing.

### v0.4.0
Fixed issue where the uptime/downtime was resetting when changing endpoints.
- Phase timers are now preserved on setting change

### v0.5.0
Added a third connectivity state: `Unreachable`
- Uses a fallback probe to distinguish `Offline` (no internet connectivity) from `Unreachable` (internet is stable, target is the issue)

Settings now accepts three methods for configuring a target
- IP Addresses (IPv4/IPv6)
- Hostnames (`google.com`)
- URLs (e.g., `https://www.google.com/`)

Updated UI and styling to support the **Server Unreachable** state 

Added a status tooltip (hover) with extra details

### v0.6.0
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

### v0.6.1
Added
- Shared tooltip system for the UI (`tooltips.py`) with centralized tooltip text for both the monitor metrics and the settings fields.
- Hover tooltips across the monitor view and settins dialog for cleaner, in-application explanations.
- Support for storing a "full target" string for URL targets so long URLs can be shown on hover.

Changed
- URL target parsing now explicitly supports only `http` and `https` schemes and handles invalid ports more safely.
- Hostname validation updated to allow single-label hostnames (device names) that do not contain a dot.

Fixed
- Hostname targets no longer incorrectly require a `.` to be considered valid (e.g., `romanjay-srv` now works).

### v0.7.0
Added
- Theme System:
    - `base.qss`: Shared structure/layout
    - `dark.qss`: Dark theme
    - `light.qss`: Light theme (**WORK IN PROGRESS**)
- ThemeManager:
    - Centralized theme loading to prepare for the themes
- Live QSS reload (`*.qss` changes update the UI when saved)

Changed
- Replaced labels with section titles
- Completely new settings layout
- Settings now is able to be styled and match the theme with the rest of the application
- Consistent pill styling
    - Application only has a dark theme at the moment

### v0.7.1
Changed
- Settings Dialog:
    - Redesigned the layout into section "cards" (Target/Check Interval/Timeout)
    - Target Section: Method Mini-box now hugs the left while inputs fill the remaining space
    - Interval/Timeout: Preset options moved into a single horizontal row with custom input underneath
    - Port field width reduced to better reflect the valid range
    - Custom Interval/Timeout field width reduced as well
- `light.qss`: Still **WORK IN PROGRESS**

Fixed
- Monitor thread shutdown:
    - Prevented `QThread: Destroyed while thread is still running` crash on close/restart
    - Made monitor loop stop-aware (checks during probes and interruptible sleep)
    - Improved timeout detection for socket connections

### v0.7.2
Changed
- Settings Dialog:
    - Added styling and colors
    - Removed a preset option for check interval and timeout interval
    - Added target preview for all target methods

Fixed
- Settings Dialog:
    - Fixed issue where custom arrows weren't clickable unless option was explicitly selected
    - Fixed issue where clickable area for custom arrows was not lining up correctly
    - Radio buttons weren't completely solid

### v0.8.0
Changed
- Major internal refactor (architecture/maintainability):
    - Monitoring logic split into `services/monitor/probe.py` (TCP connect) and `services/monitor/engine.py` (connectivity)
    - Qt worker thread moved to `ui/workers/monitor_thread.py`
    - Monitor domain state moved under `core/monitor/`
    - Settings persistence isolated in `persistence/settings_store.py`
    - UI reorganized into `dialogs/`, `views/`, `widgets/`, `workers/`, and `themes/`
- Cleaner imports using `__init__p.y` re-exports across packages

Notes
- No intended user-facing behavior changes
- Internal refactoring for long-term maintainability

### v0.8.1
Added
- Themes
    - Light theme support (`light.qss`) alongside the existing dark theme
    - Theme toggle button in the main window for quick theme switching
    - Instantly applies theme without having to restart
    - Starting application theme depends on current system theme

Changed
- Improved light theme for visual consistency
- Removed default Qt default icons in the settings
- Minor UI polish for button interactions
