from __future__ import annotations

from pathlib import Path
from typing import Literal

from PySide6.QtCore import QObject, QFileSystemWatcher, QTimer, Qt
from PySide6.QtWidgets import QApplication


ThemeName = Literal["dark", "light"]


class ThemeManager(QObject):
    def __init__(self, app: QApplication) -> None:
        super().__init__()
        self._app = app
        self._current_theme: ThemeName | None = None # None means "system"

        # Use real file paths
        self._themes_dir = Path(__file__).resolve().parent
        self._base_path = self._themes_dir / "base.qss"
        self._dark_path = self._themes_dir / "dark.qss"
        self._light_path = self._themes_dir / "light.qss"

        self._watcher = QFileSystemWatcher(self)

        self._reload_timer = QTimer(self)
        self._reload_timer.setSingleShot(True)
        self._reload_timer.setInterval(120)
        self._reload_timer.timeout.connect(self._reapply_current)

        self._watcher.fileChanged.connect(self._schedule_reload)
        self._watcher.directoryChanged.connect(self._schedule_reload)


    def _read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")


    def _build_stylesheet(self, theme_name: ThemeName) -> str:
        base_qss = self._read_text(self._base_path)
        theme_qss = self._read_text(self._themes_dir / f"{theme_name}.qss")
        return f"{base_qss}\n\n/* ---- Theme: {theme_name} ---- */\n\n{theme_qss}\n"


    def apply_theme(self, theme_name: ThemeName) -> None:
        self._current_theme = theme_name
        self._app.setStyleSheet(self._build_stylesheet(theme_name))


    def apply_system_theme(self) -> None:
        self._current_theme = None
        theme_name = self._get_system_theme()
        self._app.setStyleSheet(self._build_stylesheet(theme_name))


    def _get_system_theme(self) -> ThemeName:
        style_hints = self._app.styleHints()

        if hasattr(style_hints, "colorScheme") and hasattr(Qt, "ColorScheme"):
            try:
                return "dark" if style_hints.colorScheme() == Qt.ColorScheme.Dark else "light"
            except Exception:
                pass

        # Fallback
        palette = self._app.palette()
        window_color = palette.color(palette.ColorRole.Window)
        red = window_color.red()
        green = window_color.green()
        blue = window_color.blue()

        luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
        return "dark" if luminance < 128 else "light"


    def enable_live_reload(self) -> None:
        # Watch directory and files
        self._watcher.addPath(str(self._themes_dir))
        self._watcher.addPath(str(self._base_path))
        self._watcher.addPath(str(self._dark_path))
        self._watcher.addPath(str(self._light_path))


    def _schedule_reload(self, _changed_path: str) -> None:
        self._reload_timer.start()


    def _reapply_current(self) -> None:
        watched = set(self._watcher.files())
        for path in (self._base_path, self._dark_path, self._light_path):
            path_str = str(path)
            if path.exists() and path_str not in watched:
                self._watcher.addPath(path_str)

        if self._current_theme is None:
            self.apply_theme(self._get_system_theme())
        else:
            self.apply_theme(self._current_theme)
