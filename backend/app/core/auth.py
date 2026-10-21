"""API-key authentication, owner scoping, and per-principal rate limiting."""

import hmac
import logging
import time
from dataclasses import dataclass

from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.core.errors import ForbiddenError, TooManyRequestsError, UnauthorizedError

logger = logging.getLogger("verifai.auth")

_RATE_WINDOW_SECONDS = 60


@dataclass(frozen=True)
class Principal:
    """The caller on whose behalf a request executes.

    ``owner_id`` is None only for anonymous development callers, who may then
    choose a namespace explicitly (falling back to DEFAULT_OWNER_ID).
    """

    owner_id: str | None
    authenticated: bool

    @property
    def rate_limit_key(self) -> str:
        return self.owner_id or "anonymous"


def _match_api_key(presented: str, settings: Settings) -> str | None:
    """Return the owner for ``presented``, comparing every key in constant time."""
    matched: str | None = None
    presented_bytes = presented.encode("utf-8")
    for owner, key in settings.API_KEYS.items():
        if hmac.compare_digest(presented_bytes, key.get_secret_value().encode()):
            matched = owner
    return matched


def get_principal(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> Principal:
    """Authenticate the request from its API key header."""
    presented = request.headers.get(settings.API_KEY_HEADER, "").strip()

    if not settings.API_KEYS:
        if settings.is_development:
            return Principal(owner_id=None, authenticated=False)
        logger.error(
            "Rejecting request: API_KEYS is not configured in '%s' environment.",
            settings.ENVIRONMENT,
        )
        raise UnauthorizedError("API authentication is not configured on server.")

    if not presented:
        raise UnauthorizedError(f"Missing {settings.API_KEY_HEADER} header.")

    owner = _match_api_key(presented, settings)
    if owner is None:
        raise UnauthorizedError("Invalid API key.")
    return Principal(owner_id=owner, authenticated=True)


def resolve_owner(
    principal: Principal,
    requested_owner_id: str | None,
    settings: Settings,
) -> str:
    """Return the namespace a request may act on.

    Authenticated callers are pinned to their own namespace; naming a different
    one is rejected rather than silently rewritten. Anonymous development
    callers may pick any namespace, defaulting to DEFAULT_OWNER_ID.
    """
    requested = requested_owner_id.strip() if requested_owner_id else None
    if principal.authenticated:
        if requested and requested != principal.owner_id:
            raise ForbiddenError("Access to the requested namespace is forbidden.")
        assert principal.owner_id is not None
        return principal.owner_id
    return requested or settings.DEFAULT_OWNER_ID


def enforce_rate_limit(
    request: Request,
    principal: Principal = Depends(get_principal),
    settings: Settings = Depends(get_settings),
) -> Principal:
    """Fixed-window per-principal budget for expensive or state-changing calls.

    State lives on ``app.state`` and is therefore per-process; deployments with
    several workers need a shared store (e.g. Redis) for a global limit.
    """
    limit = settings.RATE_LIMIT_PER_MINUTE
    if limit <= 0:
        return principal

    windows: dict[str, tuple[int, int]] = (
        getattr(request.app.state, "rate_limit_windows", None) or {}
    )
    request.app.state.rate_limit_windows = windows

    now_window = int(time.monotonic() // _RATE_WINDOW_SECONDS)
    key = principal.rate_limit_key
    window, count = windows.get(key, (now_window, 0))
    if window != now_window:
        window, count = now_window, 0
    if count >= limit:
        raise TooManyRequestsError(
            f"Rate limit of {limit} requests per minute exceeded.",
            retry_after_seconds=_RATE_WINDOW_SECONDS,
        )
    windows[key] = (window, count + 1)
    return principal
