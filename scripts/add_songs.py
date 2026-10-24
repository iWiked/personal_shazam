"""Import test WAVs: python3 scripts/add_songs.py or python3 -m scripts.add_songs."""

import hashlib
import json
import re
import sqlite3
import sys
import wave
from contextlib import closing
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Direct execution starts Python's import search in scripts/, not the project root.
if __package__ in (None, ""):
    sys.path.insert(0, str(PROJECT_ROOT))

from db.db_main import DB_PATH, create_db

TEST_SONGS_DIR = PROJECT_ROOT / "test_songs"


def _get_metadata(song_path: Path) -> tuple[str, str]:
    """Use the pack's credits when available; never guess an unknown artist."""
    title = re.sub(r"^[KUS]\d+_", "", song_path.stem).replace("_", " ")
    artist = "Unknown artist"
    info_dir = TEST_SONGS_DIR / "test_pack_info"

    pack_manifest = info_dir / "manifest.json"
    if pack_manifest.is_file():
        data = json.loads(pack_manifest.read_text(encoding="utf-8"))
        for entry in data["files"]:
            if Path(entry["file"]).name == song_path.name:
                return entry.get("title", title), entry.get("artist", artist)

    youtube_manifest = info_dir / "youtube_additions.json"
    if youtube_manifest.is_file():
        data = json.loads(youtube_manifest.read_text(encoding="utf-8"))
        for entry in data["tracks"]:
            if (
                entry["file"] == song_path.name
                and entry["folder"] == song_path.parent.name
            ):
                artist, separator, source_title = entry["source_title"].partition(" - ")
                if not separator:
                    return title, entry.get("uploader", "Unknown artist")
                title = source_title.split(" | ", 1)[0]
                title = re.sub(
                    r"\s*\((?:official|video oficial).*?\)",
                    "",
                    title,
                    flags=re.IGNORECASE,
                ).strip()
                parts = re.split(r"\s+ft\.\s+", title, maxsplit=1, flags=re.IGNORECASE)
                if len(parts) == 2:
                    title, featured_artist = parts
                    artist = f"{artist} feat. {featured_artist}"
                return title, artist

    return title, artist


def add_song(
    song_path: str | Path,
    *,
    title: str | None = None,
    artist: str | None = None,
) -> int:
    """Add one test WAV and return its song_id, reusing an identical recording.

    Relative paths start at test_songs, for example "known_songs/despeinada.wav".
    Project-relative paths beginning with "test_songs" are also accepted.
    The parent folder determines is_known. Explicit title/artist override metadata.
    """
    song_path = Path(song_path).expanduser()
    if not song_path.is_absolute():
        if song_path.parts and song_path.parts[0] == TEST_SONGS_DIR.name:
            song_path = PROJECT_ROOT / song_path
        else:
            song_path = TEST_SONGS_DIR / song_path
    song_path = song_path.resolve()
    relative_path = song_path.relative_to(TEST_SONGS_DIR.resolve())
    if len(relative_path.parts) < 2 or relative_path.parts[0] not in {
        "known_songs",
        "unknown_songs",
    }:
        raise ValueError(
            f"Song must be inside known_songs or unknown_songs: {song_path}"
        )
    if song_path.suffix.lower() != ".wav" or not song_path.is_file():
        raise ValueError(f"Expected an existing WAV file: {song_path}")

    # Validate the full PCM payload so damaged files do not become database rows.
    with wave.open(str(song_path), "rb") as audio:
        frames = audio.getnframes()
        if frames == 0:
            raise ValueError(f"WAV contains no audio frames: {song_path}")
        expected_bytes = frames * audio.getnchannels() * audio.getsampwidth()
        actual_bytes = 0
        while block := audio.readframes(65536):
            actual_bytes += len(block)
        if actual_bytes != expected_bytes:
            raise ValueError(f"WAV audio is truncated: {song_path}")
        duration_ms = round(frames * 1000 / audio.getframerate())

    with song_path.open("rb") as source:
        file_sha256 = hashlib.file_digest(source, "sha256").hexdigest()
    default_title, default_artist = _get_metadata(song_path)
    title = default_title if title is None else title.strip()
    artist = default_artist if artist is None else artist.strip()
    if not title or not artist:
        raise ValueError(f"Title and artist must not be blank: {song_path}")
    is_known = relative_path.parts[0] == "known_songs"
    # Store a portable path; resolve it against PROJECT_ROOT when opening the audio.
    stored_path = song_path.relative_to(PROJECT_ROOT).as_posix()

    create_db()
    with closing(sqlite3.connect(DB_PATH)) as conn, conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            """
            INSERT INTO songs (title, artist, file_path, duration_ms, file_sha256, is_known)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(file_sha256) DO NOTHING
            """,
            (title, artist, stored_path, duration_ms, file_sha256, is_known),
        )
        inserted = conn.execute("SELECT changes()").fetchone()[0] == 1
        row = conn.execute(
            "SELECT song_id, is_known FROM songs WHERE file_sha256 = ?", (file_sha256,)
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Song insert could not be confirmed: {song_path}")
        song_id, existing_is_known = row
        if bool(existing_is_known) != is_known:
            raise ValueError(
                f"Identical audio already exists in the other known/unknown group: {song_path}"
            )

        # Refresh paths on reimport, including records created before paths were portable.
        conn.execute(
            "UPDATE songs SET file_path = ? WHERE song_id = ? AND file_path != ?",
            (stored_path, song_id, stored_path),
        )

        if inserted:
            # TODO: generate fingerprints and insert them with this conn and song_id.
            # Keep unknown songs out of the reference index during recognition tests.
            pass

    status = "Added" if inserted else "Already in database"
    print(f"{status}: {song_path.name} (song_id={song_id}, is_known={is_known})")
    return song_id


def add_test_songs() -> list[int]:
    """Import every WAV beneath test_songs and return the resulting song IDs.

    Each song commits separately. Errors stop the batch and identify the failed
    file; previous imports remain committed, and rerunning safely reuses them.
    """
    if not TEST_SONGS_DIR.is_dir():
        raise FileNotFoundError(f"Test-song folder does not exist: {TEST_SONGS_DIR}")
    songs = sorted(
        path
        for path in TEST_SONGS_DIR.rglob("*")
        if path.is_file() and path.suffix.lower() == ".wav"
    )
    if not songs:
        raise ValueError(f"No WAV files found in {TEST_SONGS_DIR}")

    song_ids = []
    for song in songs:
        try:
            song_ids.append(add_song(song))
        except (
            OSError,
            ValueError,
            EOFError,
            wave.Error,
            sqlite3.Error,
            RuntimeError,
        ) as exc:
            raise RuntimeError(
                f"Failed to import {song}: {exc}. Earlier imports remain committed; rerunning is safe."
            ) from exc
    print(
        f"Processed {len(songs)} WAV files ({len(set(song_ids))} unique database songs)."
    )
    return song_ids


if __name__ == "__main__":
    add_test_songs()
