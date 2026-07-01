<!--
Enable Raptor mini (Preview) for all clients
-->

# Copilot instructions (repo-specific)

Purpose: help an AI coding assistant be immediately productive in this repository. Keep answers short and action-oriented; prefer concrete edits and commands.

## High-level architecture
- This repo automates sermon transcription: discover video IDs -> download audio -> transcribe with whisper.cpp -> generate HTML transcripts in `docs/`.
- Key scripts: `src/berean_transcripts/get_new_video_ids.py`, `src/berean_transcripts/transcribe_youtube.py`, `src/berean_transcripts/generate_html.py`, `bash_transcribe_new_videos.sh`, `bash_transcribe.sh`.
- Data locations: `data/` (ids, transcripts, `video_details_cache.json`), `docs/` (generated HTML), `whisper.cpp/` (local build of whisper C++).

## Developer workflows & commands (explicit)
- Setup: create venv and install
  - `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && pip install -e .`
- Build whisper.cpp: clone and `make -j` in `whisper.cpp/` (binary expected at `whisper.cpp/main`).
- Common tasks:
  - Transcribe queue: `make transcribe_new` (runs `bash_transcribe_new_videos.sh`)
  - Generate HTML: `make html` or `python3 src/berean_transcripts/generate_html.py --file data/bcc_live_video_ids_done.txt`
  - Update whisper.cpp: `make update_whispercpp`
  - Tests: `pytest` (tests live at `tests/` and `backend/tests/`)
  - Format & lint: `black src/` and `ruff check src/` (configured in `pyproject.toml`)

## Project-specific conventions & gotchas
- Uses `git-lfs` for big cache files (notably `data/video_details_cache.json`). Remember to run `git lfs pull` when syncing.
- FFmpeg path is often hardcoded to `/opt/homebrew/bin/ffmpeg` in scripts (`transcribe_youtube.py`, bash scripts). Use that when testing on macOS unless configured otherwise.
- Whisper is invoked through the local `whisper.cpp` binary and expects models in `models/` (default model name in code: `ggml-large-v3-turbo.bin`). If you change invocation flags, update `src/berean_transcripts/transcribe_youtube.py`.
- Automation scripts (`bash_transcribe_new_videos.sh`) assume an SSH key is available and will `git add`, `git commit`, and `git push` — **do not run in CI without review**.

## Testing and review guidance
- Run `pytest` before opening PRs; unit tests mock external dependencies (see `tests/test_utils.py`).
- When changing transcription behavior, add tests that assert `extract_video_id`, and integration checks for generated HTML under `docs/`.

## Examples (copyable)
```
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .

# Transcribe new videos locally (non-destructive):
make transcribe_new

# Run unit tests
pytest
```

## Preferred model and agent note
- Preferred model when available: **Raptor mini (Preview)** — use it for concise coding edits and repository understanding. If not available, fall back to the default model.

## Useful files to reference when making changes
- `README.md`, `CLAUDE.md` (contains detailed developer commands)
- `Makefile` (available targets: `install`, `html`, `transcribe_new`, `update_whispercpp`)
- `src/berean_transcripts/*` (core logic)
- `bash_transcribe_new_videos.sh`, `bash_transcribe.sh` (automation and push behavior)

---
If anything here is unclear or you want a different level of detail (e.g., more examples of tests or common PR checks), tell me what to expand. 
