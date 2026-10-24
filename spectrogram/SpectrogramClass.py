import numpy as np
from scipy.signal.windows import hann

WINDOW_SIZE: int = 4096
HOP_SIZE: int = 2048


class Spectrogram:
    def __init__(self, samples: np.ndarray, sample_rate: int):
        self.samples: np.ndarray = samples
        self.sample_rate: int = sample_rate
        self.WINDOW_SIZE: int = WINDOW_SIZE
        self.HOP_SIZE: int = HOP_SIZE
        self.chunks: list[np.ndarray] = []
        self.final_array: list[list] = [[]]

    def get_chunks(self) -> None:
        # starts at 0 goes until length - WINDOW_SIZE + 1 (to include the last window possible) steps by HOP_SIZE
        for start in range(0, len(self.samples) - self.WINDOW_SIZE + 1, self.HOP_SIZE):
            # each chunk is an array of signed floats that show the amplitude at one instant
            # the values are measured relative to 0
            chunk = self.samples[start : start + self.WINDOW_SIZE]

            # The hann window is an array of weights between 0 and 1 the same length as each chunk
            window = hann(M=self.WINDOW_SIZE, sym=False)
            # We multiply the window to our chunk to reduce samples near the edges but keep the middle
            # in the future this somehow reduced artificial frequency leakage when applying FFT
            windowed_chunk = chunk * window

            # we use rfft as we have real input and skips redundant netavie frequencies
            spectrum = np.fft.rfft(windowed_chunk)
            print(spectrum)
            # we take the abs value to find the magnitudes in order to measure the strength of each frequency
            magnitudes = np.abs(spectrum)
            print(magnitudes)

            self.chunks.append(windowed_chunk)

        return None
