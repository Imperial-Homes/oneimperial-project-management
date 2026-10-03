"""Revoked-session check.

Access tokens are valid for 8 hours. When user-management deactivates an
account it records the time under auth:revoked:<user_id> in a Redis database
every service reads (each service's own REDIS_URL points at a private DB
index); tokens issued (iat) before that time are refused here, so an exited
employee loses access immediately rather than when their token expires.
Keep in sync with user-management/app/core/revocation.py.
"""

import logging
from urllib.parse import urlsplit, urlunsplit

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

REVOCATION_DB = 15
_KEY = "auth:revoked:{}"
_client: aioredis.Redis | None = None


def _get_client() -> aioredis.Redis | None:
    global _client
    if _client is None and settings.REDIS_URL:
        url = urlunsplit(urlsplit(settings.REDIS_URL)._replace(path=f"/{REVOCATION_DB}"))
        _client = aioredis.from_url(url, socket_connect_timeout=1, socket_timeout=1, decode_responses=True)
    return _client


async def is_revoked(payload: dict) -> bool:
    """True if the token was issued before the user's sessions were revoked."""
    client = _get_client()
    if client is None:
        return False
    try:
        revoked_at = await client.get(_KEY.format(payload.get("sub")))
    # ponytail: fails open when Redis is down, so a Redis outage is not an API outage.
    # Deactivated users stay blocked from user-management (DB is_active check) and refresh.
    except Exception as exc:
        logger.warning("Session revocation check unavailable: %s", exc)
        return False
    return revoked_at is not None and float(payload.get("iat", 0)) < float(revoked_at)
