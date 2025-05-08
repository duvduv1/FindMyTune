# server.py

import os
import asyncio
import json
import base64
from typing import Dict

import websockets
from websockets.legacy.server import WebSocketServerProtocol

from settings                import (
    SERVER_HOST, SERVER_PORT, USE_SSL, USERS_DB_PATH, SONGS_DB_PATH,
    MAX_FAILED_LOGIN, BRUTE_FORCE_WINDOW, RATE_LIMIT, RATE_LIMIT_WINDOW,
    SESSION_TIMEOUT, SSL_CERT_PATH, SSL_KEY_PATH
)
from security.brute_force      import BruteForceProtector
from security.rate_limiter     import RateLimiter
from security.session_manager  import SessionManager
from security.ssl_context      import create_ssl_context
from database.users_database   import UsersDatabase
from database.song_database    import SongDatabase
from model.predictor           import predict_from_bytes
from game.player               import Player
from game.game_hub             import GameHub
from security.crypto_utils     import verify_password, hash_password
from history_utils             import get_user_history_payload

# Shared state:
sessions     = SessionManager()
brute_force  = BruteForceProtector(MAX_FAILED_LOGIN, BRUTE_FORCE_WINDOW)
rate_limiter = RateLimiter(RATE_LIMIT, RATE_LIMIT_WINDOW)
USERS_DB     = UsersDatabase(db_path=USERS_DB_PATH)
SONGS_DB     = SongDatabase(db_path=SONGS_DB_PATH)
game_hub     = GameHub(songs_db=SONGS_DB)

