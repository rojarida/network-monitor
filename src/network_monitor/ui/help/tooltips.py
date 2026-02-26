from __future__ import annotations

from typing import Iterable
from PySide6 import QtWidgets


METRIC_TOOLTIPS: dict[str, str] = {
    "status": (
        "The result of the most recent check. \n\n"
        "- Online: The target host:port accepted a TCP connection.\n"
        "- Unreachable: Internet appears stable, but the target is not reachable.\n"
        "- Offline: Internet appears down.\n\n"
        "Tip: If unreachable, the port could potentially be blocked."
    ),
    "server": (
        "The target being checked.\n\n"
        "Ports can be explicited stated.\n"
        "- Hostname / IP: You can optionally include a port (e.g., google.com or 1.1.1.1:443).\n"
        "- URL: Scheme and subdomain may be omitted.\n- Default ports: http:80, https:443.\n\n"
        "Tip: If the port isn't shown, it may be using a default port; the check still uses it."
    ),
    "current_phase": (
        "How long the current status has been active.\n\n"
        "This timer changes when the status changes (Online -> Unreachable -> Offline)."
    ),
    "latency": (
        "Approximate time to establish a TCP connection to the target in milliseconds.\n\n"
        "Shown only when the target is reachable.\n\n"
        "Pill color:\n"
        "Green = <100ms\n"
        "Yellow = 100 - 199ms\n"
        "Red = >200ms"
    ),
    "disconnects": (
        "How many times the connection has dropped since the application started.\n\n"
        "A disconnect is counted when the status transitions from Online -> Unreachable/Offline."
    ),
    "total_uptime": (
        "The total time the application has reported the target as Online since the application started.\n\n"
        "As of v0.6.0, this timer resets when the application restarts."
    ),
    "total_downtime": (
        "The total time the application has reported the target NOT Online since the application started.\n\n"
        "This includes both Unreachable and Offline.\n"
        "As of v0.6.0, this timer resets when the application restarts."
    ),
}

STATUS_VALUE_TOOLTIPS: dict[str, str] = {
    "unknown": (
        "Checking...\n"
        "No result yet. The first check may still be running."
    ),
    "online": (
        "Internet connectivity appears stable."
    ),
    "offline": (
        "Internet connectivity appears down (or blocked). The well-known fallback endpoints were also unreachable.\n\n"
        "Common causes: ISP outage, router/modem down, Wi-Fi disconnected, misconfigured IP/DNS..."
    ),
    "unreachable": (
        "Internet connectivity appears stable, but the target is unreachable.\n\n"
        "Common causes: Incorrect URL/IP, blocked port, service down, firewall blocked..."
    ),
}

SETTINGS_TOOLTIPS: dict[str, str] = {

    "target_method": (
        "Choose how you want to enter the target.\n\n"
        "- IP Address: Direct IP (IPv4/IPv6)\n"
        "- Hostname: Device name or domain (optionally :port)\n"
        "- URL: Web address (scheme optional)\n\n"
        "Note: The monitor checks reachability by opening a TCP connection to host:port."
    ),

    "ip_input": (
        "The IP address to check.\n\n"
        "Examples:\n"
        "- 192.168.1.10\n"
        "- 192.168.1.10:445\n"
        "- [::1]:443\n\n"
        "Tip: IPv6 with a port should use brackets like [::1]:443.\n"
        "If no port is provided, the application uses the default port for the chosen method."
    ),

    "ip_port": (
        "Port number to connect to on the IP address.\n\n"
        "Common ports:\n"
        "- 443 (HTTPS)\n"
        "- 80 (HTTP)\n"
        "- 22 (SSH)\n"
        "- 445 (SMB)\n"
        "- 3389 (RDP)\n\n"
        "Choose the port for the specific service you want to monitor."
    ),

    "hostname_input": (
        "The hostname to check (device name or domain).\n\n"
        "Valid examples:\n"
        "- google.com\n"
        "- romanjay-srv\n"
        "- localhost:8080\n\n"
        "Hostnames do not need to contain a dot.\n"
        "If no port is provided, the application uses the default port for the chosen method."
    ),

    "url_input": (
        "A URL to check.\n\n"
        "Examples:\n"
        "- google.com\n"
        "- https://google.com\n"
        "- http://router.local\n"
        "- https://www.reddit.com/r/leagueoflegends/\n\n"
        "Scheme is optional.\n"
        "The application uses only the URL’s host and port for the connection check.\n"
        "Path/query fragments are ignored."
    ),

    "check_interval": (
        "How often the application checks the target.\n\n"
        "Shorter intervals update faster, but may increase CPU/network usage.\n"
        "If the interval is shorter than the timeout, checks can overlap."
    ),

    "timeout": (
        "How long to wait for a connection attempt before marking it as failed.\n\n"
        "If the timeout is reached, the check is treated as failed.\n"
        "A longer timeout is more tolerant of slow networks, but slows detection.\n\n"
        "Tip: Keep timeout less than or equal interval to help keep checks predictable."
    ),

    "custom_interval": (
        "Use a custom check interval (in seconds).\n\n"
        "Tip: Keep this at or above 0.5s.\n"
        "If you want smoother status updates, use 1–2 seconds."
    ),

    "custom_timeout": (
        "Use a custom timeout (in seconds).\n\n"
        "Tip: 1–2 seconds is a good default for LAN targets.\n"
        "For remote targets on slower networks, 3–5 seconds can be more stable."
    ),
}

THEME_TOOLTIPS: dict[str, str] = {
    "light": "Switch to Light mode",
    "dark": "Switch to Dark mode",
}


def apply_tooltip(widgets: Iterable[QtWidgets.QWidget], tooltip_text: str) -> None:
    if not tooltip_text:
        return
    
    for widget in widgets:
        if widget is not None:
            widget.setToolTip(tooltip_text)


def status_value_tooltip(last_status: str | None) -> str:
    if last_status is None:
        return STATUS_VALUE_TOOLTIPS["unknown"]
    
    return STATUS_VALUE_TOOLTIPS.get(last_status, STATUS_VALUE_TOOLTIPS["unknown"]) 
