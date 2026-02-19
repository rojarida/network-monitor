from __future__ import annotations

import socket
import time
import errno

from PySide6.QtCore import QThread, Signal

from network_monitor.state import CheckResult


def try_connect(
    hostname: str,
    port: int,
    timeout_s: float
    ) -> tuple[bool, float | None, str | None]:
    started = time.perf_counter()
    try:
        with socket.create_connection((hostname, port), timeout=timeout_s):
            latency_ms = (time.perf_counter() - started) * 1000.0
            return True, latency_ms, None
    except socket.gaierror:
        return False, None, "dns"
    except TimeoutError:
        return False, None, "timeout"
    except OSError as exc:
        if exc.errno == errno.ECONNREFUSED:
            return False, None, "refused"
        if exc.errno in (errno.ENETUNREACH, errno.EHOSTUNREACH):
            return False, None, "no-route"
        return False, None, "oserror"


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
        probe_endpoints: list[tuple[str, int]] = [
            ("1.1.1.1", 443),
            ("1.0.0.1", 443),
        ]

        while self.is_running:
            loop_start_time = time.monotonic()

            target_ok, target_latency_ms, target_error_kind = try_connect(
                self.server,
                self.port,
                self.timeout_s
            )

            if target_ok:
                status = "online"
                latency_ms = target_latency_ms
                error_kind = None
            else:
                # If the target failed, test if anything external can be reached
                probe_ok = False
                for probe_host, probe_port in probe_endpoints:
                    ok, _, _ = try_connect(probe_host, probe_port, self.timeout_s)
                    if ok:
                        probe_ok = True
                        break

                status = "unreachable" if probe_ok else "offline"
                latency_ms = None
                error_kind = target_error_kind

            check_result = CheckResult(
                status=status,
                latency_ms=latency_ms,
                timestamp=time.monotonic(),
                error_kind=error_kind,
            )
            
            self.result.emit(check_result)

            loop_elapsed_time = time.monotonic() - loop_start_time
            remaining_sleep_time = max(0.0, self.interval_s - loop_elapsed_time)
            self.msleep(int(remaining_sleep_time * 1000))
