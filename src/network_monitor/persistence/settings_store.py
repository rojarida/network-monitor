from __future__ import annotations

from PySide6.QtCore import QSettings

from network_monitor.core.models import SettingsData, SettingsDialogState


class SettingsStore:
    def __init__(self, settings: QSettings | None = None) -> None:
        self._settings = settings or QSettings()

    def _get_str(self, key: str, default: str) -> str:
        value = self._settings.value(key, default)

        if isinstance(value, str):
            return value
        if value is None:
            return default

        return str(value)

    def _get_int(self, key: str, default: int) -> int:
        value = self._settings.value(key, default)

        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            try:
                return int(value.strip())
            except ValueError:
                return default
        
        return default

    def _get_float(self, key: str, default: float) -> float:
        value = self._settings.value(key, default)

        if isinstance(value, bool):
            return float(int(value))
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.strip())
            except ValueError:
                return default

        return default

    def _get_bool(self, key: str, default: bool) -> bool:
        value = self._settings.value(key, default)

        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return bool(value)
        if isinstance(value, str):
            v = value.strip().lower()
            if v in {"1", "true", "yes", "on"}:
                return True
            if v in {"0", "false", "no", "off", ""}:
                return False

        return default

    def _get_float_fallback(self, keys: list[str], default: float) -> float:
        for key in keys:
            if self._settings.contains(key):
                return self._get_float(key, default)

        return default

    def _get_str_fallback(self, keys: list[str], default: str) -> str:
        for key in keys:
            if self._settings.contains(key):
                return self._get_str(key, default)

        return default

    def load_settings(self) -> SettingsData:
        host = self._get_str_fallback(["endpoint/host", "endpoint/server"], "google.com")
        interval = self._get_float_fallback(
            ["monitor/interval_seconds", "monitor/interval_s", "endpoint/interval_seconds"],
            1.0,
        )
        timeout = self._get_float_fallback(
            ["monitor/timeout_seconds", "monitor/timeout_s", "endpoint/timeout_seconds"],
            1.0,
        )

        return SettingsData(
            target_method=self._get_str("target/method", "hostname"),
            target_text=self._get_str("target/text", "google.com"),

            host=host,
            port=self._get_int("endpoint/port", 443),
            display_target=self._get_str("endpoint/display_target", "google.com"),
            full_target=self._get_str("endpoint/full_target", "google.com"),
            port_was_explicit=self._get_bool("endpoint/port_was_explicit", False),

            interval_seconds=interval,
            timeout_seconds=timeout,
        )
    
    def save_settings(self, settings: SettingsData) -> None:
        self._settings.setValue("target/method", settings.target_method)
        self._settings.setValue("target/text", settings.target_text)
        
        # Write both host keys for backward compatibility
        self._settings.setValue("endpoint/host", settings.host)
        self._settings.setValue("endpoint/server", settings.host)

        self._settings.setValue("endpoint/port", int(settings.port))
        self._settings.setValue("endpoint/display_target", settings.display_target)
        self._settings.setValue("endpoint/full_target", settings.full_target)
        self._settings.setValue("endpoint/port_was_explicit", bool(settings.port_was_explicit))

        # Write both interval keys for backward compatibility
        self._settings.setValue("monitor/interval_seconds", float(settings.interval_seconds))
        self._settings.setValue("monitor/interval_s", float(settings.interval_seconds))

        self._settings.setValue("monitor/timeout_seconds", float(settings.timeout_seconds))
        self._settings.setValue("monitor/timeout_s", float(settings.timeout_seconds))

        self._settings.sync()

    def load_dialog_state(self) -> SettingsDialogState:
        return SettingsDialogState(
            method=self._get_str("target/method", ""),
            ip_address=self._get_str("endpoint/ip_address", ""),
            ip_port=self._get_int("endpoint/ip_port", 443),
            hostname=self._get_str("endpoint/hostname", ""),
            url=self._get_str("endpoint/url", ""),
        )

    def save_dialog_state(self, state: SettingsDialogState) -> None:
        self._settings.setValue("target/method", state.method)
        self._settings.setValue("endpoint/ip_address", state.ip_address)
        self._settings.setValue("endpoint/ip_port", state.ip_port)
        self._settings.setValue("endpoint/hostname", state.hostname)
        self._settings.setValue("endpoint/url", state.url)

        self._settings.sync()
