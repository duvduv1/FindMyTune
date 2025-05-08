# game/player.py

import uuid
import asyncio
import json
from typing import Any, Dict

class Player:
    """
    Represents a connected game participant.
    Tracks identity, connection, and per-round state.
    """

    def __init__(self, username: str, websocket: Any):
        # Unique per‐connection player ID
        self.id: str = str(uuid.uuid4())
        self.username: str = username
        self.websocket = websocket

        # Cumulative score across all rounds
        self.score: int = 0

        # For heartbeat / connection liveness
        self.last_heartbeat: float = asyncio.get_event_loop().time()

        # Per‐round state (will be reset each round)
        self.has_guessed: bool = False
        self.guess_time: float = 0.0
        self.guessed_correctly: bool = False
        self.current_round_points: int = 0

    async def send_message(self, message_type: str, data: Dict[str, Any] = {}) -> bool:
        """
        Send a typed JSON message to this player over their websocket.
        Returns True on success, False if the connection is closed.
        """
        packet = {"type": message_type, "data": data}
        try:
            await self.websocket.send(json.dumps(packet))
            return True
        except Exception:
            return False

    def reset_round(self) -> None:
        """
        Clears all per‐round state in preparation for the next round.
        """
        self.has_guessed = False
        self.guess_time = None
        self.guessed_correctly = False
        self.current_round_points = 0

    def update_heartbeat(self) -> None:
        """
        Call whenever a ping/pong is received to mark the connection as alive.
        """
        self.last_heartbeat = asyncio.get_event_loop().time()