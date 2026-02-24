import socket
import errno
import time


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
    except (socket.timeout, TimeoutError):
        return False, None, "timeout"
    except OSError as exc:
        if exc.errno == errno.ETIMEDOUT:
            return False, None, "timeout"
        if exc.errno == errno.ECONNREFUSED:
            return False, None, "refused"
        if exc.errno in (errno.ENETUNREACH, errno.EHOSTUNREACH):
            return False, None, "no-route"
        return False, None, "oserror"
