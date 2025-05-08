# game/game_server.py

import asyncio
import random
from typing import List, Dict, Optional

from game.player     import Player
from game.game_round import GameRound
from settings        import GAME_SONGS_DIR

class GameServer:
    def __init__(self, game_id, host_player, songs_db):
        self.game_id     = game_id
        self.host        = host_player
        self.players     = []
        self.songs_db    = songs_db
        self.state       = "lobby"   # lobby | playing | ended
        self.settings    = {"num_rounds": 10, "round_time": 30}
        self.current_round: Optional[GameRound] = None
        self.round_number = 0
        self.used_songs   = set()

    # ---------------- Lobby Methods ----------------

    async def add_player(self, player: Player) -> bool:
        if self.state != "lobby" or len(self.players) >= 8:
            return False
        self.players.append(player)
        await self.broadcast({
            "type": "player_joined",
            "data": {
                "player_id": player.id,
                "username": player.username,
                "player_count": len(self.players)
            }
        })
        # Send the new player the lobby state
        await player.send_message("game_state", {
            "game_id": self.game_id,
            "host": self.host.username,
            "state": self.state,
            "settings": self.settings,
            "players": [{"id": p.id, "username": p.username} for p in self.players]
        })
        return True

    async def get_players(self, player: Player):
        await player.send_message("players",{
            "players": [
                {"id": p.id, "username": p.username}
                for p in self.players
            ]
        })

    async def remove_player(self, player: Player):
        if player in self.players:
            self.players.remove(player)
            await self.broadcast({
                "type": "player_left",
                "data": {
                    "player_id": player.id,
                    "username": player.username,
                    "player_count": len(self.players)
                }
            })
            if player == self.host and self.players:
                self.host = random.choice(self.players)
                await self.broadcast({
                    "type": "new_host",
                    "data": {
                        "host_id": self.host.id,
                        "host_username": self.host.username
                    }
                })

    async def update_settings(self, new_settings: Dict[str, int]) -> bool:
        if self.state != "lobby":
            return False
        valid = {}
        if "num_rounds" in new_settings:
            nr = new_settings["num_rounds"]
            if 7 <= nr <= 15:
                valid["num_rounds"] = nr
        if "round_time" in new_settings:
            rt = new_settings["round_time"]
            if 15 <= rt <= 40:
                valid["round_time"] = rt
        if not valid:
            return False
        self.settings.update(valid)
        await self.broadcast({
            "type": "settings_updated",
            "data": {"settings": self.settings}
        })
        return True

    # ---------------- Game Lifecycle ----------------

    async def start_game(self) -> bool:
        if self.state != "lobby" or not self.players:
            return False
        self.state = "playing"
        self.round_number = 0
        self.used_songs.clear()
        for p in self.players:
            p.score = 0

        await self.broadcast({
            "type": "game_started",
            "data": {
                "num_rounds":  self.settings["num_rounds"],
                "round_time":  self.settings["round_time"],
                "players":     [{"id": p.id, "username": p.username} for p in self.players]
            }
        })
        # kickoff first round
        asyncio.create_task(self._next_round())
        return True

    async def _next_round(self):
        self.round_number += 1
        if self.round_number > self.settings["num_rounds"]:
            await self.end_game()
            return

        # instantiate and setup
        self.current_round = GameRound(
            round_number=self.round_number,
            players=self.players,
            songs_db=self.songs_db,
            round_time=self.settings["round_time"]
        )
        # make sure GameRound can reference back to us
        self.current_round.game_server = self

        await self.current_round.setup(self.used_songs)
        # start it
        await self.current_round.start()

    async def finish_round(self):
        # called by round.end()
        if self.state == "playing":
            await asyncio.sleep(1)  # brief inter-round pause
            await self._next_round()

    async def end_game(self):
        self.state = "ended"
        standings = sorted(self.players, key=lambda p: p.score, reverse=True)
        data = {
            "rankings": [
                {"rank": i+1, "username": p.username, "score": p.score}
                for i, p in enumerate(standings)
            ],
            "winner": {
                "username": standings[0].username,
                "score": standings[0].score
            } if standings else None
        }
        await self.broadcast({"type": "game_ended", "data": data})
        await asyncio.sleep(5)

    # ---------------- Messaging ----------------

    async def broadcast(self, message: Dict):
        stale = []
        for p in self.players:
            ok = await p.send_message(message["type"], message.get("data", {}))
            if not ok:
                stale.append(p)
        for p in stale:
            await self.remove_player(p)

    async def process_guess(self, player: Player, msg: Dict):
        """
        msg must include:
          - "guess": the song name
          - "guess_time": client-reported seconds since round_start
        """
        if self.state != "playing" or not self.current_round or player.has_guessed:
            return
        guess = msg.get("guess", "")
        guess_time = msg.get("guess_time", 0.0)
        await self.current_round.register_guess(player, guess, guess_time)


