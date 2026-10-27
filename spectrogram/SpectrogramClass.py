from typing import Any, Optional

import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import NDArray
from scipy.signal.windows import hann

WINDOW_SIZE: int = 4096
HOP_SIZE: int = 2048


BANDS = [
    (0, 10),
    (10, 20),
    (20, 40),
    (40, 80),
    (80, 160),
    (160, 512),
]


class Peak:
    def __init__(self, time: float, frequency: float, magnitude: float):
        self.time = time
        self.frequency = frequency
        self.magnitude = magnitude


class PeakList:
    def __init__(self, peak_list: Optional[list[Peak]] = None):
        # Start empty when no list is provided; copy a supplied list.
        self.peak_list: list[Peak] = list(peak_list) if peak_list is not None else []
        self.peak_size: int = len(self.peak_list)
        self.total: float = sum(peak.magnitude for peak in self.peak_list)
        # An empty list has no average yet.
        self.average: Optional[float] = (
            self.average_magnitude() if self.peak_size else None
        )

    def add_peak(self, peaks: Peak | list[Peak]) -> None:
        # Treat a single peak as a one-item list.
        new_peaks = [peaks] if isinstance(peaks, Peak) else list(peaks)

        # Add all the new peaks and update the running totals.
        self.peak_list.extend(new_peaks)
        self.peak_size += len(new_peaks)
        self.total += sum(peak.magnitude for peak in new_peaks)

        # An empty list still has no average.
        self.average = self.total / self.peak_size if self.peak_size else None

    def remove_peak(self, peaks: Peak | list[Peak]) -> None:
        # Treat a single peak as a one-item list.
        removed_peaks = [peaks] if isinstance(peaks, Peak) else list(peaks)

        # Validate all removals on a copy so a missing peak cannot leave this
        # object only partially updated.
        remaining_peaks = self.peak_list.copy()
        for peak in removed_peaks:
            try:
                remaining_peaks.remove(peak)
            except ValueError:
                raise ValueError(
                    "Cannot remove a peak that is not in the list"
                ) from None

        # Preserve the public list object while restoring all derived values.
        self.peak_list[:] = remaining_peaks
        self.peak_size = len(self.peak_list)
        self.total = sum(peak.magnitude for peak in self.peak_list)

        # An empty list still has no average.
        self.average = self.total / self.peak_size if self.peak_size else None

    def get_candidates(self, amount: Optional[int] = None) -> "PeakList":
        candidates: PeakList = PeakList()

        if amount is not None and amount <= 0:
            raise ValueError("Amount must be greater than 0")

        if self.average is None:
            raise ValueError("Peak list must have at least 1 value")

        for peak in self.peak_list:
            if self.average and peak.magnitude > self.average:
                candidates.add_peak(peak)

        if amount:
            return PeakList(candidates.peak_list[:amount])

        return candidates

    def average_magnitude(self) -> float:
        if not self.peak_list:
            raise ValueError("Cannot average an empty peak list")

        return self.total / self.peak_size

    def clear_peaks(self) -> None:
        self.peak_list.clear()
        self.peak_size = 0
        self.total = 0
        self.average = None

        return None


