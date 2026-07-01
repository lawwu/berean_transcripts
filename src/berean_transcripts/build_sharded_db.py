import argparse
import json
import re
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


TIMESTAMP_RE = re.compile(
    r"\[\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}\]\s*"
)
BRACKET_RE = re.compile(r"\[[^\]]*\]")


def read_and_clean_whisper_file(file_path: Path) -> str:
    cleaned_text: List[str] = []
    with file_path.open("r", encoding="utf-8", errors="ignore") as file:
        for line in file:
            cleaned_line = TIMESTAMP_RE.sub("", line)
            cleaned_line = BRACKET_RE.sub("", cleaned_line)
            cleaned_text.append(cleaned_line.strip())
    return " ".join(s for s in cleaned_text if s).strip()


def group_by_year(
    metadata: Dict[str, Dict[str, object]]
) -> Dict[str, List[Tuple[str, Dict[str, object]]]]:
    grouped: Dict[str, List[Tuple[str, Dict[str, object]]]] = {}
    for video_id, info in metadata.items():
        upload_date = info.get("upload_date")
        if not upload_date or len(str(upload_date)) < 4:
            continue
        year = str(upload_date)[:4]
        grouped.setdefault(year, []).append((video_id, info))
    return grouped


def init_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=OFF;")
    conn.execute("PRAGMA synchronous=OFF;")
    conn.execute("PRAGMA temp_store=MEMORY;")
    conn.execute("PRAGMA cache_size=200000;")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS transcripts (
            id TEXT UNIQUE,
            title TEXT,
            upload_date TEXT,
            duration INTEGER,
            url TEXT,
            thumbnail TEXT,
            text TEXT
        );
        """
    )
    conn.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS transcripts_fts
        USING fts5(title, text, content='transcripts', content_rowid='rowid');
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_transcripts_date ON transcripts(upload_date);")
    return conn


def insert_transcripts(
    conn: sqlite3.Connection,
    rows: Iterable[Tuple[str, Dict[str, object]]],
    transcripts_dir: Path,
) -> int:
    count = 0
    with conn:
        for video_id, info in rows:
            transcript_path = transcripts_dir / f"{video_id}.txt"
            if not transcript_path.exists():
                continue
            text = read_and_clean_whisper_file(transcript_path)
            if not text:
                continue
            conn.execute(
                """
                INSERT INTO transcripts (id, title, upload_date, duration, url, thumbnail, text)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    video_id,
                    info.get("title"),
                    info.get("upload_date"),
                    info.get("duration"),
                    info.get("webpage_url"),
                    info.get("thumbnail"),
                    text,
                ),
            )
            conn.execute(
                "INSERT INTO transcripts_fts(rowid, title, text) VALUES (last_insert_rowid(), ?, ?);",
                (info.get("title"), text),
            )
            count += 1
    return count


def build_manifest(entries: List[Dict[str, object]], out_dir: Path) -> None:
    manifest_path = out_dir / "manifest.json"
    manifest = {
        "schema_version": 1,
        "entries": entries,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def build_id_index(
    grouped: Dict[str, List[Tuple[str, Dict[str, object]]]], out_dir: Path
) -> None:
    index: Dict[str, str] = {}
    for year, rows in grouped.items():
        for video_id, _ in rows:
            index[video_id] = year
    index_path = out_dir / "id_index.json"
    index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build sharded SQLite transcript DBs.")
    parser.add_argument(
        "--metadata",
        type=Path,
        default=Path("data/video_details_cache.json"),
        help="Path to metadata json.",
    )
    parser.add_argument(
        "--transcripts",
        type=Path,
        default=Path("data/transcripts"),
        help="Path to transcripts directory.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("docs/db"),
        help="Output directory for DB shards and manifest.",
    )
    args = parser.parse_args()

    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    grouped = group_by_year(metadata)
    args.out.mkdir(parents=True, exist_ok=True)

    manifest_entries: List[Dict[str, object]] = []

    for year in sorted(grouped.keys()):
        rows = grouped[year]
        db_path = args.out / f"transcripts_{year}.db"
        if db_path.exists():
            db_path.unlink()
        conn = init_db(db_path)
        count = insert_transcripts(conn, rows, args.transcripts)
        conn.execute("VACUUM;")
        conn.close()
        size_bytes = db_path.stat().st_size if db_path.exists() else 0
        manifest_entries.append(
            {
                "year": year,
                "count": count,
                "db": db_path.name,
                "bytes": size_bytes,
            }
        )
        print(f"{year}: {count} transcripts -> {db_path.name} ({size_bytes/1024/1024:.1f} MB)")

    build_manifest(manifest_entries, args.out)
    build_id_index(grouped, args.out)


if __name__ == "__main__":
    main()
