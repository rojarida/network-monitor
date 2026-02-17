from __future__ import annotations

from dataclasses import dataclass
import time


@dataclass
class CheckResult:
    ok: bool
    latency_ms: float | None
    timestamp: float


@dataclass
class MonitorState:
    server: str = "1.1.1.1"
    port: int = 443

    disconnects: int = 0
    total_uptime_seconds: float = 0.0
    total_downtime_seconds: float = 0.0

    last_status_ok: bool | None = None
    last_state_change_time: float = 0.0
    last_latency_ms: float | None = None

    pending_disconnect_if_first_result_down: bool = False


    def start(self) -> None:
        now = time.monotonic()
        self.last_status_ok = None
        self.last_state_change_time = now


    def apply(self, check_result: CheckResult) -> None:
        # Store latency on when UP
        self.last_latency_ms = check_result.latency_ms if check_result.ok else None

        # First check after startup or endpoint change
        if self.last_status_ok is None:
            if self.pending_disconnect_if_first_result_down and (check_result.ok is False):
                self.disconnects += 1

            self.pending_disconnect_if_first_result_down = False
            self.last_status_ok = check_result.ok
            self.last_state_change_time = check_result.timestamp
            return
        
        # No status change
        if check_result.ok == self.last_status_ok:
            return

        elapsed_in_previous_state = max(0.0, check_result.timestamp - self.last_state_change_time)

        if self.last_status_ok:
            self.total_uptime_seconds += elapsed_in_previous_state
            # last_status_ok is True and transition implies DOWN
            self.disconnects += 1
        else:
            self.total_downtime_seconds += elapsed_in_previous_state

        self.last_status_ok = check_result.ok
        self.last_state_change_time = check_result.timestamp


    def endpoint_changed(self) -> None:
        # Keep totals, but close out current phase and restart tracking
        now = time.monotonic()

        # Check status before switching endpoints
        was_up_before_change = (self.last_status_ok is True)

        # If in a known state, finalize the current phase into totals
        if self.last_status_ok is not None:
            elapsed = max(0.0, now - self.last_state_change_time)
            if self.last_status_ok:
                self.total_uptime_seconds += elapsed
            else:
                self.total_downtime_seconds += elapsed

        # New endpoint starts "unknown"
        self.last_status_ok = None
        self.last_state_change_time = now
        self.last_latency_ms = None

        # If status was previously UP, and the endpoint status is DOWN
        # Consider it as a disconnect
        self.pending_disconnect_if_first_result_down = was_up_before_change


    def current_phase_seconds(self) -> float:
        return max(0.0, time.monotonic() - self.last_state_change_time)

    
    def totals_including_current_phase(self) -> tuple[float, float]:
        total_uptime = self.total_uptime_seconds
        total_downtime = self.total_downtime_seconds
        current_phase = self.current_phase_seconds()

        if self.last_status_ok is None:
            return (total_uptime, total_downtime)

        if self.last_status_ok:
            total_uptime += current_phase
        else:
            total_downtime += current_phase

        return (total_uptime, total_downtime)
