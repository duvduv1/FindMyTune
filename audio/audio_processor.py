# audio/audio_processor.py

import os
import random
import logging
from concurrent.futures import ProcessPoolExecutor
from typing import Tuple, List

import torch
import torchaudio
import torchaudio.functional as F
import torchaudio.transforms as T
import numpy as np

from settings import BACKGROUND_NOISES_DIR, SPECTROGRAM_DIR

logger = logging.getLogger(__name__)

# — Spectrogram & processing params (match your old code) —
SAMPLE_RATE    = 22050
N_FFT          = 2048
HOP_LENGTH     = 512
N_MELS         = 128
TOP_DB         = 80
MAX_PROCESSES  = 2     # as before
EPS            = 1e-8  # floor for spectrogram magnitudes
NOISE_LEVEL    = 1e-6  # tiny noise for all‑zero segments


def load_audio(file_path: str) -> torch.Tensor:
    """
    Load, resample, mono‑mix, and inject a tiny noise floor if totally silent.
    """
    try:
        waveform, sr = torchaudio.load(file_path)
    except Exception:
        logger.exception("Failed to load audio file %s", file_path)
        raise

    if sr != SAMPLE_RATE:
        waveform = T.Resample(sr, SAMPLE_RATE)(waveform)

    mono = waveform.mean(dim=0)
    if mono.abs().max() < EPS:
        mono = mono + torch.randn_like(mono) * NOISE_LEVEL

    return mono


def apply_window(audio: torch.Tensor) -> torch.Tensor:
    """
    Apply a Hann window across the entire segment.
    """
    window = torch.hann_window(audio.shape[-1], periodic=False)
    return audio * window


def normalize_volume(audio: torch.Tensor, target_peak: float = 0.7) -> torch.Tensor:
    """
    Scale so that max(abs(sample)) == target_peak; if silent, inject tiny noise.
    """
    max_val = audio.abs().max()
    if max_val < EPS:
        audio = audio + torch.randn_like(audio) * NOISE_LEVEL
        max_val = audio.abs().max()
    return audio * (target_peak / max_val)


def create_spectrogram(audio: torch.Tensor) -> torch.Tensor:
    """
    Build a mel‑spectrogram, clamp to EPS, convert to dB, and replace any NaNs/infs.
    """
    # 1) raw mel
    mel = T.MelSpectrogram(
        sample_rate=SAMPLE_RATE,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH,
        n_mels=N_MELS
    )(audio.unsqueeze(0))

    # 2) clamp to avoid zeros → -inf dB
    mel = torch.clamp(mel, min=EPS)

    # 3) to dB
    db = T.AmplitudeToDB(top_db=TOP_DB)(mel)

    # 4) replace any NaN or inf with floor (-TOP_DB)
    db = torch.where(torch.isfinite(db), db, torch.tensor(-TOP_DB))

    return db.squeeze(0)


def create_noisy_segment(segment: torch.Tensor) -> torch.Tensor:
    """
    “Dirty” variant: EQ → downsample → compress → synthetic noise → real noise.
    """
    seg = F.highpass_biquad(segment, SAMPLE_RATE, 300)
    seg = F.equalizer_biquad(seg, SAMPLE_RATE, 1800, gain=3.0, Q=1.0)
    seg = F.lowpass_biquad(seg, SAMPLE_RATE, 3400)

    # down/up sample
    y1 = T.Resample(SAMPLE_RATE, 16000)(seg.unsqueeze(0))
    seg = T.Resample(16000, SAMPLE_RATE)(y1).squeeze(0)

    # clip & renormalize
    peak = seg.abs().max() * 8
    seg = torch.clamp(seg, -peak, peak)
    seg = seg / seg.abs().max()

    # synthetic uniform noise
    seg = seg + torch.rand_like(seg) * 0.003

    # background noise
    try:
        files = [f for f in os.listdir(BACKGROUND_NOISES_DIR)
                 if os.path.isfile(os.path.join(BACKGROUND_NOISES_DIR, f))]
        if files:
            choice = random.choice(files)
            noise = load_audio(os.path.join(BACKGROUND_NOISES_DIR, choice))
            snr_db = random.uniform(20, 23)
            sig_p   = seg.pow(2).mean()
            noise_p = noise.pow(2).mean()
            scaled  = noise * torch.sqrt(sig_p / (noise_p * (10 ** (snr_db / 10))))
            if scaled.shape[0] >= seg.shape[0]:
                scaled = scaled[:seg.shape[0]]
            else:
                pad = seg.shape[0] - scaled.shape[0]
                scaled = torch.cat([scaled, torch.zeros(pad)], dim=0)
            seg = seg + scaled
    except Exception:
        logger.exception("Background‑noise mixing failed")

    return normalize_volume(seg)


