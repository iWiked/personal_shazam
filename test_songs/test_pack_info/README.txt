SONG RECOGNITION TEST PACK

CONTENTS
known/: 4 full songs to add to your fingerprint database.
unknown/: 5 full songs to keep OUT of the database.
silence/: 1 valid 10-second WAV containing exactly zero-valued samples.

All audio is 44,100 Hz, mono, 16-bit PCM WAV. Music was decoded from the
artist's published MP3 files; it is not an original lossless master.

YOUR EXISTING SONG
Add your own Despeinada file to the known collection. This package provides
FOUR ADDITIONAL known songs, making five known songs including Despeinada.
Despeinada is not supplied in this archive.

HOW TO TEST
1. Index only the four songs inside known/ plus your own Despeinada file.
2. Keep unknown/ and silence/ out of database imports. Do not recursively
   import this entire package.
3. Start by querying a known full song to check the basic workflow.
4. Then test 5-, 10-, and 15-second excerpts from different positions in
   known songs. They should match their corresponding indexed recordings.
5. Query excerpts from each unknown song. The desired result is no confident
   match. Unknown means absent from YOUR catalog, not obscure or unnamed.
6. Query the silence WAV. It should be identified as silence or rejected
   without a song match, a crash, or a division-by-zero error.
7. Finally, play known songs through a speaker and record short queries
   with your microphone to evaluate real-world performance.

ABOUT THE SILENCE FILE
This is a playable WAV with an audio stream containing digital silence.
It is not a zero-byte file or a video without an audio stream; those are
separate invalid-input/missing-stream tests.

LIMITATIONS
This small starter collection uses instrumental music by one composer.
It is useful for basic matching and rejection checks, but does not establish
accuracy across a large catalog, varied vocals, remixes, or noisy conditions.
The files were checked for format, duration, nonempty music, and exact
silence. Your recognizer has not been run on them, so outcomes are targets.

SOURCES AND CREDITS
All nine music tracks are by Kevin MacLeod (incompetech.com), distributed
under Creative Commons Attribution 4.0. See ATTRIBUTION.txt and manifest.json
for credits, source links, conversion details, and SHA-256 checksums.
Keep the attribution information with any redistributed package or demo.
