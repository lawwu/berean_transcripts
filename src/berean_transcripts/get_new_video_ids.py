import subprocess
from berean_transcripts.utils import (
    data_dir,
)
import logging

log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=log_fmt)
logger = logging.getLogger(__name__)


# Step 1: Get all video list from the channel
cmd = "yt-dlp --flat-playlist --print id https://www.youtube.com/@bereancommunitychurch5642/streams"
result = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True, text=True)
video_ids = result.stdout.strip().split("\n")
total_videos = len(video_ids)
logging.info(f"Total videos fetched: {total_videos}")

# Step 2: Load existing video ids from the done file
try:
    with open(data_dir / "bcc_live_video_ids_done.txt", "r") as f:
        existing_ids = f.readlines()
    existing_ids = [x.strip() for x in existing_ids]
except FileNotFoundError:
    existing_ids = []

# Step 3: Find new video ids by comparing
new_ids = [vid for vid in video_ids if vid not in existing_ids]
new_videos_count = len(new_ids)
logging.info(f"New videos found: {new_videos_count}")

# Step 4: Update the bcc_live_video_ids_done.txt by adding new ids at the top
if new_ids:
    with open(data_dir / "bcc_live_video_ids_done.txt", "w") as f:
        for vid in reversed(new_ids):
            f.write(f"{vid}\n")
        for existing in existing_ids:
            f.write(f"{existing}\n")

    # Step 5: Write new video ids to bcc_live_video_ids.txt
    with open(data_dir / "bcc_live_video_ids.txt", "w") as f:
        for vid in reversed(new_ids):
            f.write(f"{vid}\n")
