#!/bin/bash

# Read IDs from the text file and store them in a variable
ids=$(cat ./data/bcc_vimeo_ids.txt)

# Loop through each YouTube ID
for id in $ids; do
  # Create the full YouTube URL
  url="https://vimeo.com/$id"
  
  # Call your Python script
  # python src/berean_transcripts/transcribe_youtube.py "$url" --model_name ggml-large-32-2.en.bin
  python src/berean_transcripts/transcribe_youtube.py "$url" --model_name ggml-large-v3.bin
  
  # Optionally, sleep for a few seconds to avoid hitting rate limits
  sleep 2
done
