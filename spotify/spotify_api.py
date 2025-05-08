# spotify/spotify_api.py

from typing import List, Dict, Optional
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException

from settings import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_REDIRECT_URI,
    SPOTIFY_SCOPE
)

# Setup user‑auth flow
_auth_manager = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=SPOTIFY_SCOPE,
    cache_path='.spotify_token_cache'
)
sp = spotipy.Spotify(auth_manager=_auth_manager)


def get_playlist_tracks(playlist_id: str) -> List[Dict]:
    """
    Retrieve all items from a Spotify playlist (paginated).
    Returns a list of track dicts.
    """
    results: List[Dict] = []
    try:
        resp = sp.playlist_items(
            playlist_id,
            fields='items.track,next',
            limit=100
        )
        results.extend(item['track'] for item in resp.get('items', []) if item.get('track'))
        while resp.get('next'):
            resp = sp.next(resp)
            results.extend(item['track'] for item in resp.get('items', []) if item.get('track'))
    except SpotifyException as e:
        print(f"[ERROR] Spotify API playlist_tracks failed: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error fetching playlist {playlist_id}: {e}")
    return results


def get_artist_top_tracks(artist_id: str, limit: int = 5) -> List[Dict]:
    """
    Fetch an artist’s top tracks.
    Returns up to `limit` track dicts.
    """
    try:
        resp = sp.artist_top_tracks(artist_id)
        return resp.get('tracks', [])[:limit]
    except SpotifyException as e:
        print(f"[ERROR] Spotify API artist_top_tracks failed for {artist_id}: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error fetching top tracks for {artist_id}: {e}")
    return []


def add_items_to_playlist(playlist_id: str, uris: List[str]) -> None:
    """
    Add the given list of track URIs to the playlist in batches of 100.
    """
    try:
        for i in range(0, len(uris), 100):
            batch = uris[i:i+100]
            sp.playlist_add_items(playlist_id, batch)
    except SpotifyException as e:
        print(f"[ERROR] Spotify API add_items_to_playlist failed: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error adding items to playlist {playlist_id}: {e}")


def get_album_image_url(album_name: str) -> Optional[str]:
    """
    Search for an album by name and return its primary image URL.
    """
    try:
        resp = sp.search(q=f'album:"{album_name}"', type='album', limit=1)
        items = resp.get('albums', {}).get('items', [])
        if not items:
            return None
        images = items[0].get('images', [])
        if not images:
            return None
        return images[0].get('url')
    except SpotifyException as e:
        print(f"[ERROR] Spotify API get_album_image_url failed for {album_name}: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error searching album {album_name}: {e}")
    return None


def get_track_metadata(track_name: str) -> Dict[str, Optional[str]]:
    """
    Search Spotify by track_name and return its metadata dict with only:
      - track_name
      - artist_name
      - album_name
      - album_type
      - release_date
      - spotify_url
    """
    try:
        resp = sp.search(q=f'track:"{track_name}"', type='track', limit=1)
        items = resp.get('tracks', {}).get('items', [])
        track = items[0]
        return {
            'track_name': track.get('name'),
            'artist_name': track.get('artists', [{}])[0].get('name'),
            'album_name': track.get('album', {}).get('name'),
            'album_type': track.get('album', {}).get('album_type'),
            'release_date': track.get('album', {}).get('release_date'),
            'spotify_url': track.get('external_urls', {}).get('spotify')
        }
    except SpotifyException as e:
        print(f"[ERROR] Spotify API search track failed for {track_name}: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error searching track {track_name}: {e}")
    return {k: None for k in [
        'track_name','artist_name','album_name',
        'album_type','release_date','spotify_url']}