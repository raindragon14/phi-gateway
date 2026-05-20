"""URL validation and SSRF prevention for tool endpoint proxying.

Blocks requests to private, link-local, and cloud metadata IP ranges
to prevent Server-Side Request Forgery (SSRF) attacks.
"""

import ipaddress
import socket
from urllib.parse import urlparse


# IPv4 private/reserved ranges that should not be reachable from a proxy.
_BLOCKED_NETWORKS: list = [
    ipaddress.ip_network("127.0.0.0/8"),       # Loopback
    ipaddress.ip_network("10.0.0.0/8"),         # RFC 1918 private
    ipaddress.ip_network("172.16.0.0/12"),      # RFC 1918 private
    ipaddress.ip_network("192.168.0.0/16"),     # RFC 1918 private
    ipaddress.ip_network("169.254.0.0/16"),     # Link-local (AWS metadata)
    ipaddress.ip_network("0.0.0.0/8"),          # Current network
    ipaddress.ip_network("100.64.0.0/10"),      # Carrier-grade NAT
    ipaddress.ip_network("198.18.0.0/15"),      # Benchmarking
]

# IPv6 blocked ranges
_BLOCKED_NETWORKS_V6: list = [
    ipaddress.ip_network("::1/128"),             # Loopback
    ipaddress.ip_network("fe80::/10"),           # Link-local
    ipaddress.ip_network("fc00::/7"),            # Unique local
    ipaddress.ip_network("::ffff:0:0/96"),       # IPv4-mapped IPv6
]


def validate_endpoint_url(url: str) -> None:
    """Validate a tool endpoint URL and reject SSRF-vulnerable targets.

    Checks that the URL uses HTTP(S), resolves to a public IP address,
    and is not in a private/reserved range.

    Args:
        url: The tool endpoint URL to validate.

    Raises:
        ValueError: If the URL is invalid, uses a forbidden scheme,
            or resolves to a blocked IP range.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(
            f"Invalid URL scheme '{parsed.scheme}'. Only http and https are allowed."
        )
    if not parsed.hostname:
        raise ValueError("URL missing hostname")

    try:
        addr = socket.getaddrinfo(parsed.hostname, None)
        ip_str = addr[0][4][0]
        ip = ipaddress.ip_address(ip_str)
    except socket.gaierror as e:
        raise ValueError(f"Cannot resolve hostname '{parsed.hostname}': {e}")
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid address for '{parsed.hostname}': {e}")

    blocked = _BLOCKED_NETWORKS if isinstance(ip, ipaddress.IPv4Address) else _BLOCKED_NETWORKS_V6
    for network in blocked:
        if ip in network:
            raise ValueError(
                f"Blocked private/reserved IP range {network}. "
                f"Tool endpoints must be publicly routable."
            )
