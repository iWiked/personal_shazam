import sys
import wave
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Direct execution starts Python's import search in scripts/, not the project root.
if __package__ in (None, ""):
    sys.path.insert(0, str(PROJECT_ROOT))

from wav.WavClass import SilentAudioError, WavConv

TEST_WAV_FORMAT_PATH = PROJECT_ROOT / "test_songs" / "known_songs" / "despeinada.wav"
DEFAULT_WAV_FORMAT_PATH = (
    PROJECT_ROOT / "test_songs" / "known_songs" / "K08_Bad_Bunny_Jhay_Cortez_Dakiti.wav"
)


def test_conversion() -> None:
    converter = WavConv()
    for path in (TEST_WAV_FORMAT_PATH, DEFAULT_WAV_FORMAT_PATH):
        with wave.open(str(path), "rb") as audio:
            original_duration = audio.getnframes() / audio.getframerate()

        samples, sample_rate = converter.wav_to_samples(str(path))
        assert sample_rate == 44100
        assert samples.ndim == 1 and samples.size > 0
        assert abs(samples.size / sample_rate - original_duration) <= (
            1 / sample_rate + 1e-9
        )
        print(f"PASS: {path.name} -> {samples.size} mono samples at {sample_rate} Hz")

    silence = PROJECT_ROOT / "test_songs" / "known_songs" / "S01_Silence_10_seconds.wav"
    try:
        converter.wav_to_samples(str(silence))
    except SilentAudioError:
        print("PASS: silence rejected")
    else:
        raise AssertionError("Expected SilentAudioError for the silence WAV")


if __name__ == "__main__":
    test_conversion()
