# security/rate_limiter.py

import time
from threading import Lock

class RateLimiter:
    """
    Tracks requests per key (e.g. IP) and enforces a maximum number
    of requests within a sliding time window.
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window       = window_seconds
        self.requests     = {}  # key -> list of request timestamps
        self._lock        = Lock()

    def allow(self, key: str) -> bool:
        """
        Returns True if `key` has made fewer than max_requests
        in the past window_seconds; records the new request.
        """
        now = time.time()
        with self._lock:
            timestamps = self.requests.setdefault(key, [])
            # drop timestamps older than window
            cutoff = now - self.window
            while timestamps and timestamps[0] < cutoff:
                timestamps.pop(0)
            if len(timestamps) < self.max_requests:
                timestamps.append(now)
                return True
            return False
