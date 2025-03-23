import os
import secrets

import dotenv

dotenv.load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_bytes(30))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/db.sqlite")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)

ENV_TYPE = os.getenv("ENV", "dev")