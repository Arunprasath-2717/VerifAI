"""Security validations and source authority heuristics for evidence retrieval."""

import ipaddress
import re
from urllib.parse import urlparse

# Private, link-local, loopback, and metadata network ranges for SSRF prevention
BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # Cloud metadata service (AWS/GCP/Azure)
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.88.99.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),  # Multicast
    ipaddress.ip_network("240.0.0.0/4"),  # Reserved
    ipaddress.ip_network("::1/128"),  # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),  # IPv6 ULA
    ipaddress.ip_network("fe80::/10"),  # IPv6 link-local
]

# Reputable academic, institutional, and reference domains
HIGH_AUTHORITY_PATTERNS = [
    r"\.gov(?:\.[a-z]{2})?$",
    r"\.edu(?:\.[a-z]{2})?$",
    r"\.mil$",
    r"(?:wikipedia|nature|science|reuters|apnews|nih|who|nasa|cdc|britannica)\.org$",
    r"(?:nature|sciencemag|reuters|apnews|bloomberg|bbc)\.com$",
]


def is_safe_url(url: str) -> bool:
    """Validate that a URL uses http/https and does not target internal addresses."""
    if not url or not isinstance(url, str):
        return False

    try:
        parsed = urlparse(url.strip())
    except Exception:
        return False

    # 1. Scheme check: only http and https allowed
    if parsed.scheme.lower() not in {"http", "https"}:
        return False

    hostname = parsed.hostname
    if not hostname:
        return False

    hostname = hostname.lower().strip("[]")

    # 2. Rejection of localhost and metadata service names
    if hostname in {"localhost", "metadata.google.internal", "instance-data"}:
        return False

    # 3. Check for literal IP addresses in hostname
    try:
        ip = ipaddress.ip_address(hostname)
        for net in BLOCKED_IP_NETWORKS:
            if ip in net:
                return False
    except ValueError:
        # Not a literal IP address; domain name syntax check
        pass

    # 4. Valid domain syntax
    domain_pattern = re.compile(
        r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
    )
    if not domain_pattern.match(hostname):
        try:
            ipaddress.ip_address(hostname)
        except ValueError:
            return False

    return True


def compute_domain_authority(url: str | None) -> float:
    """Compute a baseline source authority weight in [0.0, 1.0]."""
    if not url:
        return 0.50

    try:
        hostname = urlparse(url).hostname
        if not hostname:
            return 0.50
        hostname = hostname.lower()

        for pat in HIGH_AUTHORITY_PATTERNS:
            if re.search(pat, hostname):
                return 0.90

        if hostname.endswith(".org"):
            return 0.75

        return 0.60
    except Exception:
        return 0.50
