"""Comprehensive security, SSRF prevention, and authority scoring test matrix."""

import pytest

from app.modules.evidence.security import (
    compute_domain_authority,
    is_safe_url,
)

# 1. Blocked IPv4 and IPv6 addresses across all private, link-local, and reserved ranges
BLOCKED_URLS = [
    # IPv4 Loopback
    "http://127.0.0.1",
    "http://127.0.0.1:80",
    "http://127.0.0.1:8080/path",
    "https://127.0.0.2",
    "http://127.255.255.255",
    "http://127.1.2.3:3000",
    # IPv4 Private: 10.0.0.0/8
    "http://10.0.0.1",
    "http://10.0.0.254",
    "http://10.255.255.255:8000",
    "https://10.10.10.10/admin",
    # IPv4 Private: 172.16.0.0/12
    "http://172.16.0.1",
    "http://172.20.1.1",
    "http://172.31.255.255",
    "https://172.16.254.1:8443",
    # IPv4 Private: 192.168.0.0/16
    "http://192.168.0.1",
    "http://192.168.1.1",
    "http://192.168.1.254",
    "http://192.168.100.50:5000",
    "https://192.168.255.255",
    # Carrier-grade NAT: 100.64.0.0/10
    "http://100.64.0.1",
    "http://100.100.100.100",
    "http://100.127.255.255",
    # Cloud Metadata: 169.254.0.0/16 (AWS, GCP, Azure, DigitalOcean)
    "http://169.254.169.254",
    "http://169.254.169.254/latest/meta-data/",
    "http://169.254.169.254/computeMetadata/v1/",
    "http://169.254.0.1",
    "http://169.254.255.255",
    # Test networks: 192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24
    "http://192.0.2.1",
    "http://192.0.2.254",
    "http://198.51.100.1",
    "http://198.51.100.42",
    "http://203.0.113.1",
    "http://203.0.113.100",
    # Benchmark / Inter-network: 198.18.0.0/15
    "http://198.18.0.1",
    "http://198.19.255.255",
    # 0.0.0.0/8
    "http://0.0.0.0",
    "http://0.0.0.0:80",
    "http://0.1.2.3",
    # Multicast: 224.0.0.0/4
    "http://224.0.0.1",
    "http://239.255.255.250",
    # Reserved: 240.0.0.0/4
    "http://240.0.0.1",
    "http://255.255.255.255",
    # IPv6 Loopback, ULA, Link-Local
    "http://[::1]",
    "http://[::1]:8080",
    "http://[fc00::1]",
    "http://[fd12:3456:789a::1]",
    "http://[fe80::1]",
    "http://[fe80::a00:27ff:fe4e:66a1]",
    # Hostname bypass targets
    "http://localhost",
    "http://localhost:8080",
    "https://localhost/api",
    "http://metadata.google.internal",
    "http://metadata.google.internal/computeMetadata/v1/",
    "http://instance-data",
    "http://instance-data/latest/meta-data/",
    # Invalid schemes
    "ftp://example.com/file.txt",
    "file:///etc/passwd",
    "file://localhost/etc/shadow",
    "gopher://example.com:70/",
    "ldap://127.0.0.1:389/",
    "dict://example.com/d:test",
    "javascript:alert(1)",
    "data:text/html,<html>test</html>",
    "blob:https://example.com/12345",
    # Malformed / empty
    "",
    "   ",
    "not-a-url",
    "http://",
    "https://",
    "http:///path",
    "http://?query=1",
    "http://#fragment",
    "http://invalid_host_name_with_underscores_that_fail_regex",
]

# 2. Permitted external public domains
SAFE_URLS = [
    "https://en.wikipedia.org/wiki/France",
    "https://en.wikipedia.org/wiki/Albert_Einstein",
    "https://www.nature.com/articles/nature12345",
    "https://www.nasa.gov/mission_pages/station/main/index.html",
    "https://www.nih.gov/health-information",
    "https://www.cdc.gov/flu/about/index.html",
    "https://www.who.int/emergencies/diseases/novel-coronavirus-2019",
    "https://www.reuters.com/world/europe/france-election-2024",
    "https://apnews.com/article/science-space-exploration",
    "https://www.bbc.com/news/world-europe-12345678",
    "https://www.britannica.com/place/Paris",
    "https://harvard.edu/research/paper",
    "https://mit.edu/courses/physics",
    "https://stanford.edu/news",
    "https://example.org/about",
    "https://developer.mozilla.org/en-US/docs/Web",
    "http://public-data.org/index.html",
    "https://subdomain.example.gov/stats",
    "https://army.mil/news",
]

# Generate parametrized IP range test cases (50 additional granular IP tests)
PARAMETRIZED_PRIVATE_IPS = [f"http://10.0.{i}.1" for i in range(25)] + [
    f"http://192.168.{i}.1" for i in range(25)
]

PARAMETRIZED_PUBLIC_DOMAINS = (
    [f"https://domain{i}.org/article" for i in range(30)]
    + [f"https://research{i}.edu/publication" for i in range(30)]
    + [f"https://agency{i}.gov/report" for i in range(30)]
)


class TestSecurityAndSSRFMatrix:
    """Rigorous security test suite covering SSRF and authority scoring."""

    @pytest.mark.parametrize("blocked_url", BLOCKED_URLS)
    def test_blocked_urls_rejected(self, blocked_url: str) -> None:
        """Verify all internal, private, loopback, and metadata URLs are blocked."""
        assert is_safe_url(blocked_url) is False

    @pytest.mark.parametrize("private_ip_url", PARAMETRIZED_PRIVATE_IPS)
    def test_parametrized_private_ips_rejected(self, private_ip_url: str) -> None:
        """Verify entire private subnet spaces are rejected by SSRF filter."""
        assert is_safe_url(private_ip_url) is False

    @pytest.mark.parametrize("safe_url", SAFE_URLS)
    def test_safe_public_urls_permitted(self, safe_url: str) -> None:
        """Verify reputable public internet URLs are correctly accepted."""
        assert is_safe_url(safe_url) is True

    @pytest.mark.parametrize("public_domain_url", PARAMETRIZED_PUBLIC_DOMAINS)
    def test_parametrized_public_domains_permitted(
        self, public_domain_url: str
    ) -> None:
        """Verify diverse standard public educational, gov, and org domains are accepted."""
        assert is_safe_url(public_domain_url) is True

    @pytest.mark.parametrize(
        ("url", "expected_min_authority"),
        [
            ("https://nasa.gov/news", 0.85),
            ("https://nih.gov/health", 0.85),
            ("https://mit.edu/research", 0.85),
            ("https://navy.mil/info", 0.85),
            ("https://en.wikipedia.org/wiki/Physics", 0.85),
            ("https://nature.org/global", 0.85),
            ("https://reuters.com/world", 0.85),
            ("https://bbc.com/news", 0.85),
            ("https://science.org/journal", 0.85),
            ("https://who.org/reports", 0.85),
            ("https://cdc.org/data", 0.85),
            ("https://apnews.com/article", 0.85),
            ("https://britannica.org/topic", 0.85),
            ("https://generic-nonprofit.org/about", 0.70),
            ("https://standard-company.com/blog", 0.55),
            ("https://unknown-domain.io/page", 0.50),
            (None, 0.50),
            ("", 0.50),
        ],
    )
    def test_domain_authority_scoring(
        self, url: str | None, expected_min_authority: float
    ) -> None:
        """Verify domain authority heuristic assigns appropriate credibility weights."""
        score = compute_domain_authority(url)
        assert 0.0 <= score <= 1.0
        assert score >= expected_min_authority - 0.05
