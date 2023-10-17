# get new video ideas
python src/berean_transcripts/get_new_video_ids.py

# Check if bcc_live_video_ids.txt is empty
if [ -s "./data/bcc_live_video_ids.txt" ]; then
    # transcribe new videos
    ./bash_transcribe.sh ./data/bcc_live_video_ids.txt
    
    # generate html and output to docs/
    python src/berean_transcripts/generate_html.py --file ./data/bcc_live_video_ids_done.txt
    
    # commit files
    git add "./data/*.txt"
    git add "./docs/*.html"
    git add data/video_details_cache.json
    git commit -m "adding latest messages from $(date +'%Y-%m-%d')"
    git push
else
    echo "No new videos found. Exiting script."
fi