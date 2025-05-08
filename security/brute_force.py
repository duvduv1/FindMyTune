import time
from threading import Lock

class BruteForceProtector:
    """
    Tracks failed login attempts by IP address and blocks
    any IP that exceeds a configured number of failures
    within a time window.
    """

    def __init__(self, max_attempts: int = 5, window_seconds: int = 300):
        """
        Args:
          max_attempts: Maximum allowed failures within the time window.
          window_seconds: The sliding time window size, in seconds.
        """
        self.max_attempts = max_attempts
        self.window       = window_seconds
        self.failures     = {}  # ip -> list of failure timestamps
        self._lock        = Lock()

    def register_failure(self, ip: str) -> None:
        """
        Record a failed login attempt for `ip`, and purge old entries.
        """
        now = time.time()
        with self._lock:
            timestamps = self.failures.setdefault(ip, [])
            timestamps.append(now)
            # Remove any older than window_seconds ago
            cutoff = now - self.window
            self.failures[ip] = [ts for ts in timestamps if ts >= cutoff]

    def is_blocked(self, ip: str) -> bool:
        """
        Returns True if this IP has exceeded max_attempts within the window.
        """
        with self._lock:
            timestamps = self.failures.get(ip, [])
            return len(timestamps) >= self.max_attempts