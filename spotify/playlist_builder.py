# spotify/playlist_builder.py

import os
from typing import Set, List
import yt_dlp
import requests
from PIL import Image
from io import BytesIO

from spotify.spotify_api import (
    get_playlist_tracks,
    get_artist_top_tracks,
    add_items_to_playlist,
    get_album_image_url
)


def get_artists_from_playlist(playlist_id: str) -> Set[str]:
    """
    Fetch all unique artist IDs from the given playlist,
    via the spotify_api wrapper.
    """
    artists: Set[str] = set()
    for item in get_playlist_tracks(playlist_id):
        track = item.get("track", item)
        for artist in track.get("artists", []):
            artists.add(artist["id"])
    return artists


def build_song_playlist(artist_ids: Set[str], playlist_id: str, top_n: int = 5) -> None:
    """
    Ensure the target playlist contains each artist’s top `top_n` tracks,
    adding any that aren’t already there.
    """
    # 1) Fetch existing track names in the playlist
    existing = {
        item["track"]["name"].lower()
        for item in get_playlist_tracks(playlist_id)
    }

    # 2) For each artist, pull top tracks and queue any new ones
    to_add: List[str] = []
    for aid in artist_ids:
        for t in get_artist_top_tracks(aid, limit=top_n):
            if t["name"].lower() not in existing:
                to_add.append(t["uri"])

    # 3) Push additions back to Spotify
    if to_add:
        add_items_to_playlist(playlist_id, to_add)


def download_track_mp3(track_name: str, folder: str) -> None:
    """
    Use yt-dlp to find & grab the best audio for `track_name`,
    saving as MP3 in `folder`.
    """
    os.makedirs(folder, exist_ok=True)
    safe = sanitize_filename(track_name)
    outtmpl = os.path.join(folder, f"{safe}.%(ext)s")
    target_mp3 = os.path.join(folder, f"{safe}.mp3")

    if os.path.exists(target_mp3):
        return

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'outtmpl': outtmpl,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"ytsearch1:{track_name} audio"])


def sanitize_filename(name: str) -> str:
    """
    Strip or replace characters illegal in file names.
    """
    return name.replace("/", "_").replace("\\", "_")


def download_album_image(album_name: str, size: tuple[int, int] = (150, 150)) -> str | None:
    """
    Download & resize album art (via spotify_api.get_album_image_url),
    saving under ALBUM_IMAGES_DIR and returning the file path.
    """
    url = get_album_image_url(album_name)
    if not url:
        return None

    from settings import ALBUM_IMAGES_DIR  # local import to avoid circular dependencies
    os.makedirs(ALBUM_IMAGES_DIR, exist_ok=True)
    safe = sanitize_filename(album_name)
    dest = os.path.join(ALBUM_IMAGES_DIR, f"{safe}.jpg")
    if os.path.exists(dest):
        return dest

    try:
        resp = requests.get(url, stream=True, timeout=10)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert("RGB")
        img = img.resize(size, Image.LANCZOS)
        img.save(dest, format="JPEG", quality=75, optimize=True)
        return dest
    except Exception:
        return None
