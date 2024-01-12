#!/bin/bash

echo "Script started at $(date)"

# Set the absolute path to the Git repository directory
SCRIPT_DIR="/Users/lawrencewu/Github/berean_transcripts"
SSH_KEY_PATH="/Users/lawrencewu/.ssh/id_rsa"

# Change to the Git repository directory
cd "$SCRIPT_DIR"

# Set the Git remote URL to use SSH
export PATH=$PATH:/opt/homebrew/bin
git remote set-url origin git@github.com:lawwu/berean_transcripts.git
git lfs install

# Activate the virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Start the SSH agent and add the SSH key
eval "$(ssh-agent -s)"
ssh-add "$SSH_KEY_PATH"

# Get new video ideas
python "$SCRIPT_DIR/src/berean_transcripts/get_new_video_ids.py"

# Check if bcc_live_video_ids.txt is empty
if [ -s "$SCRIPT_DIR/data/bcc_live_video_ids.txt" ]; then
    # Transcribe new videos
    "$SCRIPT_DIR/bash_transcribe.sh" "$SCRIPT_DIR/data/bcc_live_video_ids.txt"
    
    # Generate HTML and output to docs/
    python "$SCRIPT_DIR/src/berean_transcripts/generate_html.py"
    
    # Commit files
    git add "$SCRIPT_DIR/data/*.txt"
    git add "$SCRIPT_DIR/docs/*.html"
    git add "$SCRIPT_DIR/data/video_details_cache.json"
    git commit -m "AUTO: adding latest messages from $(date +'%Y-%m-%d')"
    git push 2>&1 | tee "$SCRIPT_DIR/git_push_output.log"

else
    echo "No new videos found. Exiting script."
fi

# Kill the SSH agent
eval "$(ssh-agent -k)"

echo "Script finished at $(date)"