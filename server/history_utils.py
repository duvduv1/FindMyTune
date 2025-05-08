import base64
import os
from typing import List, Dict
from database.song_database import SongDatabase
from database.users_database import UsersDatabase
from game.song import Song
from settings import SONGS_DB_PATH, USERS_DB_PATH


def get_user_history_payload(username: str) -> List[Dict]:
    """
    Fetches a user's play history and returns a list of song dicts with their metadata,
    including base64-encoded album cover images and played_at timestamps.
    """

    # 1) Connect to SongDatabase
    db = SongDatabase(SONGS_DB_PATH)

    # 2) Get raw history entries: [{'song_name':..., 'played_at':...}, ...]
    raw_history = db.get_user_history(username)

    payload = []
    for entry in raw_history:
        name = entry['song_name']
        played_at = entry['played_at']

        # 3) Load full song metadata
        song = Song(name, db)
        info = song.to_dict()

        # 4) Remove id
        info.pop('id')

        # 5) Attach played_at
        info['played_at'] = played_at

        # 6) Read album_cover_image file and base64-encode
        cover_path = info['album_cover_image']
        if cover_path and os.path.isfile(cover_path):
            with open(cover_path, 'rb') as f:
                raw_bytes = f.read()
            info['album_cover_image'] = base64.b64encode(raw_bytes).decode('ascii')
        else:
            # If no file, leave the original or set empty
            info['album_cover_image'] = None
        payload.append(info)

    return payload
