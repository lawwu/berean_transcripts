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

# TODO

- [ ] automatically tag the beginning and end of the sermons and clip this out
- [ ] can transfer rest of Berean's Vimeo videos to Youtube: https://github.com/hichamelkaddioui/vimeo-to-youtube and then transcribe
- [ ] Whisper thinks some sections of the sermon are praise
- [ ] Use python bindings instead of calling whisper.cpp directly, can use https://github.com/aarnphm/whispercpp