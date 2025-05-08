# game/game_hub.py

import uuid
import asyncio
from typing import Dict, Optional, Tuple
import websockets
from websockets.legacy.server import WebSocketServerProtocol
from game.game_server import GameServer
from game.player      import Player

class GameHub:
    def __init__(self, songs_db, max_games: int = 100):
        self.songs_db      = songs_db
        self._games        = {}     # game_id -> GameServer
        self._user_games   = {}     # player.id -> game_id
        self.max_games     = max_games
        self._lock         = asyncio.Lock()

    def _make_unique_id(self) -> str:
        gid = uuid.uuid4().hex[:8]
        while gid in self._games:
            gid = uuid.uuid4().hex[:8]
        return gid

    async def create_game(self, host_player: Player) -> Optional[GameServer]:
        async with self._lock:
            if len(self._games) >= self.max_games:
                return None
            gid = self._make_unique_id()
            gs = GameServer(gid, host_player, self.songs_db)
            await gs.add_player(host_player)
            self._games[gid] = gs
            self._user_games[host_player.id] = gid
            return gs

    async def join_game(self, player: Player, game_id: str) -> Tuple[bool, str]:
        async with self._lock:
            gs = self._games.get(game_id)
            if not gs:               return False, "game_not_found"
            if gs.state != "lobby":  return False, "game_already_started"
            if len(gs.players) >= 8: return False, "game_full"
            await gs.add_player(player)
            self._user_games[player.id] = game_id
            return True, ""

    async def kick_player_by_username(self, host_ws, target_username: str) -> Tuple[bool,str]:
        async with self._lock:
            for gid, gs in self._games.items():
                if gs.host.websocket == host_ws:
                    target = next((p for p in gs.players if p.username == target_username), None)
                    if not target: return False, "player_not_found"
                    # notify & remove
                    await target.send_message("kicked", {"reason":"removed_by_host"})
                    await gs.remove_player(target)
                    self._user_games.pop(target.id, None)
                    return True, ""
        return False, "not_host"

    async def update_lobby_settings(self, host_ws, data: Dict) -> Tuple[bool,str]:
        async with self._lock:
            # find server by host socket
            for gs in self._games.values():
                if gs.host.websocket == host_ws and gs.state=="lobby":
                    # prepare new_settings
                    new = {}
                    if "num_rounds" in data:  new["num_rounds"] = data["num_rounds"]
                    if "round_time" in data:  new["round_time"] = data["round_time"]
                    ok = await gs.update_settings(new)
                    return (True,"") if ok else (False,"invalid_settings")
        return False, "not_host_or_not_lobby"

    async def start_game(self, host_ws) -> Tuple[bool,str]:
        async with self._lock:
            for gs in self._games.values():
                if gs.host.websocket == host_ws and gs.state=="lobby":
                    ok = await gs.start_game()
                    return (True,"") if ok else (False,"cannot_start")
        return False, "not_host_or_not_lobby"

    async def handle_guess(self,
                           ws: WebSocketServerProtocol,
                           guess_msg: Dict[str, any]
                           ) -> Tuple[bool, str]:
        """
        Find the GameServer & Player instance by websocket, then forward the guess.
        """
        # 1) Find the server that holds this ws
        for server in self._games.values():
            for p in server.players:
                if p.websocket is ws:
                    # 2) Dispatch straight to GameServer
                    await server.process_guess(p, guess_msg)
                    return True, ""
        return False, "not_in_game"

    async def handle_next_round(self,ws: WebSocketServerProtocol,) -> Tuple[bool, str]:
        """
        Only the host may trigger the next round.
        Finds the GameServer for `username` and calls its private _next_round().
        """
        for gs in self._games.values():
            if gs.host.websocket == ws:
                # start the next round
                await gs._next_round()
                return True, ""

        return False, "not host"

    async def prune_finished(self):
        while True:
            await asyncio.sleep(60)
            async with self._lock:
                for gid, gs in list(self._games.items()):
                    if gs.state == "ended":
                        for pid, g in list(self._user_games.items()):
                            if g == gid: del self._user_games[pid]
                        del self._games[gid]

    async def get_players(self, ws: WebSocketServerProtocol):
        for server in self._games.values():
            for p in server.players:
                if p.websocket is ws:
                    await server.get_players(p)
                    return

