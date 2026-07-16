from berean_transcripts.quality import (
    collapse_consecutive_repeats,
    find_transcript_issue,
)


def timestamped(lines):
    return "\n".join(
        f"[00:00:{index:02}.000 --> 00:00:{index:02}.900]   {line}"
        for index, line in enumerate(lines)
    )


def test_rejects_empty_transcript():
    assert "only 0 words" in find_transcript_issue("")


def test_rejects_repetitive_hallucination():
    transcript = timestamped(["Thank you."] * 40 + ["Good morning."])
    assert "repeat 'thank you'" in find_transcript_issue(transcript)


def test_accepts_diverse_sermon_transcript():
    lines = [
        f"This is sermon sentence {index} with several distinct faithful words."
        for index in range(30)
    ]
    assert find_transcript_issue(timestamped(lines)) is None


def test_accepts_recovery_after_leading_silence():
    lines = ["Thank you."] * 20 + [
        f"Spoken announcement number {index} contains distinct useful words."
        for index in range(25)
    ]
    assert find_transcript_issue(timestamped(lines)) is None


def test_collapses_consecutive_decoder_loops():
    transcript = timestamped(
        ["Thank you."] * 10 + ["Good morning, church family."]
    )
    cleaned = collapse_consecutive_repeats(transcript)
    assert cleaned.count("Thank you.") == 2
    assert "Good morning, church family." in cleaned
