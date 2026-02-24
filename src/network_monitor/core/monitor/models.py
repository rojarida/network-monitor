from typing import Literal

from dataclasses import dataclass


ConnectionStatus = Literal["online", "offline", "unreachable"]


@dataclass
class CheckResult:
    status: ConnectionStatus
    latency_ms: float | None
    timestamp: float
    error_kind: str | None = None
