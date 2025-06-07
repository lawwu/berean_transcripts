import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import types
sys.modules.setdefault("yt_dlp", types.ModuleType("yt_dlp"))
sys.modules.setdefault("ffmpeg", types.ModuleType("ffmpeg"))
sys.modules["yt_dlp"].YoutubeDL = object
sys.modules["ffmpeg"].input = lambda *args, **kwargs: None
import pytest

from berean_transcripts.transcribe_youtube import extract_video_id


def test_extract_video_id_youtube():
    url = "https://www.youtube.com/watch?v=abcd1234EFG"
    assert extract_video_id(url) == "abcd1234EFG"


def test_extract_video_id_vimeo():
    url = "https://vimeo.com/123456789"
    assert extract_video_id(url) == "123456789"


def test_extract_video_id_unknown():
    url = "https://example.com/video"
    assert extract_video_id(url) == "unknown_id"

