import threading
import os
import time
import torch
import numpy as np
import base64

from torch.utils.checkpoint import checkpoint

from model.model import SongCNN
from settings import MODEL_PATH, SONGS_DB_PATH
from database.song_database import SongDatabase
from audio.audio_converter import convert_audio_to_pcm
from audio.audio_processor import prepare_audio
from game.song import Song

# model/predictor.py

class ModelPool:
    def __init__(self,
                 model_path: str = MODEL_PATH,
                 pool_size: int = 5):
        self.model_path  = model_path
        self.pool_size   = pool_size
        self._lock       = threading.Lock()
        self._mtimes     = None      # start as None so first load always happens
        self._models     = []
        # initial load
        self._reload_if_needed()

    def _load_model(self) -> SongCNN:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        checkpoint = torch.load(self.model_path, map_location="cpu")
        num_classes = checkpoint.get("num_classes")
        model = SongCNN(num_classes)
        model.load_state_dict(checkpoint["model_state_dict"])
        model.to(device)
        model.eval()
        return model

    def _reload_if_needed(self):
        """
        Reload all models if:
          - file is present and mtime changed, or
          - pool is currently empty (first run or after failure)
        """
        try:
            mtime = os.path.getmtime(self.model_path)
        except OSError:
            # can’t access model file; leave existing pool alone
            return

        # if first‐time load (self._mtimes is None) or file changed
        if self._mtimes is None or mtime != self._mtimes:
            with self._lock:
                # rebuild entire pool
                new_models = []
                for _ in range(self.pool_size):
                    new_models.append(self._load_model())
                self._models = new_models
                self._mtimes = mtime

    def get(self) -> SongCNN:
        """
        Returns one model instance from the pool (round‑robin by time).
        Ensures pool is nonempty, reloading if needed.
        """
        # attempt reload
        self._reload_if_needed()

        # if still empty (e.g. model file missing), load at least one
        if not self._models:
            with self._lock:
                # try a minimal load
                model = self._load_model()
                self._models = [model]

        idx = time.time_ns() % len(self._models)
        return self._models[idx]

    def label_to_song(self, label: int):
        checkpoint = torch.load(self.model_path, map_location="cpu")
        labels_to_songs = checkpoint.get("labels_to_songs")
        song = labels_to_songs[label]
        return song


# Singleton pool for app usage
model_pool = ModelPool()

# Helper to combine conversion + spectrogram prep in one go
def prepare_audio_bytes(audio_bytes: bytes, fmt: str) -> np.ndarray:
    pcm = convert_audio_to_pcm(audio_bytes, fmt)
    return prepare_audio(pcm)


def predict_from_bytes(audio_bytes: bytes,
                       fmt: str = "wav",) -> dict:
    """
    Full end-to-end prediction pipeline:
      1. Convert raw bytes to PCM array
      2. Prepare fixed-length spectrogram
      3. Run inference on pooled SongCNN
      4. Lookup metadata in SongDatabase
      5. Return song info dict
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # 1) prepare spectrogram
    spectrogram = prepare_audio_bytes(audio_bytes, fmt)

    # 2) inference
    model = model_pool.get()
    input_tensor = torch.tensor(spectrogram, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
    input_tensor = input_tensor.to(device)
    with torch.no_grad():
        logits = model(input_tensor)
        idx = torch.argmax(logits, dim=1).item()
        song_name = model_pool.label_to_song(idx)

    # 3) lookup metadata
    db = SongDatabase(SONGS_DB_PATH)
    song = Song(song_name, db)
    song_info = song.to_dict()
    song_info.pop("id", None)
    cover_path = song_info['album_cover_image']
    if cover_path and os.path.isfile(cover_path):
        with open(cover_path, 'rb') as f:
            raw_bytes = f.read()
        song_info['album_cover_image'] = base64.b64encode(raw_bytes).decode('ascii')
    return song_info
