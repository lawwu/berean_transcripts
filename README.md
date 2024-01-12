# Berean Transcripts

Sermon transcripts for <https://bereancc.com/> inspired by <https://karpathy.ai/lexicap/index.html>

# Setup

```bash
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
```

# Setup crontab

Start ssh agent

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_rsa
```

Create crontab

```bash
crontab -e
# run at Sundays, 2pm PST and Wednesdays 11pm PST
0 14 * * SUN /Users/lawrencewu/Github/berean_transcripts/bash_transcribe_new_videos.sh >> /Users/lawrencewu/Github/berean_transcripts/crontab_sun.log
0 23 * * WED /Users/lawrencewu/Github/berean_transcripts/bash_transcribe_new_videos.sh >> /Users/lawrencewu/Github/berean_transcripts/crontab_wed.log
```


# TODO

- [x] don't use JSON cache, use a slimmer CSV with id, title, upload_date, url, and other necessary fields
- [ ] Use python bindings instead of calling whisper.cpp directly, can use https://github.com/abdeladim-s/pywhispercpp or https://github.com/aarnphm/whispercpp 
- [ ] automatically tag the beginning and end of the sermons and clip this out
- [ ] Whisper thinks some sections of the sermon are praise
- [ ] check does whisper remove ums and ahs?