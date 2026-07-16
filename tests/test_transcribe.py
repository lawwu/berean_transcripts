from pathlib import Path

import pytest

from berean_transcripts import transcribe_youtube


def plausible_transcript():
    return "\n".join(
        f"[00:00:{index:02}.000 --> 00:00:{index:02}.900]   "
        f"Distinct sermon sentence {index} with several useful words."
        for index in range(30)
    )


def configure_paths(monkeypatch, tmp_path):
    transcripts = tmp_path / "transcripts"
    transcripts.mkdir()
    monkeypatch.setattr(transcribe_youtube, "transcripts_dir", transcripts)
    monkeypatch.setattr(transcribe_youtube, "model_dir", tmp_path / "models")
    monkeypatch.setattr(
        transcribe_youtube, "whispercpp_dir", tmp_path / "whisper.cpp"
    )
    return transcripts


def test_run_whisper_uses_no_context_and_replaces_atomically(
    monkeypatch, tmp_path
):
    transcripts = configure_paths(monkeypatch, tmp_path)
    published = transcripts / "video.txt"
    published.write_text("old transcript", encoding="utf-8")
    observed = {}

    def fake_run(command, stdout, check, text):
        observed["command"] = command
        assert check is True
        assert text is True
        stdout.write(plausible_transcript())

    monkeypatch.setattr(transcribe_youtube.subprocess, "run", fake_run)

    result = transcribe_youtube.run_whisper("video", "model.bin")

    assert result == published
    assert "-mc" in observed["command"]
    assert observed["command"][observed["command"].index("-mc") + 1] == "0"
    assert "Distinct sermon sentence" in published.read_text(encoding="utf-8")
    assert not Path(f"{published}.partial").exists()


def test_run_whisper_keeps_published_file_when_candidate_is_rejected(
    monkeypatch, tmp_path
):
    transcripts = configure_paths(monkeypatch, tmp_path)
    published = transcripts / "video.txt"
    published.write_text("old transcript", encoding="utf-8")

    def fake_run(command, stdout, check, text):
        stdout.write(
            "\n".join(
                f"[00:00:{index:02}.000 --> 00:00:{index:02}.900] Thank you."
                for index in range(40)
            )
        )

    monkeypatch.setattr(transcribe_youtube.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="Rejected transcript"):
        transcribe_youtube.run_whisper("video", "model.bin")

    assert published.read_text(encoding="utf-8") == "old transcript"
    assert Path(f"{published}.partial").exists()
