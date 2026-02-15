from __future__ import annotations

import socket
import time

from PySide6.QtCore import QThread, Signal

from network_monitor.state import CheckResult


class MonitorThread(QThread):
    result = Signal(object)


    def __init__(
        self,
        server: str,
        port: int,
        interval_s: float = 1.0,
        timeout_s: float = 1.0,
    ) -> None:
        super().__init__()
        self.server = server
        self.port = port
        self.interval_s = interval_s
        self.timeout_s = timeout_s
        self.is_running = True


    def stop(self) -> None:
        self.is_running = False


    def run(self) -> None:
        while self.is_running:
            loop_start_time = time.monotonic()

            is_online = False
            latency_ms: float | None = None

            try:
                connection_start_time = time.monotonic()
                with socket.create_connection(
                        (self.server, self.port),
                        timeout=self.timeout_s
                    ):
                        pass
                connection_end_time = time.monotonic()

                is_online = True
                latency_ms = (connection_end_time - connection_start_time) * 1000.0
            
            except OSError:
                is_online = False
                latency_ms = None

            check_result = CheckResult(
                ok=is_online,
                latency_ms=latency_ms,
                timestamp=time.monotonic(),
            )
            self.result.emit(check_result)

            loop_elapsed_time = time.monotonic() - loop_start_time
            remaining_sleep_time = max(0.0, self.interval_s - loop_elapsed_time)
            self.msleep(int(remaining_sleep_time * 1000))
