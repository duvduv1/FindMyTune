import io
import numpy as np
from pydub import AudioSegment

def convert_audio_to_pcm(data: bytes, fmt: str = "wav") -> np.ndarray:
    """
    Converts raw audio bytes into a mono, 1D NumPy array of floats in [-1.0, +1.0].

    Args:
      data: Raw audio file bytes (e.g. received over the network).
      fmt:  Format hint (“wav”, “mp3”, etc.), used by pydub to parse.

    Returns:
      A NumPy float32 array shaped (num_samples,), normalized to ±1.0.
    """
    # 1) Load into a pydub AudioSegment
    audio = AudioSegment.from_file(io.BytesIO(data), format=fmt)

    # 2) Convert to mono (mixes channels)
    mono = audio.set_channels(1)

    # 3) Get raw samples as an array of ints
    samples = np.array(mono.get_array_of_samples(), dtype=np.float32)

    # 4) Normalize based on sample width
    max_val = float(1 << (8 * mono.sample_width - 1))
    pcm = samples / max_val

    return pcm