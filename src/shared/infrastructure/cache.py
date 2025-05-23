# shared/infrastructure/cache.py
import redis


class CacheManager:
    def __init__(self):
        self.client = redis.Redis(host="redis", port=6379, db=0)

    def get(self, key: str) -> Optional[str]:
        return self.client.get(key)

    def set(self, key: str, value: str, ttl: int = 3600):
        self.client.set(key, value, ex=ttl)
