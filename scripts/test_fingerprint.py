import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from spectrogram.SpectrogramClass import Spectrogram
from wav.WavClass import WavConv

MOONLIGHT_PATH = (
    PROJECT_ROOT / "test_songs" / "known_songs" / "K05_XXXTENTACION_Moonlight.wav"
)


def test_fingerprint() -> None:
    samples, sample_rate = WavConv().wav_to_samples(str(MOONLIGHT_PATH))
    spectrogram = Spectrogram(samples, sample_rate)
    # Pass only the first three chunks to peak selection.
    chunks = spectrogram.create_spectrogram()
    # chunks = spectrogram.create_spectrogram()[:9]
    peaks = spectrogram.get_peaks(chunks)
    result = spectrogram.create_fingerprint(peaks)
    print(result)
    spectrogram.visualize_peaks(spectrogram.spectrogram, peaks)


if __name__ == "__main__":
    test_fingerprint()
