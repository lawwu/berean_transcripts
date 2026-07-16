import re
from collections import Counter
from typing import Optional


TIMESTAMP_LINE_RE = re.compile(r"^\[[^\]]+ --> [^\]]+\]\s*(.*)$")
WORD_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?")

MIN_TRANSCRIPT_WORDS = 50
MIN_REPEAT_COUNT = 20
MAX_DOMINANT_SEGMENT_RATIO = 0.55


def _segment_texts(transcript: str):
    segments = []
    for line in transcript.splitlines():
        match = TIMESTAMP_LINE_RE.match(line.strip())
        text = match.group(1) if match else line
        text = text.strip()
        if text:
            segments.append(text)
    return segments


def _normalize(text: str) -> str:
    return " ".join(WORD_RE.findall(text.lower().replace("’", "'")))


def collapse_consecutive_repeats(
    transcript: str, max_consecutive: int = 2
) -> str:
    """Collapse decoder loops while leaving timestamps and real text intact."""
    output_lines = []
    previous = None
    repeat_count = 0
    for line in transcript.splitlines():
        match = TIMESTAMP_LINE_RE.match(line.strip())
        segment = match.group(1) if match else line
        normalized = _normalize(segment)
        if normalized and normalized == previous:
            repeat_count += 1
        else:
            previous = normalized
            repeat_count = 1
        if not normalized or repeat_count <= max_consecutive:
            output_lines.append(line)
    return "\n".join(output_lines) + ("\n" if output_lines else "")


def find_transcript_issue(transcript: str) -> Optional[str]:
    """Return a publish-blocking quality issue, or None for plausible output."""
    segments = _segment_texts(transcript)
    word_count = sum(len(WORD_RE.findall(segment)) for segment in segments)
    if word_count < MIN_TRANSCRIPT_WORDS:
        return f"only {word_count} words were transcribed"

    normalized = [text for text in map(_normalize, segments) if text]
    if not normalized:
        return "no spoken text was transcribed"

    dominant_text, dominant_count = Counter(normalized).most_common(1)[0]
    dominant_ratio = dominant_count / len(normalized)
    if (
        dominant_count >= MIN_REPEAT_COUNT
        and dominant_ratio >= MAX_DOMINANT_SEGMENT_RATIO
    ):
        return (
            f"{dominant_ratio:.0%} of segments repeat "
            f"{dominant_text!r} ({dominant_count} times)"
        )

    return None
