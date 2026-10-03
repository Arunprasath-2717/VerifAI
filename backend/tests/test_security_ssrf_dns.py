"""Security regression tests for DNS-resolution SSRF protection and address validation."""

import socket
from unittest.mock import patch

from app.modules.evidence.security import is_safe_url


class TestSecuritySSRFDNSResolution:
    """Regression suite covering DNS resolution SSRF defense and IPv4/IPv6 address validation."""

    def test_dns_nip_io_loopback_resolved_and_rejected(self) -> None:
        """Verify domains that resolve via DNS to loopback (e.g. 127.0.0.1.nip.io) are rejected."""
        assert is_safe_url("http://127.0.0.1.nip.io/api") is False

    def test_cloud_metadata_ips_and_names_rejected(self) -> None:
        """Verify cloud metadata endpoints (AWS/GCP/Azure) are strictly rejected."""
        assert is_safe_url("http://169.254.169.254/latest/meta-data/") is False
        assert (
            is_safe_url("http://metadata.google.internal/computeMetadata/v1/") is False
        )
        assert is_safe_url("http://instance-data/") is False

    def test_internal_domain_suffixes_rejected(self) -> None:
        """Verify internal network suffixes (.internal, .local, .localhost) are rejected."""
        assert is_safe_url("http://database.internal/query") is False
        assert is_safe_url("http://service.local/status") is False
        assert is_safe_url("http://app.localhost/metrics") is False

    def test_ipv6_loopback_and_link_local_rejected(self) -> None:
        """Verify IPv6 loopback, link-local, and ULA addresses are rejected."""
        assert is_safe_url("http://[::1]/status") is False
        assert is_safe_url("http://[fe80::1]/info") is False
        assert is_safe_url("http://[fc00::1]/admin") is False

    def test_ipv4_mapped_ipv6_loopback_rejected(self) -> None:
        """Verify IPv4-mapped IPv6 addresses targeting loopback or private ranges are rejected."""
        assert is_safe_url("http://[::ffff:127.0.0.1]/") is False
        assert is_safe_url("http://[::ffff:169.254.169.254]/meta-data") is False
        assert is_safe_url("http://[::ffff:10.0.0.1]/") is False

    def test_dns_multi_address_with_one_private_ip_rejected(self) -> None:
        """Verify a domain resolving to multiple IPs where one is private/internal is rejected."""
        # Simulate dual-homed DNS response: public IP 93.184.216.34 AND internal IP 10.0.0.1
        dual_homed_addrinfo = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 80)),
        ]

        with patch("socket.getaddrinfo", return_value=dual_homed_addrinfo):
            assert is_safe_url("https://dualhomed-target.com/data") is False

    def test_dns_metadata_resolved_ip_rejected(self) -> None:
        """Verify a domain resolving to 169.254.169.254 via DNS is rejected."""
        metadata_addrinfo = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", 80))
        ]

        with patch("socket.getaddrinfo", return_value=metadata_addrinfo):
            assert is_safe_url("https://attacker-cloud-metadata.com/secret") is False

    def test_reputable_public_domain_permitted(self) -> None:
        """Verify reputable public internet URLs with valid public IPs are permitted."""
        assert is_safe_url("https://en.wikipedia.org/wiki/Computer_science") is True
        assert is_safe_url("https://www.nature.com/articles/d41586-024-00000-0") is True
