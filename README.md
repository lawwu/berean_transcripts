# Berean Transcripts

Sermon transcripts for <https://bereancc.com/> inspired by <https://karpathy.ai/lexicap/index.html>

# Setup

```bash
pyenv local 3.11
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# install berean_transcripts in editable mode
pip install -e .

# initialize git-lfs
git lfs install

# build whisper.cpp
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make clean
make -j

# setup pre-commit
pre-commit install

# setup crontab
crontab -e
# run at Sundays, 2pm PST and Wednesdays 11pm PST
# 0 14 * * 0 /Users/lawrencewu/Github/berean_transcripts/bash_transcribe_new_videos.sh
# 0 23 * * 3 /Users/lawrencewu/Github/berean_transcripts/bash_transcribe_new_videos.sh
```


# TODO

- [X] ~~can transfer rest of Berean's Vimeo videos to Youtube: https://github.com/hichamelkaddioui/vimeo-to-youtube and then transcribe~~ Decided to leave Vimeo videos alone and transcribe them in place
- [ ] don't use JSON cache, use a slimmer CSV with id, title, upload_date, url, and other necessary fields
- [ ] automatically tag the beginning and end of the sermons and clip this out
- [ ] Whisper thinks some sections of the sermon are praise
- [ ] Use python bindings instead of calling whisper.cpp directly, can use https://github.com/aarnphm/whispercpp