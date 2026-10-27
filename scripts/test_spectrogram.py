import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(PROJECT_ROOT))

from spectrogram.SpectrogramClass import Spectrogram
from wav.WavClass import WavConv

MOONLIGHT_PATH = (
    PROJECT_ROOT / "test_songs" / "known_songs" / "K05_XXXTENTACION_Moonlight.wav"
)
DESPACITO_PATH = (
    PROJECT_ROOT
    / "test_songs"
    / "known_songs"
    / "K06_Luis_Fonsi_Daddy_Yankee_Despacito.wav"
)

paths: list[Path] = [MOONLIGHT_PATH, DESPACITO_PATH]
song_names: list[str] = ["Moonlight", "Despacito"]


def _check_spectrogram(path: Path, song_name: str) -> None:
    samples, sample_rate = WavConv().wav_to_samples(str(path))
    spectrogram = Spectrogram(samples, sample_rate)
    spectro = spectrogram.create_spectrogram()

    assert spectrogram.chunks, "No chunks were created."
    first_chunk = spectrogram.chunks[0]
    assert isinstance(first_chunk, np.ndarray), (
        "Chunks must be audio arrays, not start indices."
    )
    assert first_chunk.shape == (spectrogram.WINDOW_SIZE,), "Unexpected chunk size."

    # Each complete time chunk should have one row of nonnegative frequency magnitudes.
    expected_chunks = (
        1 + (len(samples) - spectrogram.WINDOW_SIZE) // spectrogram.HOP_SIZE
    )
    expected_bins = spectrogram.WINDOW_SIZE // 2 + 1
    assert isinstance(spectro, np.ndarray), "Spectrogram must be a NumPy array."
    assert spectro.shape == (expected_chunks, expected_bins), (
        f"Unexpected spectrogram shape: {spectro.shape}"
    )
    assert len(spectrogram.chunks) == expected_chunks, "Unexpected chunk count."
    assert np.isfinite(spectro).all(), "Spectrogram contains NaN or infinity."
    assert (spectro >= 0).all(), "Magnitudes must not be negative."
    print(
        f"PASS: {song_name} spectrogram shape {spectro.shape} (chunks, frequency bins)."
    )

    spectrogram.get_peaks(spectro)

    # spectrogram.visualize_spectrogram(spectro)


def test_spectrogram() -> None:
    _check_spectrogram(MOONLIGHT_PATH, "Moonlight")


def test_multi_spectrogram() -> None:
    for path, song_name in zip(paths, song_names):
        _check_spectrogram(path, song_name)


if __name__ == "__main__":
    test_spectrogram()
    # test_multi_spectrogram()
