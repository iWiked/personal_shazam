# Personal Shazam

A work-in-progress Python song recognition project using WAV audio, NumPy, SciPy, and SQLite.

Currently includes audio preparation, song metadata imports, and overlapping audio chunks with Hann windowing and FFT calculations. Fingerprinting and song matching are still in progress.

## Setup

Use Python 3.11 or newer. From the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

On Windows, use `python` instead of `python3` to create the environment, then activate it with `.\.venv\Scripts\Activate.ps1` in PowerShell.

## Local audio

Put your own WAV files in `test_songs/known_songs/` and `test_songs/unknown_songs/`. The converter supports 16-bit PCM mono or stereo WAV audio and prepares it at 44,100 Hz in mono.

```bash
python scripts/add_songs.py
python scripts/test_spectrogram.py
python scripts/test_universal_wav_conv.py
```

The spectrogram test expects `test_songs/known_songs/K05_XXXTENTACION_Moonlight.wav`. The conversion test expects `despeinada.wav`, `K08_Bad_Bunny_Jhay_Cortez_Dakiti.wav`, and `S01_Silence_10_seconds.wav` in the same folder. Supply those files locally to run those tests.

Audio files, archives, the generated database, and virtual environments are excluded from Git. The original test pack credits and metadata are in `test_songs/test_pack_info/`.

## Paths

Paths are based on the source files' locations, so you can clone or move the project without editing usernames or home directories. Scripts also work when called by their full path from a different working directory; activate the environment or use its Python executable.

- The database is created at `db/database.db`.
- `WavConv.wav_to_samples()` accepts absolute paths or paths relative to the project folder, such as `test_songs/known_songs/example.wav`.
- `add_song()` accepts an absolute path inside `test_songs`, a path such as `known_songs/example.wav`, or a project-relative path beginning with `test_songs/`.
- Database song paths are stored relative to the project folder with forward slashes. Resolve them against the project folder before opening them. Reimporting an existing song updates its stored path without duplicating it.
