"""Security validations and source authority heuristics for evidence retrieval."""

import asyncio
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


# Hostnames and suffixes that only ever resolve to internal infrastructure.
_BLOCKED_HOSTNAMES = {"localhost", "metadata.google.internal", "instance-data"}
_BLOCKED_HOST_SUFFIXES = (
    ".localhost",
    ".local",
    ".localdomain",
    ".internal",
    ".intranet",
    ".lan",
    ".home.arpa",
)
_NAT64_PREFIX = ipaddress.ip_network("64:ff9b::/96")
_DOMAIN_PATTERN = re.compile(
    r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)


def _embedded_ipv4(ip: ipaddress.IPv6Address) -> ipaddress.IPv4Address | None:
    """Return an IPv4 address tunnelled inside an IPv6 one, if any."""
    if ip.ipv4_mapped is not None:
        return ip.ipv4_mapped
    if ip.sixtofour is not None:
        return ip.sixtofour
    if ip.teredo is not None:
        return ip.teredo[1]
    if ip in _NAT64_PREFIX:
        return ipaddress.IPv4Address(int(ip) & 0xFFFFFFFF)
    return None


def is_public_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """True only for globally routable unicast addresses.

    IPv4 addresses embedded in IPv6 (mapped, 6to4, Teredo, NAT64) are unwrapped
    and checked too, so "::ffff:127.0.0.1" cannot smuggle a loopback target.
    """
    if isinstance(ip, ipaddress.IPv6Address):
        embedded = _embedded_ipv4(ip)
        if embedded is not None:
            return is_public_ip(embedded)
    if ip.is_multicast or ip.is_unspecified or ip.is_reserved:
        return False
    # Explicit blocklist kept as defense in depth alongside is_global.
    if any(ip.version == net.version and ip in net for net in BLOCKED_IP_NETWORKS):
        return False
    return ip.is_global


def is_safe_url(url: str) -> bool:
    """Statically validate that a URL is http(s) and not an internal target.

    This check does not resolve DNS, so a public-looking name may still point at
    an internal address (e.g. wildcard-DNS services such as ``*.nip.io``).
    Anything that makes a server-side request to the URL must call
    :func:`is_safe_url_resolved` first.
    """
    if not url or not isinstance(url, str):
        return False

    try:
        parsed = urlparse(url.strip())
        hostname = parsed.hostname
    except ValueError:
        return False

    if parsed.scheme.lower() not in {"http", "https"} or not hostname:
        return False
    if parsed.username or parsed.password:
        return False  # credentials in URLs enable host-confusion tricks

    hostname = hostname.lower().strip("[]").rstrip(".")
    if hostname in _BLOCKED_HOSTNAMES or hostname.endswith(_BLOCKED_HOST_SUFFIXES):
        return False

    try:
        return is_public_ip(ipaddress.ip_address(hostname))
    except ValueError:
        pass  # not an IP literal

    return bool(_DOMAIN_PATTERN.match(hostname))


async def is_safe_url_resolved(url: str) -> bool:
    """Validate a URL and every address its hostname currently resolves to.

    Required before any server-side fetch. Resolution failures are unsafe.
    Callers should connect to the validated address (or re-check at connect
    time) to avoid DNS-rebinding between this check and the request.
    """
    if not is_safe_url(url):
        return False
    hostname = (urlparse(url.strip()).hostname or "").strip("[]")
    try:
        ipaddress.ip_address(hostname)
        return True  # literal already validated
    except ValueError:
        pass
    try:
        infos = await asyncio.get_running_loop().getaddrinfo(hostname, None)
    except OSError:
        return False
    addresses = {str(info[4][0]) for info in infos}
    if not addresses:
        return False
    for address in addresses:
        try:
            ip = ipaddress.ip_address(address.split("%", 1)[0])
        except ValueError:
            return False
        if not is_public_ip(ip):
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
