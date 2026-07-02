import argparse
import json
import logging
import re
from pathlib import Path

from yt_dlp import YoutubeDL

from berean_transcripts.utils import data_dir

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_minimum_info_dict(info_dict: dict) -> dict:
    return {
        "id": info_dict.get("id", None),
        "title": info_dict.get("title", None),
        "upload_date": info_dict.get("upload_date", None),
        "duration": info_dict.get("duration", None),
        "webpage_url": info_dict.get("webpage_url", None),
        "thumbnail": info_dict.get("thumbnail", None),
        "thumbnails": info_dict.get("thumbnails", None),
        "chapters": info_dict.get("chapters", []),
    }


def fetch_video_details(video_id: str) -> dict | None:
    ydl_opts = {"quiet": True}
    youtube_match = re.search(r"([a-zA-Z0-9_-]{11})", video_id)
    if youtube_match:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(
                f"https://www.youtube.com/watch?v={video_id}", download=False
            )
            return get_minimum_info_dict(info_dict)

    vimeo_match = re.search(r"(\d+)", video_id)
    if vimeo_match:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(
                f"https://www.vimeo.com/{video_id}", download=False
            )
            return get_minimum_info_dict(info_dict)

    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch and cache yt-dlp metadata for transcribed videos "
        "that aren't in video_details_cache.json yet."
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=data_dir / "bcc_live_video_ids_done.txt",
        help="File with one video ID per line to ensure are cached.",
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=data_dir / "video_details_cache.json",
        help="Path to metadata cache json.",
    )
    args = parser.parse_args()

    if args.cache.exists():
        cache = json.loads(args.cache.read_text(encoding="utf-8"))
    else:
        cache = {}

    video_ids = [
        line.strip()
        for line in args.file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    missing = [vid for vid in video_ids if vid not in cache]
    logging.info(f"{len(missing)} video(s) missing from cache")

    for video_id in missing:
        logging.info(f"Fetching details for {video_id}")
        try:
            info = fetch_video_details(video_id)
        except Exception:
            logging.exception(f"Failed to fetch details for {video_id}")
            continue
        if info is None:
            logging.warning(f"Could not parse video id: {video_id}")
            continue
        cache[video_id] = info
        args.cache.write_text(json.dumps(cache), encoding="utf-8")

    logging.info("Cache update complete")


if __name__ == "__main__":
    main()
