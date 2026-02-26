from __future__ import annotations

from dataclasses import dataclass

import time

from .models import ConnectionStatus, CheckResult


@dataclass
class MonitorState:
    server: str = "1.1.1.1"
    port: int = 443

    disconnects: int = 0
    total_uptime_seconds: float = 0.0
    total_downtime_seconds: float = 0.0

    last_status: ConnectionStatus | None = None
    last_state_change_time: float = 0.0
    last_latency_ms: float | None = None
    last_error_kind: str | None = None


    def start(self) -> None:
        now = time.monotonic()
        self.last_status = None
        self.last_state_change_time = now
        self.last_latency_ms = None
        self.last_error_kind = None

    def apply(self, check_result: CheckResult) -> None:
        # Store latest "detail" information
        self.last_error_kind = check_result.error_kind
        self.last_latency_ms = (
            check_result.latency_ms if check_result.status == "online" else None
        )

        # First check after startup or endpoint change
        if self.last_status is None:
            self.last_status = check_result.status
            self.last_state_change_time = check_result.timestamp
            return

        # No state change
        if check_result.status == self.last_status:
            return

        elapsed_in_previous_state = max(0.0, check_result.timestamp - self.last_state_change_time)

        # Close out previous phase
        if self.last_status == "online":
            self.total_uptime_seconds += elapsed_in_previous_state

            # Only count a disconnect when leaving online
            if check_result.status != "online":
                self.disconnects +=1
        
        else:
            # Offline/unreachable both count as downtime
            self.total_downtime_seconds += elapsed_in_previous_state

        # Start new phase
        self.last_status = check_result.status
        self.last_state_change_time = check_result.timestamp

    def set_endpoint(self, server: str, port: int) -> None:
        if self.server == server and self.port == port:
            return

        self.server = server
        self.port = port
        self.last_latency_ms = None
        self.last_error_kind = None

    def endpoint_changed(self) -> None:
        """
        Endpoint changes are NOT connectivity changes.
        """
        self.last_latency_ms = None
        self.last_error_kind = None

    def current_phase_seconds(self) -> float:
        return max(0.0, time.monotonic() - self.last_state_change_time)
    
    def totals_including_current_phase(self) -> tuple[float, float]:
        total_uptime = self.total_uptime_seconds
        total_downtime = self.total_downtime_seconds
        current_phase = self.current_phase_seconds()

        if self.last_status is None:
            return (total_uptime, total_downtime)

        if self.last_status == "online":
            total_uptime += current_phase
        else:
            total_downtime += current_phase

        return (total_uptime, total_downtime)
