#!/bin/bash

echo "Script started at $(date)"

# Set the absolute path to the script directory
SCRIPT_DIR="/Users/lawrencewu/Github/berean_transcripts"

# Activate the virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Change to the script directory
cd "$SCRIPT_DIR"

# Get new video ideas
python "$SCRIPT_DIR/src/berean_transcripts/get_new_video_ids.py"

# Check if bcc_live_video_ids.txt is empty
if [ -s "$SCRIPT_DIR/data/bcc_live_video_ids.txt" ]; then
    # Transcribe new videos
    "$SCRIPT_DIR/bash_transcribe.sh" "$SCRIPT_DIR/data/bcc_live_video_ids.txt"
    
    # Generate HTML and output to docs/
    python "$SCRIPT_DIR/src/berean_transcripts/generate_html.py" --file "$SCRIPT_DIR/data/bcc_live_video_ids_done.txt"
    
    # Commit files
    git add "$SCRIPT_DIR/data/*.txt"
    git add "$SCRIPT_DIR/docs/*.html"
    # git add "$SCRIPT_DIR/data/video_details_cache.json"
    git commit -m "AUTO: adding latest messages from $(date +'%Y-%m-%d')"
    git push
else
    echo "No new videos found. Exiting script."
fi

echo "Script finished at $(date)"