from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from urllib.parse import urlsplit


METHOD_IP = "ip"
METHOD_HOSTNAME = "hostname"
METHOD_URL = "url"

_HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)"
    r"(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*\.?$"
)


@dataclass(frozen=True)
class NormalizedTarget:
    host: str
    port: int
    display_target: str
    full_target: str
    port_was_explicit: bool


def format_host_port(host: str, port: int) -> str:
    if ":" in host and not host.startswith("[") and host.count(":") >= 2:
        return f"[{host}]:{port}"
    return f"{host}:{port}"


def looks_like_url(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False

    # If text contains one of these symbols, it's in the form of a URL
    return (
        "://" in stripped
        or "/" in stripped
        or "?" in stripped
        or "#" in stripped
    )


def parse_host_optional_port(text: str, default_port: int = 443) -> tuple[str, int, bool]:
    raw_text = text.strip()

    if not raw_text:
        raise ValueError("Please enter a hostname.")

    explicit_port = False

    # Handle IPv6 ([::1]:443)
    if raw_text.startswith("["):
        closing_index = raw_text.find("]")
        if closing_index == -1:
            raise ValueError("Invalid bracketed host. Example: [::1]:443")

        host = raw_text[1:closing_index].strip()
        remainder = raw_text[closing_index + 1 :].strip()

        if remainder.startswith(":"):
            port_text = remainder[1:].strip()
            if not port_text.isdigit():
                raise ValueError("Port must be a number (1 - 65535).")
            port = int(port_text)
            explicit_port = True
        else:
            port = default_port

        if not (1 <= port <= 65535):
            raise ValueError("Port must be in the range 1 - 65535")

        return host, port, explicit_port

    # Normal hostname with optional port
    host = raw_text
    port = default_port

    if ":" in raw_text:
        possible_host, possible_port = raw_text.rsplit(":", 1)
        if possible_port.isdigit():
            host = possible_host.strip()
            port = int(possible_port)
            explicit_port = True

    if not host:
        raise ValueError("Hostname cannot be empty.")
    if not (1 <= port <= 65535):
        raise ValueError("Port must be in the range 1 - 65535")

    return host, port, explicit_port


def normalize_target(method: str, *, ip_address: str, ip_port: int, hostname: str, url: str) -> NormalizedTarget:
    # Target Method: IP Address
    if method == METHOD_IP:
        raw = ip_address.strip()
        if not raw:
            raise ValueError("Please enter an IP address.")
        clean = raw.strip("[]")
        try:
            ipaddress.ip_address(clean)
        except ValueError as exc:
            raise ValueError("Please enter a valid IPv4 or IPv6 address.") from exc

        port = int(ip_port)
        return NormalizedTarget(
            host=clean,
            port=port,
            display_target=format_host_port(clean, port),
            full_target=format_host_port(clean, port),
            port_was_explicit=True,
        )

    # Target Method: Hostname
    if method == METHOD_HOSTNAME:
        raw = hostname.strip()

        if looks_like_url(hostname):
            raise ValueError("Format is similar to URL. Switch Target Method to URL.")

        host, port, explicit = parse_host_optional_port(hostname, default_port=443)

        # Accept IP-as-hostname
        try:
            ipaddress.ip_address(host.strip("[]"))
            clean_ip = host.strip("[]")
            display = clean_ip if not explicit else format_host_port(clean_ip, port)
            return NormalizedTarget(
                host=clean_ip,
                port=port,
                display_target=display,
                full_target=display,
                port_was_explicit=explicit
            )
        except ValueError:
            pass

        try:
            ascii_host = host.encode("idna").decode("ascii").rstrip(".")
        except Exception as exc:
            raise ValueError("Invalid hostname.") from exc

        if not _HOSTNAME_RE.match(ascii_host):
            raise ValueError(
                'Enter a hostname (e.g., "romanjay-srv" or "google.com") or an IP address.\n'
                '"localhost" is permitted.'
            )

        display = host if not explicit else format_host_port(host, port)
        return NormalizedTarget(
            host=host,
            port=port,
            display_target=display,
            full_target=display,
            port_was_explicit=explicit
        )

    # Target Method: URL
    raw = url.strip()
    if not raw:
        raise ValueError("Please enter a URL.")

    # Allow scheme to be omitted (assume https)
    normalized_url = raw if "://" in raw else f"https://{raw}"
    parts = urlsplit(normalized_url)

    if parts.scheme not in ("http", "https"):
        raise ValueError('Only "http" and "https" URLs are supported.')
    if not parts.hostname:
        raise ValueError("Please enter a valid URL (must include a host).")

    try:
        port = parts.port
    except ValueError as exc:
        raise ValueError("Invalid port in URL.") from exc

    explicit = port is not None
    if port is None:
        port = 80 if parts.scheme == "http" else 443

    if not (1 <= port <= 65535):
        raise ValueError("Port out of range.")

    display = parts.hostname if not explicit else format_host_port(parts.hostname, port)
    return NormalizedTarget(
        host=parts.hostname,
        port=int(port),
        display_target=display,
        full_target=normalized_url,
        port_was_explicit=explicit
    )


