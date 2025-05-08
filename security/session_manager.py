# security/session_manager.py

import uuid
import time
import threading
from threading import Lock

from settings import SESSION_TIMEOUT  # in seconds

class SessionManager:
    """
    In‑memory session token manager with expiration.
    """

    def __init__(self):
        # token -> (user_id, last_access_time)
        self.sessions = {}
        self.session_timeout = SESSION_TIMEOUT
        self._lock = Lock()

        # start background cleanup
        thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        thread.start()

    def create_session(self, user_id: int) -> str:
        """
        Generates a new session token for `user_id`.
        """
        token = uuid.uuid4().hex
        now = time.time()
        with self._lock:
            self.sessions[token] = (user_id, now)
        return token

    def validate_session(self, token: str) -> int | None:
        """
        Returns the user_id if token exists and is not expired.
        Otherwise deletes it and returns None.
        """
        now = time.time()
        with self._lock:
            data = self.sessions.get(token)
            if not data:
                return None
            user_id, ts = data
            if now - ts > self.session_timeout:
                # expired
                del self.sessions[token]
                return None
            # update last access time (sliding timeout)
            self.sessions[token] = (user_id, now)
            return user_id

    def delete_session(self, token: str) -> None:
        """
        Explicitly invalidate a session token.
        """
        with self._lock:
            self.sessions.pop(token, None)

    def _cleanup_loop(self):
        """
        Periodically remove expired sessions.
        """
        while True:
            time.sleep(self.session_timeout)
            now = time.time()
            with self._lock:
                expired = [t for t, (_, ts) in self.sessions.items()
                           if now - ts > self.session_timeout]
                for t in expired:
                    del self.sessions[t]