async def handler(ws):
    """
    Handles a single WebSocket connection.
    Expects JSON messages of form:
      { "action": "...", "data": { … } }
    Replies likewise with JSON.
    """
    # Extract client IP for rate/brute checks:
    peer = ws.remote_address[0]

    # 1) First‐connect rate limiting
    if not rate_limiter.allow(peer):
        await ws.close()
        return

    user = None
    token = None

    # 2) Authentication loop
    async for raw in ws:  # wait for login/signup
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            continue

        action = msg.get("action")
        data   = msg.get("data", {})

        # — SIGNUP —
        if action == "signup":
            uname = data.get("username", "").strip()
            pwd   = data.get("password", "")

            # 1) Require both fields
            if not uname or not pwd:
                await ws.send(json.dumps({
                    "status": "error", "reason": "username_password_required"
                }))
                continue

            # 2) Enforce uniqueness
            if USERS_DB.get_user_by_username(uname):
                await ws.send(json.dumps({
                    "status": "error", "reason": "user_exists"
                }))
                continue

            # 3) Re‑hash the client hash and store
            hashed_pwd = hash_password(pwd)
            created = USERS_DB.add_user(uname, hashed_pwd)
            if not created:
                await ws.send(json.dumps({
                    "status": "error", "reason": "couldn't_create_user"
                }))

            # 4) Success - issue session token
            else:
                token = sessions.create_session(uname)
                user = uname
                await ws.send(json.dumps({
                    "status": "ok", "token": token
                }))
                break

        # — LOGIN —
        elif action == "login":
            if brute_force.is_blocked(peer):
                await ws.send(json.dumps({
                    "status": "error", "reason": "too_many_attempts"
                }))
                continue

            uname_in = data.get("username", "").strip()
            pwd_in = data.get("password", "")
            row = USERS_DB.get_user_by_username(uname_in)
            if row and verify_password(pwd_in, row[2]):
                uname = row[1]
                token = sessions.create_session(uname)
                user  = uname
                await ws.send(json.dumps({
                    "status": "ok", "token": token
                }))
                break
            else:
                brute_force.register_failure(peer)
                await ws.send(json.dumps({
                    "status": "error", "reason": "invalid_credentials"
                }))
                continue

        else:
            await ws.send(json.dumps({
                "status": "error", "reason": "auth_required"
            }))

    if not user:
        await ws.close()
        return

    # 3) Main loop
    async for raw in ws:
        # rate‑limit per request
        if not rate_limiter.allow(peer):
            await ws.send(json.dumps({
                "status": "error", "reason": "rate_limit_exceeded"
            }))
            break

        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            continue

        action = msg.get("action")
        data   = msg.get("data", {})

        # ping/pong
        if action == "ping":
            await ws.send(json.dumps({"action": "pong"}))
            continue

        # validate session
        t = data.get("token")
        if t != token or sessions.validate_session(t) != user:
            await ws.send(json.dumps({
                "status": "error", "reason": "session_invalid"
            }))
            break

        # — HISTORY —
        if action == "get_history":
            # Fetch and send user history
            history_payload = get_user_history_payload(user)
            await ws.send(json.dumps({
                'status': 'ok',
                'history': history_payload
            }))
            continue

        # — PREDICT —
        if action == "predict":
            audio_b64 = data.get("audio")
            fmt       = data.get("format", "wav")
            if not audio_b64:
                await ws.send(json.dumps({
                    "status": "error", "reason": "audio_required"
                }))
                continue

            try:
                pcm = base64.b64decode(audio_b64)
            except Exception:
                await ws.send(json.dumps({
                    "status": "error", "reason": "invalid_audio_format"
                }))
                continue

            info = predict_from_bytes(pcm, fmt=fmt)
            await ws.send(json.dumps({
                "status": "ok", "song": info
            }))
            # ask client to confirm
            await ws.send(json.dumps({"action": "confirm"}))
            continue

        # — FEEDBACK —
        if action == "prediction_feedback":
            song_name = data.get("song_name")
            correct   = data.get("correct", False)
            if song_name and correct:
                SONGS_DB.update_song_history(user, song_name)
            await ws.send(json.dumps({
                "status": "ok", "action": "feedback_received"
            }))
            continue

        # — CREATE GAME —
        if action == "create_game":
            host_player = Player(user, ws)
            server = await game_hub.create_game(host_player)
            if not server:
                await ws.send(json.dumps({
                    "status": "error", "reason": "max_games_reached"
                }))
            else:
                # 1) Tell the client that creation succeeded
                await ws.send(json.dumps({
                    "status": "ok", "game_id": server.game_id
                }))

                # 2) Immediately send the full lobby state
                await ws.send(json.dumps({
                    "type": "game_state",
                    "data": {
                        "game_id": server.game_id,
                        "host": server.host.username,
                        "state": server.state,
                        "settings": server.settings,
                        "players": [
                            {"id": p.id, "username": p.username}
                            for p in server.players
                        ]
                    }
                }))
            continue

        # — JOIN GAME —
        if action == "join_game":
            p = Player(user, ws)
            success, reason = await game_hub.join_game(p, data.get("game_id",""))
            await ws.send(json.dumps({
                "status": "ok" if success else "error",
                **({"reason": reason} if not success else {})
            }))
            continue

        if action == "get_players":
            await game_hub.get_players(ws)
            continue

        # — GUESS —
        if action == "guess":
            # Look up the GameServer for this user
            success, reason = await game_hub.handle_guess(ws, {
                "guess": data.get("guess", ""),
                "guess_time": data.get("guess_time", 0.0),
            })
            await ws.send(json.dumps({
                "status": "ok" if success else "error",
                **({"reason": reason} if not success else {})
            }))
            continue

        # — NEXT ROUND (host only) —
        if action == "next_round":
            success, reason = await game_hub.handle_next_round(ws)
            await ws.send(json.dumps({
                "status": "ok" if success else "error",
                **({"reason": reason} if not success else {})
            }))
            continue

        # — KICK PLAYER —
        if action == "kick_player":
            success, reason = await game_hub.kick_player_by_username(ws, data.get("username",""))
            await ws.send(json.dumps({
                "status": "ok" if success else "error",
                **({"reason":reason} if not success else {})
            }))
            continue

        # — UPDATE SETTINGS —
        if action == "update_settings":
            ok, reason = await game_hub.update_lobby_settings(ws, data)
            await ws.send(json.dumps({
                "status": "ok" if ok else "error",
                **({"reason":reason} if not ok else {})
            }))
            continue

        # — START GAME —
        if action == "start_game":
            ok, reason = await game_hub.start_game(ws)
            await ws.send(json.dumps({
                "status": "ok" if ok else "error",
                **({"reason": reason} if not ok else {})
            }))
            continue

        # — LOGOUT —
        if action == "logout":
            # Remove their session server‐side
            sessions.sessions.pop(token, None)
            # Acknowledge back to the client
            await ws.send(json.dumps({"status": "ok"}))
            # Break out of the loop to close the socket
            break

        # unknown
        await ws.send(json.dumps({
            "status": "error", "reason": "unknown_action"
        }))

    await ws.close()

async def main():
    # 1) Build SSLContext if needed
    ssl_ctx = create_ssl_context() if USE_SSL else None

    # 2) Start the WebSocket server (this now runs inside a running loop)
    server = await websockets.serve(
        handler,
        host='0.0.0.0',
        port=SERVER_PORT,
        ssl=ssl_ctx,
        ping_interval=None
    )
    print(f"WebSocket server listening on {SERVER_HOST}:{SERVER_PORT}...")

    # 3) Schedule your background prune task
    asyncio.create_task(game_hub.prune_finished())

    # 4) Keep the server alive forever
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())