class Spectrogram:
    def __init__(self, samples: np.ndarray, sample_rate: int):
        self.samples: np.ndarray = samples
        self.sample_rate: int = sample_rate
        self.WINDOW_SIZE: int = WINDOW_SIZE
        self.HOP_SIZE: int = HOP_SIZE
        self.BANDS: list[tuple[int, int]] = BANDS
        self.chunks: list[np.ndarray] = []
        self.final_array: list[np.ndarray] = []
        # a 2D array of frquency magnitueds
        # created of arrays of time chunks[arrays of magnitude strength]
        self.spectrogram: NDArray[Any]

    def create_spectrogram(self) -> NDArray[Any]:
        """Build a magnitude spectrogram from overlapping audio chunks.

        Apply a Hann window to each complete WINDOW_SIZE-sample chunk,
        moving forward by HOP_SIZE samples each time. Store the windowed
        chunks in self.chunks and their FFT magnitudes in self.final_array.

        Store the combined magnitudes in self.spectrogram, with one row per
        chunk and one column per frequency bin. Skip incomplete trailing
        chunks. If no complete chunk fits, store an empty 1D array instead.
        Replace the previous results each time this method is called.

        Returns:
            None. The results are stored on this instance.
        """
        # to prevent duplication if called on the same object we clear the arrays
        self.chunks.clear()
        self.final_array.clear()

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

            # conv each chunk from amplitude over time into frequency components which show which frequencies are present
            # Ex. a chunk containing a 440Hz tone looks like a waveform, but after rfft and taking the abs value
            # it reveals a strong peak near 440Hz
            # we use rfft as we have real input and skips redundant netavie frequencies
            spectrum = np.fft.rfft(windowed_chunk)
            # we take the abs value to find the magnitudes in order to measure the strength of each frequency
            magnitudes = np.abs(spectrum)
            self.chunks.append(windowed_chunk)

            self.final_array.append(magnitudes)

        # Combine the magnitude arrays into one NumPy array: each row is a time chunk,
        # and each column is a frequency bin whose value shows its strength in that chunk.
        self.spectrogram = np.array(self.final_array)
        return self.spectrogram

    def visualize_spectrogram(self, spectrogram: NDArray[Any]) -> None:
        # convert magnitudes to decibels so quieter details are easier to see
        db = 20 * np.log10(np.maximum(spectrogram, 1e-10))

        # .T swaps rows and columns so time runs horizontally and frequency runs vertically. Brighter colors indicate stronger frequencies
        plt.imshow(
            db.T,
            origin="lower",
            aspect="auto",
            cmap="magma",
            # reveal more detail by narrowing color range
            vmin=db.max() - 80,
            vmax=db.max(),
        )
        plt.xlabel("Time (Chunk Number)")
        plt.ylabel("Frequency (Bin Number)")
        plt.colorbar(label="Magnitude (dB)")

        plt.show()

        return None

    def visualize_peaks(
        self,
        spectrogram: NDArray[Any],
        peaks: PeakList,
        *,
        show: bool = True,
    ) -> None:
        """Draw selected peaks as cyan dots over the magnitude spectrogram.

        Convert peak times and frequencies back to chunk and bin numbers
        so the dots line up with the existing graph. Set show=False when
        saving or testing the plot without opening a window.
        """
        if spectrogram.ndim != 2 or spectrogram.size == 0:
            raise ValueError("A nonempty 2D spectrogram is required to plot peaks")

        db = 20 * np.log10(np.maximum(spectrogram, 1e-10))
        figure, axes = plt.subplots(figsize=(12, 5))
        image = axes.imshow(
            db.T,
            origin="lower",
            aspect="auto",
            cmap="magma",
            vmin=db.max() - 80,
            vmax=db.max(),
        )

        # The graph uses chunk and bin numbers, while Peak stores seconds and Hz.
        chunk_positions = [
            peak.time * self.sample_rate / self.HOP_SIZE for peak in peaks.peak_list
        ]
        bin_positions = [
            peak.frequency * self.WINDOW_SIZE / self.sample_rate
            for peak in peaks.peak_list
        ]
        axes.scatter(
            chunk_positions,
            bin_positions,
            s=6,
            color="cyan",
            marker=".",
            label="Selected peaks",
        )
        axes.set_xlabel("Time (Chunk Number)")
        axes.set_ylabel("Frequency (Bin Number)")
        axes.legend(loc="upper right")
        figure.colorbar(image, ax=axes, label="Magnitude (dB)")
        figure.tight_layout()

        if show:
            plt.show()

        return None

    def get_peaks(self, spectrogram: NDArray[Any]):
        # For now, inspect only the first two short moments of the song.
        # Each row contains the frequency strengths for one moment.

        final_peaks: PeakList = PeakList()

        for chunk_idx, chunk in enumerate(spectrogram):
            # when this chunk starts in the song
            time_seconds: float = chunk_idx * self.HOP_SIZE / self.sample_rate

            potential_peaks: PeakList = PeakList()

            # look at each frequency group, from low to high.
            for start_bin, end_bin in self.BANDS:
                # take the magnitudes in this group; end_bin is not included.
                band = chunk[start_bin:end_bin]

                # argmax gives the strongest magnitudes position within this band
                # Add start_bin to get its position in the whole chunk.
                peak_bin: int = start_bin + int(np.argmax(band))
                # Read how strong that frequency is.
                peak_magnitude = chunk[peak_bin]
                # Convert its bin number into a frequency in Hz.
                frequency_hz = peak_bin * self.sample_rate / self.WINDOW_SIZE

                # print one candidate per group; weak candidates are not filtered yet.
                # calculated time is not printed or stored yet.

                peak: Peak = Peak(time_seconds, frequency_hz, peak_magnitude)
                potential_peaks.add_peak(peak)

            candidates: PeakList = potential_peaks.get_candidates()
            final_peaks.add_peak((candidates.peak_list))

        return final_peaks

    def create_fingerprint(self, final_peaks: PeakList, anchor_partners: int = 5):
        print(f"Final Peak size: {final_peaks.peak_size}")
        peak_list = final_peaks.peak_list

        if anchor_partners <= 1:
            raise ValueError(f"Anchor partners must be greater than 1")

        if anchor_partners > final_peaks.peak_size:
            raise ValueError(f"Anchor partner amount is greater than peaks in song")

        if anchor_partners > final_peaks.peak_size // 3:
            raise ValueError(
                f"Anchor partner amount must be smaller than {final_peaks.peak_size // 4}"
            )

        window: PeakList = PeakList()
        stored_fingerprints: dict[int, PeakList] = {}

        for i in range(anchor_partners):
            # initialize starting window
            window.add_peak(peak_list[i])

        stored_fingerprints[0] = PeakList(window.peak_list)

        left = 0
        for right in range(anchor_partners, final_peaks.peak_size):
            window.add_peak(peak_list[right])
            window.remove_peak(peak_list[left])

            left += 1
            stored_fingerprints[left] = PeakList(window.peak_list)

        return stored_fingerprints
