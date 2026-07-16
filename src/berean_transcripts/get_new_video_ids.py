import subprocess
from berean_transcripts.utils import (
    data_dir,
)
import logging

from berean_transcripts.quality import find_transcript_issue
from berean_transcripts.utils import transcripts_dir

log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=log_fmt)
logger = logging.getLogger(__name__)

RECENT_QUALITY_WINDOW = 24


def transcript_needs_retry(video_id):
    transcript_path = transcripts_dir / f"{video_id}.txt"
    if not transcript_path.exists():
        return True
    transcript = transcript_path.read_text(encoding="utf-8", errors="replace")
    issue = find_transcript_issue(transcript)
    if issue:
        logging.warning("Retrying %s: %s", video_id, issue)
    return issue is not None


# Step 1: Get all video list from the channel. Fail closed if discovery fails;
# an empty/partial yt-dlp result must not be mistaken for a valid video ID.
command = [
    "yt-dlp",
    "--flat-playlist",
    "--print",
    "id",
    "https://www.youtube.com/@bereancommunitychurch5642/streams",
]
result = subprocess.run(
    command, stdout=subprocess.PIPE, check=True, text=True
)
video_ids = [video_id for video_id in result.stdout.splitlines() if video_id]
total_videos = len(video_ids)
logging.info(f"Total videos fetched: {total_videos}")

# Step 2: Load existing video ids from the done file
try:
    with open(data_dir / "bcc_live_video_ids_done.txt", "r") as f:
        existing_ids = f.readlines()
    existing_ids = [x.strip() for x in existing_ids]
except FileNotFoundError:
    existing_ids = []

# Step 3: Find new videos, plus recent videos whose transcript failed the
# quality gate. The bounded retry window avoids unexpectedly reprocessing the
# full historical archive.
brand_new_ids = [vid for vid in video_ids if vid not in existing_ids]
retry_ids = [
    vid
    for vid in video_ids[:RECENT_QUALITY_WINDOW]
    if vid in existing_ids and transcript_needs_retry(vid)
]
queued_ids = list(dict.fromkeys(brand_new_ids + retry_ids))
logging.info(
    "Videos queued: %s new, %s quality retries",
    len(brand_new_ids),
    len(retry_ids),
)

# Step 4: Update the bcc_live_video_ids_done.txt by adding new ids at the top
if queued_ids:
    with open(data_dir / "bcc_live_video_ids_done.txt", "w") as f:
        for vid in reversed(brand_new_ids):
            f.write(f"{vid}\n")
        for existing in existing_ids:
            f.write(f"{existing}\n")

    # Step 5: Write new video ids to bcc_live_video_ids.txt
    with open(data_dir / "bcc_live_video_ids.txt", "w") as f:
        for vid in reversed(queued_ids):
            f.write(f"{vid}\n")
else:
    logging.info("No new videos found")
    # make sure bcc_live_video_ids.txt is blank
    with open(data_dir / "bcc_live_video_ids.txt", "w") as f:
        f.write("")
