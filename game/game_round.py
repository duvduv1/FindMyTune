# project/game/game_round.py

import os
import random
import asyncio
from typing import Set, List, Dict, Any
from game.game_utils import clip_to_base64
from game.player import Player
from game.song import Song
from settings import GAME_SONGS_DIR
import base64


class GameRound:
    """
    Encapsulates a single “guess the song” round.
    Picks a clip, presents options, collects guesses, scores players, and reports results.
    """

    def __init__(self,
                 round_number: int,
                 players: List[Player],
                 songs_db,
                 round_time: int):
        self.round_number = round_number
        self.players      = players
        self.songs_db     = songs_db
        self.round_time   = round_time

        # Populated in setup()
        self.correct_song_name: str = ""
        self.clip_path: str = ""
        self.options: List[str] = []

        # Runtime state
        self.start_ts: float = 0.0
        self.guesses: int = 0
        self.correct_guessers: List[Player] = []

    async def setup(self, used_songs: set[str]) -> None:
        """
        Selects a song folder not in used_songs,
        picks a random clip within it, and builds 4 options.
        """
        # 1) List all songs
        all_songs = [d for d in os.listdir(GAME_SONGS_DIR)
                     if os.path.isdir(os.path.join(GAME_SONGS_DIR, d))]
        # 2) Filter out used
        choices = [s for s in all_songs if s not in used_songs]
        if not choices:
            used_songs.clear()
            choices = all_songs
        # 3) Pick correct song
        self.correct_song_name = random.choice(choices)
        used_songs.add(self.correct_song_name)

        # 4) Pick random clip file
        song_dir = os.path.join(GAME_SONGS_DIR, self.correct_song_name)
        clips = [f for f in os.listdir(song_dir) if f.endswith((".mp3",".wav"))]
        self.clip_path = os.path.join(song_dir, random.choice(clips))

        # 5) Build options list (1 correct + 3 random wrong)
        wrong = [s for s in all_songs if s != self.correct_song_name]
        self.options = random.sample(wrong, k=min(3, len(wrong)))
        self.options.append(self.correct_song_name)
        random.shuffle(self.options)

    async def start(self) -> None:
        """
        Broadcasts 'round_start', then waits self.round_time seconds
        or until all players have guessed, then calls end().
        """
        # Reset per-round state on each player
        for p in self.players:
            p.reset_round()

        clip_b64 = clip_to_base64(self.clip_path)

        options_payload = []
        for option in self.options:
            song = Song(option, self.songs_db)
            info = song.to_dict()
            info.pop("id", None)
            cover_path = info['album_cover_image']
            if cover_path and os.path.isfile(cover_path):
                with open(cover_path, 'rb') as f:
                    raw_bytes = f.read()
                info['album_cover_image'] = base64.b64encode(raw_bytes).decode('ascii')
            options_payload.append(info)

        # Broadcast start message including clip path & options
        payload = {
            "round_number": self.round_number,
            "round_time":   self.round_time,
            "options":      options_payload,
            # Clip path could be streamed via server file logic
            "clip_b64":    clip_b64
        }
        await asyncio.gather(*[p.send_message("round_start", payload)
                               for p in self.players])

        self.start_ts = asyncio.get_event_loop().time()
        # Schedule automatic end
        asyncio.create_task(self._timer())

    async def _timer(self) -> None:
        await asyncio.sleep(self.round_time)
        await self.end()

    async def register_guess(self, player: Player, guess: str, guess_time: float) -> None:
        """
        Called when a player submits a guess.
        Tags them as guessed and if correct, adds to correct_guessers.
        """
        if player.has_guessed:
            return
        player.has_guessed = True
        # Use client-reported guess_time directly (seconds since round_start)
        player.guess_time = guess_time
        player.guessed_correctly = (guess == self.correct_song_name)
        self.guesses += 1
        if player.guessed_correctly:
            self.correct_guessers.append(player)
        # End early if all have guessed
        if self.guesses >= len(self.players):
            await self.end()

    async def end(self):
        """
        Ends the round: calculates points, sends each player their personal results,
        then broadcasts the placements table to all players.
        """
        # Prevent multiple end calls
        if hasattr(self, "_ended") and self._ended:
            return
        self._ended = True

        # 1) Calculate and assign points
        await self.calculate_points()

        # 2) Prepare per-player results and send individually
        for player in self.game_server.players:
            correct_song = Song(self.correct_song_name, self.songs_db)
            correct_info = correct_song.to_dict()
            correct_info.pop("id", None)
            cover_path = correct_info['album_cover_image']
            if cover_path and os.path.isfile(cover_path):
                with open(cover_path, 'rb') as f:
                    raw_bytes = f.read()
                correct_info['album_cover_image'] = base64.b64encode(raw_bytes).decode('ascii')
            else:
                correct_info['album_cover_image'] = None
            data = {
                "correct_answer": correct_info,
                "correct": player.guessed_correctly,
                "guess_time": player.guess_time,
                "points_earned": player.current_round_points,
                "total_score": player.score
            }
            await player.send_message("your_result", data)

        # 3) Short pause before broadcasting the full placements
        await asyncio.sleep(2)

        # 4) Build placements table sorted by total_score desc
        sorted_players = sorted(
            self.game_server.players,
            key=lambda p: p.score,
            reverse=True
        )
        placements = []
        for rank, p in enumerate(sorted_players, start=1):
            placements.append({
                "placement": rank,
                "username": p.username,
                "points_this_round": p.current_round_points,
                "total_score": p.score
            })

        # 5) Broadcast round_end with the placements table
        await self.game_server.broadcast({
            "type": "round_end",
            "data": {
                "round_number": self.round_number,
                "placements_table": placements,
                "waiting_for_host": True
            }
        })

    async def calculate_points(self):
        """
        Assigns points to each player in self.correct_guessers based on:
          - Base points
          - Time bonus (percentage of time left × time_factor)
          - Placement bonus
          - Rarity bonus
        """
        base_points = 200
        time_factor = 2.5
        placement_bonus = {
            0: 1.20,
            1: 1.14,
            2: 1.09,
            3: 1.05,
            4: 1.02,
        }

        # Ensure we sort by guess_time (fastest first)
        self.correct_guessers.sort(key=lambda p: p.guess_time or float('inf'))
        total_players = len(self.game_server.players)
        correct_count = len(self.correct_guessers)

        for idx, player in enumerate(self.correct_guessers):
            # 1) Base points
            pts = base_points

            # 2) Time bonus
            time_pct = max(0.0, 1 - (player.guess_time / self.round_time))
            pts = int(pts * time_pct * time_factor)

            # 3) Placement bonus (if more than one player)
            if total_players > 1 and idx in placement_bonus:
                pts = int(pts * placement_bonus[idx])

            # 4) Rarity bonus (fewer correct guesses → higher multiplier)
            if total_players > 1:
                rarity = 1 + (1 - (correct_count / total_players)) * 0.4
                pts = int(pts * rarity)

            # 5) Assign
            player.current_round_points = pts
            player.score += pts