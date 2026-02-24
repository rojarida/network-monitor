from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SettingsDialogState:
    method: str
    ip_address: str
    ip_port: int
    hostname: str
    url: str


@dataclass(frozen=True)
class SettingsData:
    target_method: str
    target_text: str

    host: str
    port: int
    display_target: str
    full_target: str
    port_was_explicit: bool

    interval_seconds: float
    timeout_seconds: float

