from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from skylock.pages.page_router import html_handler
from skylock.api.app import api
from skylock.utils.ratelimit_config import limiter

app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler) # type: ignore[arg-type]
app.mount("/api/v1", api)
app.mount("/", html_handler)
