import redis
from skylock.config import REDIS_HOST, REDIS_PORT

redis_mem = redis.Redis(
    host=REDIS_HOST,
    port=int(REDIS_PORT),
    decode_responses=True
)