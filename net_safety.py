"""Outbound fetch guard for URLs that come from users or scraped third-party data.

Blocks requests to loopback, private, link-local (including cloud metadata at
169.254.169.254), multicast and other non-public addresses, and re-checks every
redirect hop so a public URL cannot bounce the server into its own network.
"""
import ipaddress
import socket
from typing import Optional
from urllib.parse import urljoin, urlsplit

import requests

ALLOWED_SCHEMES = {"http", "https"}
ALLOWED_PORTS = {None, 80, 443}
MAX_REDIRECTS = 5
MAX_BYTES = 3 * 1024 * 1024


class UnsafeURLError(ValueError):
    """Raised when a URL points somewhere the server must not fetch."""


def _is_public_ip(ip: ipaddress._BaseAddress) -> bool:
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip.is_global and not ip.is_multicast


def assert_public_url(url: str) -> str:
    """Validates scheme, port and that every address the host resolves to is public.
    Returns the URL unchanged, or raises UnsafeURLError."""
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError as e:
        raise UnsafeURLError(f"Malformed URL: {e}")
    if parts.scheme.lower() not in ALLOWED_SCHEMES:
        raise UnsafeURLError("Only http and https URLs can be fetched.")
    if parts.username or parts.password:
        raise UnsafeURLError("URLs with embedded credentials are not allowed.")
    if port not in ALLOWED_PORTS:
        raise UnsafeURLError("Only standard web ports (80, 443) are allowed.")
    host = (parts.hostname or "").strip().rstrip(".")
    if not host:
        raise UnsafeURLError("URL has no host.")

    try:
        infos = socket.getaddrinfo(host, port or (443 if parts.scheme == "https" else 80), proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise UnsafeURLError(f"Could not resolve host '{host}'.")
    addresses = {info[4][0].split("%")[0] for info in infos}
    if not addresses:
        raise UnsafeURLError(f"Could not resolve host '{host}'.")
    for addr in addresses:
        if not _is_public_ip(ipaddress.ip_address(addr)):
            raise UnsafeURLError("URL points to a private or internal network address.")
    return url


def safe_get(url: str, timeout: float = 10, headers: Optional[dict] = None, max_bytes: int = MAX_BYTES) -> requests.Response:
    """requests.get replacement for untrusted URLs: validates each redirect hop and caps body size.

    A DNS answer can still change between the check and the connection (DNS rebinding);
    deploy behind an egress firewall if that matters for your threat model.
    """
    current = url
    for _ in range(MAX_REDIRECTS + 1):
        assert_public_url(current)
        resp = requests.get(current, headers=headers, timeout=timeout, allow_redirects=False, stream=True)
        if resp.is_redirect or resp.is_permanent_redirect:
            location = resp.headers.get("Location", "")
            resp.close()
            if not location:
                raise UnsafeURLError("Redirect without a Location header.")
            current = urljoin(current, location)
            continue

        body = b""
        for chunk in resp.iter_content(chunk_size=65536):
            body += chunk
            if len(body) > max_bytes:
                resp.close()
                raise UnsafeURLError("Response is too large.")
        resp._content = body
        resp._content_consumed = True
        return resp
    raise UnsafeURLError("Too many redirects.")
