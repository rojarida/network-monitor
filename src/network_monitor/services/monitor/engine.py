from __future__ import annotations

import time
from collections.abc import Callable

from network_monitor.core.monitor import CheckResult
from .probe import try_connect


DEFAULT_PROBE_ENDPOINTS: tuple[tuple[str, int], ...] = (
    ("1.1.1.1", 443),
    ("1.0.0.1", 443),
)


def check_once(
    server: str,
    port: int,
    timeout_seconds: float,
    *,
    probe_endpoints: tuple[tuple[str, int], ...] = DEFAULT_PROBE_ENDPOINTS,
    should_stop: Callable[[], bool] | None = None,
) -> CheckResult:
    def stopping() -> bool:
        return should_stop is not None and should_stop()

    # Target connect (cannot be interrupted mid-call)
    target_ok, target_latency_ms, target_error_kind = try_connect(
        server, port, timeout_seconds
    )

    if target_ok:
        return CheckResult(
            status="online",
            latency_ms=target_latency_ms,
            timestamp=time.monotonic(),
            error_kind=None,
        )

    # Probes (stop-aware)
    probe_ok = False
    for probe_host, probe_port in probe_endpoints:
        if stopping():
            break
        ok, _, _ = try_connect(probe_host, probe_port, timeout_seconds)
        if ok:
            probe_ok = True
            break

    status = "unreachable" if probe_ok else "offline"
    return CheckResult(
        status=status,
        latency_ms=None,
        timestamp=time.monotonic(),
        error_kind=target_error_kind,
    )
