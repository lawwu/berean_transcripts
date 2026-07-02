# AGENTS.md

This file provides guidance to Claude Code, Codex and other coding agents when working with code in this repository.

## Project Overview

This is a sermon transcription system for Berean Christian Church (bereancc.com). It automatically downloads sermons from YouTube/Vimeo, transcribes them using Whisper, and generates HTML transcripts for the website.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies and package in editable mode
make install
# OR manually:
pip install -r requirements.txt
pip install -e .

# Setup git-lfs for large files
git lfs install
git lfs pull data/video_details_cache.json

# Build whisper.cpp (required for transcription)
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make clean && make -j
```

### Common Development Tasks
```bash
# Transcribe new videos from the queue
make transcribe_new
# OR: ./bash_transcribe_new_videos.sh

# Rebuild the sharded SQLite DBs that power the static search/viewer app
make db
# OR: python3 src/berean_transcripts/build_sharded_db.py

# (Legacy) Generate per-video HTML files from transcripts
make html
# OR: python3 src/berean_transcripts/generate_html.py --file data/bcc_live_video_ids_done.txt

# Update whisper.cpp to latest version
make update_whispercpp

# Run tests
pytest

# Format code (configured in pyproject.toml)
black src/
ruff check src/
```

## Architecture

### Core Components

**Data Pipeline:**
1. `get_new_video_ids.py` - Discovers new YouTube/Vimeo videos from Berean CC
2. `download_audio.py` - Downloads audio using yt-dlp
3. `transcribe_youtube.py` - Transcribes audio using whisper.cpp
4. `update_metadata_cache.py` - Fetches yt-dlp metadata (title/date/duration/url) for transcribed videos missing from `video_details_cache.json`; must run before `build_sharded_db.py` or new videos are silently skipped
5. `build_sharded_db.py` - Builds per-year SQLite DBs (with FTS5) into `docs/db/` for the static web app
6. `generate_html.py` - (Legacy) Converts transcripts to per-video HTML; existing files kept for old links
7. `get_sermon_sections.py` - Extracts sermon sections/timestamps

**Data Flow:**
- Video IDs stored in `data/bcc_live_video_ids.txt` (new videos) and `data/bcc_live_video_ids_done.txt` (processed)
- Audio files downloaded to `data/transcripts/`
- Website is a static SPA on GitHub Pages: `docs/index.html` (search) and `docs/viewer.html` (transcript view) query per-year SQLite shards in `docs/db/` client-side via sql.js; `docs/db/*.json` must stay out of git-lfs (Pages serves LFS pointers, not content — see `.gitattributes`)
- Video metadata cached in `data/video_details_cache.json`
- Legacy per-video HTML files remain in `docs/` so old links keep working

**Automation:**
- `bash_transcribe_new_videos.sh` - Main automation script
- Automatically commits and pushes results to GitHub
- Scheduled via launchd (`~/Library/LaunchAgents/com.lawrencewu.berean-transcribe.plist`) Sundays 2pm and Wednesdays 11pm local time; launchd runs missed jobs on wake, unlike cron
- Dead-man's switch: `.github/workflows/staleness-alert.yml` opens a GitHub issue if no AUTO commit lands for 10+ days

### Project Structure
```
src/berean_transcripts/     # Main Python package
data/                       # Video IDs, transcripts, cache files
docs/                       # Generated HTML transcripts
whisper.cpp/               # Whisper C++ implementation (git submodule)
bash_*.sh                  # Automation scripts
```

### Key Dependencies
- `yt-dlp` - Video/audio downloading
- `whispercpp` or `faster-whisper` - Speech transcription
- `ffmpeg-python` - Audio processing
- External: whisper.cpp binary (built locally)

### Testing
- Uses pytest framework
- Tests should be run before committing changes
- No specific test runner configured in Makefile

### Code Style
- Black formatter with 80 character line length
- Ruff linter configured
- Configuration in `pyproject.toml`

## Notes
- This system processes religious content for defensive/educational purposes
- Requires FFmpeg installed (configured for Homebrew path: `/opt/homebrew/bin/ffmpeg`)
- Uses git-lfs for large cache files
- SSH key authentication required for automated git operations