# Read WAV headers and the audio bytes stored in the file.
import wave
from pathlib import Path

# Store and process audio samples as arrays.
import numpy as np

# Change the sample rate using filtering and interpolation.
from scipy.signal import resample_poly

# Every converted recording will use 44,100 samples per second.
FINAL_SAMPLE_RATE: int = 44100
# Reject audio whose normalized RMS signal level is below this value.
SILENCE_THRESHHOLD: float = 0.001
# Min duration length
MIN_SONG_DURATION_SECONDS: int = 3


# Separate error types let callers handle each audio problem differently.
class TruncatedAudioError(ValueError):
    """Wav contains fewer audio bytes than its header declares"""


class TooShortAudioError(ValueError):
    pass


class SilentAudioError(ValueError):
    pass


class WavConv:
    def __init__(self) -> None:
        # Keep the conversion settings on this converter instance.
        self.FINAL_SAMPLE_RATE: int = FINAL_SAMPLE_RATE
        self.SILENCE_THRESHHOLD: float = SILENCE_THRESHHOLD
        self.MIN_SONG_DURATION_SECONDS: int = MIN_SONG_DURATION_SECONDS

    def conversion_checks(self, audio: wave.Wave_read) -> np.ndarray:
        """Read, validate, downmix, and scale the WAV samples."""
        # Read the audio payload once; the WAV header is not included.
        raw_audio: bytes = audio.readframes(audio.getnframes())
        channels: int = audio.getnchannels()

        # Expected bytes = frames x channels x bytes per channel sample.
        expected_bytes: int = audio.getnframes() * channels * audio.getsampwidth()

        if expected_bytes != len(raw_audio):
            raise TruncatedAudioError(
                f"Expected {expected_bytes} audio bytes, but got {len(raw_audio)}"
            )

        # Frames divided by frames per second gives duration for mono or stereo.
        duration_seconds: float = audio.getnframes() / audio.getframerate()
        if duration_seconds < self.MIN_SONG_DURATION_SECONDS:
            raise TooShortAudioError(
                f"Audio must be at least 3 seconds, got: {duration_seconds:.2f}"
            )

        # "<i2" reads each pair of bytes as a little-endian signed 16-bit integer.
        # Convert to floats so averaging and scaling can produce decimal values.
        samples = np.frombuffer(raw_audio, dtype="<i2").astype(np.float32)
        if channels == 2:
            # Group each left/right pair into a row, then average it into mono.
            samples = samples.reshape(-1, channels).mean(axis=1)

        # Scale -32768..32767 to -1.0..just below 1.0; this changes amplitude units,
        # not the sample rate or playback speed.
        samples /= 32768.0

        # RMS measures signal strength without positive/negative values cancelling.
        # Use float64 for a more precise average, then reject silence/very quiet audio.
        rms = np.sqrt(np.mean(samples**2, dtype=np.float64))
        if rms < self.SILENCE_THRESHHOLD:
            raise SilentAudioError("Audio is silent or too quiet")

        # Reuse these prepared samples instead of reading the file again.
        return samples

    def wav_to_samples(
        self,
        file_path: str,
    ) -> tuple[np.ndarray, int]:
        """Read a 16-bit PCM WAV file and prepare mono waveform samples.

        Args:
            file_path: Absolute or project-relative path to a local 16-bit PCM WAV file.

        Returns:
            A tuple (final_samples, sample_rate), where:
                final_samples: A one-dimensional floating-point NumPy array,
                    resampled to self.FINAL_SAMPLE_RATE Hz and divided by
                    32768.0 to scale the original 16-bit amplitudes.
                sample_rate: The output sample rate, self.FINAL_SAMPLE_RATE Hz.

        """
        # Resolve relative audio paths from the project folder, regardless of the terminal's directory.
        audio_path = Path(file_path).expanduser()
        if not audio_path.is_absolute():
            audio_path = Path(__file__).resolve().parents[1] / audio_path

        # Open in read-binary mode; "with" closes the file even if an error occurs.
        # str() also allows file_path to be a pathlib.Path object.
        with wave.open(str(audio_path), "rb") as audio:
            # Read the original channel count and number of samples per second.
            channels = audio.getnchannels()
            sample_rate = audio.getframerate()

            # This decoder supports 2-byte (16-bit) samples and one or two channels.
            if audio.getsampwidth() != 2 or channels not in (1, 2):
                raise ValueError("Expected 16-bit mono or stereo WAV audio.")

            # Validate the data, convert stereo to mono, and scale the amplitudes.
            samples = self.conversion_checks(audio)

            # Calculate new samples at the target rate (441.kHz) (441.kHz) (441.kHz) (441.kHz) (441.kHz) (441.kHz) (441.kHz) (441.kHz) (441.kHz) while preserving timing.
            # The resampler filters the signal to prevent aliasing.
            final_samples = resample_poly(
                samples, up=self.FINAL_SAMPLE_RATE, down=sample_rate
            )

        # Return the waveform and its output rate for correct time/frequency calculations.
        return (final_samples, self.FINAL_SAMPLE_RATE)
