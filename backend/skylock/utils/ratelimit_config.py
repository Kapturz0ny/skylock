from slowapi import Limiter
from slowapi.util import get_remote_address

from skylock.config import REDIS_URL_RATELIMIT

RATE_LIMITING_ENABLED: bool = True

DEFAULT_RATE_LIMIT: str = "1/second"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[DEFAULT_RATE_LIMIT],
    strategy="fixed-window",
    storage_uri=REDIS_URL_RATELIMIT,
    enabled=RATE_LIMITING_ENABLED,
)
