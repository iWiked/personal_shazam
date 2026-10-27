"""Test peak selection; add --plot to view Moonlight with its selected peaks."""

import argparse
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(PROJECT_ROOT))

from spectrogram.SpectrogramClass import Peak, PeakList, Spectrogram
from wav.WavClass import WavConv

MOONLIGHT_PATH = (
    PROJECT_ROOT / "test_songs" / "known_songs" / "K05_XXXTENTACION_Moonlight.wav"
)


def test_peak_list() -> None:
    peaks = PeakList()
    peaks.add_peak(Peak(0.0, 100.0, 10.0))
    peaks.add_peak([Peak(0.0, 200.0, value) for value in (8.0, 3.0, 2.0, 1.0, 0.5)])
    assert peaks.peak_size == 6 and peaks.total == 24.5
    assert peaks.average is not None
    assert np.isclose(peaks.average, 24.5 / 6)
    assert [peak.magnitude for peak in peaks.get_candidates().peak_list] == [10.0, 8.0]
    assert peaks.get_candidates(1).peak_size == 1
    peaks.clear_peaks()
    assert peaks.peak_size == 0 and peaks.total == 0 and peaks.average is None
    print("PASS: PeakList additions, average, filtering, and clearing.")


def test_peak_selection() -> None:
    analysis = Spectrogram(np.zeros(4096), 44100)
    # Known band strengths in three time chunks, followed by a silent chunk.
    spectro = np.zeros((4, 2049))
    for row, strengths in enumerate(
        ((10, 8, 3, 2, 1, 0.5), (2, 4, 6, 8, 10, 12), (12, 10, 8, 6, 4, 2))
    ):
        for (start_bin, _), magnitude in zip(analysis.BANDS, strengths):
            spectro[row, start_bin + 2] = magnitude

    # Hide the class's per-band debug prints so the test results stay readable.
    with redirect_stdout(StringIO()):
        peaks = analysis.get_peaks(spectro)

    # Each row has its own average; the silent fourth row should contribute nothing.
    expected = [
        (0, 2, 10), (0, 12, 8),
        (1, 42, 8), (1, 82, 10), (1, 162, 12),
        (2, 2, 12), (2, 12, 10), (2, 22, 8),
    ]
    assert isinstance(peaks, PeakList) and peaks.peak_size == len(expected)
    for peak, (row, frequency_bin, magnitude) in zip(peaks.peak_list, expected):
        assert np.isclose(peak.time, row * 2048 / 44100)
        assert np.isclose(peak.frequency, frequency_bin * 44100 / 4096)
        assert peak.magnitude == magnitude

    # Check that plotted dots land on the expected chunk/bin coordinates.
    analysis.visualize_peaks(spectro, peaks, show=False)
    figure = plt.gcf()
    dots = np.asarray(
        figure.axes[0].collections[0].get_offsets(), dtype=np.float64
    )
    np.testing.assert_allclose(
        dots, [(row, frequency_bin) for row, frequency_bin, _ in expected]
    )
    plt.close(figure)
    print("PASS: per-chunk filtering, timestamps, frequencies, silence, and peak overlay.")


def test_moonlight_peaks(plot: bool = False, save: Path | None = None) -> None:
    samples, sample_rate = WavConv().wav_to_samples(str(MOONLIGHT_PATH))
    analysis = Spectrogram(samples, sample_rate)
    spectro = analysis.create_spectrogram()
    with redirect_stdout(StringIO()):
        peaks = analysis.get_peaks(spectro)

    assert isinstance(peaks, PeakList) and peaks.peak_size > 0
    assert peaks.peak_size == len(peaks.peak_list)
    for peak in peaks.peak_list:
        row = round(peak.time * sample_rate / analysis.HOP_SIZE)
        frequency_bin = round(peak.frequency * analysis.WINDOW_SIZE / sample_rate)
        assert 0 <= row < len(spectro)
        assert 0 <= frequency_bin < analysis.BANDS[-1][1]
        assert np.isfinite(peak.magnitude) and peak.magnitude > 0
        assert np.isclose(peak.magnitude, spectro[row, frequency_bin])
    print(f"PASS: Moonlight produced {peaks.peak_size} retained peaks from {len(spectro)} chunks.")

    if plot or save is not None:
        analysis.visualize_peaks(spectro, peaks, show=False)
        figure = plt.gcf()
        figure.axes[0].set_title("Moonlight: selected peaks")
        if save is not None:
            save = save.expanduser().resolve()
            save.parent.mkdir(parents=True, exist_ok=True)
            figure.savefig(save, dpi=150, bbox_inches="tight")
            print(f"Saved plot: {save}")
        if plot:
            plt.show()
        plt.close(figure)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plot", action="store_true", help="Show Moonlight's peak overlay.")
    parser.add_argument("--save", type=Path, help="Save Moonlight's peak overlay to an image.")
    args = parser.parse_args()
    if not args.plot:
        plt.switch_backend("Agg")
    test_peak_list()
    test_peak_selection()
    test_moonlight_peaks(plot=args.plot, save=args.save)
