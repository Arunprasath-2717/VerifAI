"""Security regression tests for trusted proxy policy, X-Forwarded-For handling, and rate limiting."""

from unittest.mock import MagicMock

from app.core.config import Settings
from app.core.rate_limit import (
    _GLOBAL_RATE_LIMITER,
    enforce_rate_limit,
    get_client_identifier,
)


def _build_request(
    client_ip: str | None = "127.0.0.1", forwarded_for: str | None = None
) -> MagicMock:
    """Helper to build mock FastAPI Request with custom socket peer and X-Forwarded-For header."""
    req = MagicMock()
    if client_ip is not None:
        req.client.host = client_ip
    else:
        req.client = None

    headers = {}
    if forwarded_for is not None:
        headers["X-Forwarded-For"] = forwarded_for
    req.headers = headers
    return req


class TestSecurityProxyRateLimit:
    """Regression suite for VERIFAI-FIND-002: Trusted proxy & X-Forwarded-For rate limiting."""

    def test_direct_client_forged_x_forwarded_for_ignored(self) -> None:
        """1. Direct client with forged X-Forwarded-For must use the actual socket address."""
        # Untrusted client 203.0.113.195 sends forged header claiming to be 198.51.100.1
        req = _build_request(client_ip="203.0.113.195", forwarded_for="198.51.100.1")
        settings = Settings(FORWARDED_ALLOW_IPS=[])

        identifier = get_client_identifier(req, settings=settings)
        assert identifier == "ip:203.0.113.195", (
            "Must ignore X-Forwarded-For when proxy is not trusted"
        )

    def test_trusted_proxy_valid_forwarded_address_extracted(self) -> None:
        """2. Trusted proxy with valid forwarded address must extract the client IP."""
        # Trusted reverse proxy at 10.0.0.1 forwards real client 198.51.100.25
        req = _build_request(client_ip="10.0.0.1", forwarded_for="198.51.100.25")
        settings = Settings(FORWARDED_ALLOW_IPS=["10.0.0.0/8"])

        identifier = get_client_identifier(req, settings=settings)
        assert identifier == "ip:198.51.100.25", (
            "Must extract client IP from trusted proxy"
        )

    def test_untrusted_proxy_forwarded_address_ignored(self) -> None:
        """3. Untrusted proxy socket IP is used directly; forwarded address is ignored."""
        # Intermediate host 172.16.5.10 is NOT in trusted CIDRs
        req = _build_request(client_ip="172.16.5.10", forwarded_for="198.51.100.25")
        settings = Settings(FORWARDED_ALLOW_IPS=["10.0.0.0/8"])

        identifier = get_client_identifier(req, settings=settings)
        assert identifier == "ip:172.16.5.10", (
            "Must use untrusted proxy socket IP directly"
        )

    def test_multiple_x_forwarded_for_values_walks_chain_to_first_untrusted(
        self,
    ) -> None:
        """4. Multiple X-Forwarded-For values walks right-to-left to determine the true client."""
        # Chain: Client 203.0.113.5 -> Internal Proxy 10.0.0.2 -> Ingress 10.0.0.1 -> App
        # Both 10.0.0.1 and 10.0.0.2 are trusted proxies in 10.0.0.0/8
        req = _build_request(
            client_ip="10.0.0.1", forwarded_for="203.0.113.5, 10.0.0.2"
        )
        settings = Settings(FORWARDED_ALLOW_IPS=["10.0.0.0/8"])

        identifier = get_client_identifier(req, settings=settings)
        assert identifier == "ip:203.0.113.5", (
            "Must find first untrusted IP walking backwards"
        )

    def test_ipv4_client_and_proxy(self) -> None:
        """5. IPv4 addresses are normalized and parsed cleanly."""
        req = _build_request(
            client_ip="192.168.1.1", forwarded_for="198.51.100.50:8080"
        )
        settings = Settings(FORWARDED_ALLOW_IPS=["192.168.1.1"])

        identifier = get_client_identifier(req, settings=settings)
        assert identifier == "ip:198.51.100.50", "Must handle IPv4 with port cleanly"

    def test_ipv6_client_and_proxy(self) -> None:
        """6. IPv6 addresses are supported for both client and trusted proxy."""
        # IPv6 loopback proxy ::1 forwards IPv6 client 2001:db8::cafe
        req = _build_request(client_ip="::1", forwarded_for="2001:db8::cafe")
        settings = Settings(FORWARDED_ALLOW_IPS=["::1/128"])

        identifier = get_client_identifier(req, settings=settings)
        assert identifier == "ip:2001:db8::cafe", "Must support IPv6 addresses"

    def test_missing_forwarded_header_falls_back_safely(self) -> None:
        """7. Missing X-Forwarded-For header safely falls back to socket peer IP."""
        req = _build_request(client_ip="10.0.0.1", forwarded_for=None)
        settings = Settings(FORWARDED_ALLOW_IPS=["10.0.0.0/8"])

        identifier = get_client_identifier(req, settings=settings)
        assert identifier == "ip:10.0.0.1", (
            "Must fall back to peer IP when header is absent"
        )

    def test_malformed_header_falls_back_safely(self) -> None:
        """8. Malformed or non-IP headers are ignored and fall back safely to socket peer IP."""
        req = _build_request(
            client_ip="10.0.0.1",
            forwarded_for="invalid_ip_string, <script>alert(1)</script>, ;;;",
        )
        settings = Settings(FORWARDED_ALLOW_IPS=["10.0.0.0/8"])

        identifier = get_client_identifier(req, settings=settings)
        assert identifier == "ip:10.0.0.1", (
            "Must fall back to peer IP on malformed header"
        )

    def test_authenticated_user_takes_precedence_over_ip(self) -> None:
        """Verify authenticated user ID strictly overrides IP identifier regardless of headers."""
        req = _build_request(client_ip="10.0.0.1", forwarded_for="198.51.100.1")
        settings = Settings(FORWARDED_ALLOW_IPS=["10.0.0.0/8"])

        identifier = get_client_identifier(
            req, user_id="user-uuid-9999", settings=settings
        )
        assert identifier == "usr:user-uuid-9999"

    def test_rate_limit_enforcement_under_trusted_vs_untrusted_ip(self) -> None:
        """Verify enforce_rate_limit correctly isolates sliding windows per resolved identifier."""
        settings = Settings(
            RATE_LIMIT_ENABLED=True,
            RATE_LIMIT_ENABLED_IN_TEST=True,
            FORWARDED_ALLOW_IPS=["10.0.0.1"],
        )
        _GLOBAL_RATE_LIMITER.clear()

        # Direct untrusted client cannot bypass limit by spoofing header
        untrusted_req = _build_request(client_ip="203.0.113.1", forwarded_for="1.1.1.1")
        enforce_rate_limit(untrusted_req, "login", limit=2, settings=settings)

        # Same client rotates header to 2.2.2.2 -> must still hit the SAME socket bucket (ip:203.0.113.1)
        untrusted_req.headers["X-Forwarded-For"] = "2.2.2.2"
        enforce_rate_limit(untrusted_req, "login", limit=2, settings=settings)

        # Third attempt from same client must raise RateLimitError
        untrusted_req.headers["X-Forwarded-For"] = "3.3.3.3"
        import pytest

        from app.core.errors import RateLimitError

        with pytest.raises(RateLimitError):
            enforce_rate_limit(untrusted_req, "login", limit=2, settings=settings)
