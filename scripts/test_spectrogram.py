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


def test_spectrogram() -> None:
    samples, sample_rate = WavConv().wav_to_samples(str(MOONLIGHT_PATH))
    spectrogram = Spectrogram(samples, sample_rate)
    spectrogram.get_chunks()

    assert spectrogram.chunks, "No chunks were created."
    first_chunk = spectrogram.chunks[0]
    assert isinstance(first_chunk, np.ndarray), (
        "Chunks must be audio arrays, not start indices."
    )
    assert first_chunk.shape == (spectrogram.WINDOW_SIZE,), "Unexpected chunk size."
    print(f"PASS: Moonlight produced {len(spectrogram.chunks)} chunks.")


if __name__ == "__main__":
    test_spectrogram()
