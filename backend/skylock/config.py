import os
import secrets

import dotenv

dotenv.load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_bytes(30))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/db.sqlite")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB_RATELIMIT: int = int(os.getenv("REDIS_DB_RATELIMIT", "0"))
REDIS_URL_RATELIMIT: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB_RATELIMIT}"

ENV_TYPE = os.getenv("ENV", "dev")

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