def create_reverb_segment(segment: torch.Tensor) -> torch.Tensor:
    """
    “Reverb” variant: phone_speaker EQ + simple multi‑tap echo.
    """
    seg = F.highpass_biquad(segment, SAMPLE_RATE, 200)
    seg = F.lowpass_biquad(seg, SAMPLE_RATE, 4800)
    seg = F.equalizer_biquad(seg, SAMPLE_RATE, 250, gain=-12.0, Q=1.0)

    echo_accum = segment.clone()
    for i in range(8):
        delay = int((0.02 + i * 0.012) * SAMPLE_RATE)
        echo = torch.zeros_like(segment)
        echo[delay:] = segment[:-delay]
        echo_accum = echo_accum + echo * (0.12 * (0.7 ** i))

    return normalize_volume(seg + echo_accum * 0.25)


def process_song_segment(args: Tuple[np.ndarray, int, str]) -> None:
    """
    Called inside a ProcessPoolExecutor: turns one chunk into 3 specs.
    """
    segment_np, idx, folder = args
    try:
        segment = torch.from_numpy(segment_np)
        seg_win = apply_window(segment)
        seg_norm = normalize_volume(seg_win)

        specs = {
            "clean":  create_spectrogram(seg_norm),
            "noisy":  create_spectrogram(create_noisy_segment(seg_norm)),
            "reverb": create_spectrogram(create_reverb_segment(seg_norm))
        }

        for tag, spec in specs.items():
            arr = spec.cpu().numpy()
            path = os.path.join(folder, f"part{idx}_{tag}.npy")
            np.save(path, arr)
    except Exception:
        logger.exception("Error processing segment %d", idx)


def process_audio(
    song_name: str,
    audio_path: str,
    segment_length: float = 5.0,
    overlap: float = 0.5
) -> str:
    """
    Splits into overlapping 5 s chunks, processes each in parallel,
    and writes .npy files under SPECTROGRAM_DIR/<song_name>.spectrograms/.
    """
    target_folder = os.path.join(SPECTROGRAM_DIR, f"{song_name}.spectrograms")
    os.makedirs(target_folder, exist_ok=True)

    waveform = load_audio(audio_path)
    total = waveform.shape[0]
    seg_samples = int(segment_length * SAMPLE_RATE)
    hop = int(seg_samples * (1 - overlap))

    tasks: List[Tuple[np.ndarray, int, str]] = []
    idx = 1
    for start in range(0, total, hop):
        end = min(start + seg_samples, total)
        if (end - start) < seg_samples // 2:
            continue
        chunk = waveform[start:end]
        if chunk.shape[0] < seg_samples:
            pad = seg_samples - chunk.shape[0]
            chunk = torch.nn.functional.pad(chunk, (0, pad))
        tasks.append((chunk.numpy(), idx, target_folder))
        idx += 1

    with ProcessPoolExecutor(max_workers=MAX_PROCESSES) as executor:
        executor.map(process_song_segment, tasks)

    return target_folder

def prepare_audio(pcm: np.ndarray) -> np.ndarray:
    """
    Convert a mono PCM NumPy array (values in [-1,1]) into
    a single “clean” mel‑spectrogram array of shape (N_MELS, T).
    This matches exactly the spectrogram you saved during training.
    """
    # 1) Convert to tensor
    audio = torch.from_numpy(pcm).float()

    # 2) Apply the same windowing & normalization you use in training
    audio = apply_window(audio)
    audio = normalize_volume(audio)

    # 3) Generate mel→dB spectrogram, clamp & remove NaNs
    spec = create_spectrogram(audio)

    # 4) Return as NumPy array
    return spec.cpu().numpy()