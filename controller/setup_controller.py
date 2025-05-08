# controller/setup_controller.py

import os
import time
from pathlib import Path
from threading import Thread, Event
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor

from spotify.playlist_builder import (
    get_artists_from_playlist,
    build_song_playlist
)
from spotify.spotify_api import get_playlist_tracks, get_track_metadata
from spotify.spotify_api import download_album_image
from spotify.spotify_api import download_track_mp3
from audio.audio_processor import process_audio
from database.song_database import SongDatabase
from model.model import pretrain_model, create_model
from settings import (
    ARTIST_PLAYLIST_ID,
    SONG_PLAYLIST_ID,
    AUDIO_FOLDER_PATH,
    SONGS_DB_PATH,
    MODEL_PATH,
    MAX_SONG_THREADS
)

# Single queue and event to coordinate processing vs uploading
db = SongDatabase(db_path=SONGS_DB_PATH)
upload_queue = Queue()
processing_complete = Event()


def process_and_queue_song(song_name: str, audio_path: str):
    """
    Prepare song data and enqueue it for database upload.
    Does audio processing, fetches Spotify metadata and album image.
    """
    try:
        # 1) Split audio and create spectrograms
        spec_folder = process_audio(
            song_name=song_name,
            audio_path=audio_path,
            segment_length=5.0,
            overlap=0.5
        )

        # 2) Fetch metadata from Spotify
        meta = get_track_metadata(song_name)

        # 3) Download album image locally
        cover_path = None
        if meta.get('album_name'):
            cover_path = download_album_image(meta['album_name'])

        # 4) Build song data dict for DB insertion
        song_data = {
            'song_name':      meta.get('track_name'),
            'artist_name':    meta.get('artist_name'),
            'album_name':     meta.get('album_name'),
            'album_cover_image': cover_path,
            'album_type':     meta.get('album_type'),
            'release_date':   meta.get('release_date'),
            'spotify_url':    meta.get('spotify_url'),
            'spectrograms':   spec_folder
        }

        upload_queue.put(song_data)
    except Exception as e:
        print(f"[ERROR] Failed to process {song_name}: {e}")


def upload_worker():
    """
    Worker thread that takes song_data from the queue and writes to DB.
    """
    while True:
        try:
            song_data = upload_queue.get(block=True, timeout=1)
        except Empty:
            if processing_complete.is_set() and upload_queue.empty():
                break
            time.sleep(0.1)
            continue

        try:
            # add_song now accepts full metadata dict
            db.add_song(song_data)
        except Exception as e:
            print(f"[ERROR] Upload failed for {song_data.get('song_name')}: {e}")
        finally:
            upload_queue.task_done()


def run_initial_setup():
    """
    1) Rebuild playlist
    2) Download MP3s
    3) Process audio in parallel; enqueue for DB upload
    4) Upload to DB in single worker
    5) Pretrain & train model
    """
    # Ensure directories exist
    Path(AUDIO_FOLDER_PATH).mkdir(parents=True, exist_ok=True)
    Path(os.path.dirname(SONGS_DB_PATH)).mkdir(parents=True, exist_ok=True)

    # 1) Rebuild song playlist
    try:
        artist_ids = get_artists_from_playlist(ARTIST_PLAYLIST_ID)
        build_song_playlist(artist_ids, SONG_PLAYLIST_ID)
    except Exception as e:
        print(f"[ERROR] Failed to rebuild playlist: {e}")
        return

    # 2) Collect MP3 file list
    mp3_files = [f for f in os.listdir(AUDIO_FOLDER_PATH) if f.endswith('.mp3')]
    print(f"Found {len(mp3_files)} MP3 files to process")

    # 3) Start upload worker thread
    uploader = Thread(target=upload_worker, daemon=True)
    uploader.start()

    # 4) Download tracks and process in parallel
    with ThreadPoolExecutor(max_workers=MAX_SONG_THREADS) as executor:
        futures = []
        for track in get_playlist_tracks(SONG_PLAYLIST_ID):
            title = track.get('name', '')
            artists = ' '.join(a.get('name','') for a in track.get('artists', []))
            filename = f"{title} - {artists}.mp3"
            mp3_path = os.path.join(AUDIO_FOLDER_PATH, filename)

            def task(t=title, art=artists, path=mp3_path):
                # download audio
                download_track_mp3(f"{t} {art}", AUDIO_FOLDER_PATH)
                # process + queue metadata
                process_and_queue_song(f"{t} - {art}", path)

            futures.append(executor.submit(task))
        for f in futures:
            try:
                f.result()
            except Exception:
                pass

    # 5) Signal completion and wait for uploads
    processing_complete.set()
    upload_queue.join()
    print("All songs processed and uploaded")

    # 6) Contrastive pre‑training
    try:
        pretrain_model(db)
    except Exception as e:
        print(f"[ERROR] Contrastive pretraining failed: {e}")
        return

    # 7) Classification training
    try:
        create_model(db, MODEL_PATH, pretrained=True)
    except Exception as e:
        print(f"[ERROR] Classification training failed: {e}")
        return

    print("Initial setup finished successfully")

if __name__ == '__main__':
    run_initial_setup()