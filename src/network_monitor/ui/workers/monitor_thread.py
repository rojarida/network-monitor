from __future__ import annotations

import time
from typing import TYPE_CHECKING

from PySide6.QtCore import QThread, Signal

from network_monitor.services.monitor import check_once

if TYPE_CHECKING:
    from network_monitor.core.monitor import CheckResult


class MonitorThread(QThread):
    # Emits CheckResult
    result = Signal(object)

    def __init__(
        self,
        server: str,
        port: int,
        interval_seconds: float = 1.0,
        timeout_seconds: float = 1.0,
    ) -> None:
        super().__init__()
        self.server = server
        self.port = port
        self.interval_seconds = interval_seconds
        self.timeout_seconds = timeout_seconds
        self.is_running = True

    def stop(self) -> None:
        self.is_running = False
        self.requestInterruption()

    def _should_stop(self) -> bool:
        return (not self.is_running) or self.isInterruptionRequested()

    def run(self) -> None:
        while not self._should_stop():
            start = time.monotonic()

            check_result = check_once(
                self.server,
                self.port,
                self.timeout_seconds,
                should_stop=self._should_stop,
            )

            if self._should_stop():
                break

            self.result.emit(check_result)

            # Interruptible sleep
            elapsed = time.monotonic() - start
            remaining_sleep = max(0.0, self.interval_seconds - elapsed)
            sleep_ms = int(remaining_sleep * 1000)
            step_ms = 50

            while sleep_ms > 0 and not self._should_stop():
                self.msleep(min(step_ms, sleep_ms))
                sleep_ms -= step_ms
