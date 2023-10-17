import subprocess
import argparse
from yt_dlp import YoutubeDL
import re
import ffmpeg
import logging

from berean_transcripts.utils import (
    transcripts_dir,
    model_dir,
    whispercpp_dir,
    timeit,
)

log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=log_fmt)
logger = logging.getLogger(__name__)


def extract_video_id(url):
    match = re.search(r"v=([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1)
    else:
        return "unknown_id"


def download_audio(url, outfile_name):
    try:
        # video_id = extract_video_id(url)
        options = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "192",
                }
            ],
            "outtmpl": str(transcripts_dir / outfile_name)
            # "outtmpl": f"./berean/{outfile_name}",
        }
        with YoutubeDL(options) as ydl:
            print(f"Downloading: {url}")
            ydl.download([url])
    except Exception as e:
        print(f"Error in download_audio: {e}")


# Extract audio from video
def extract_audio(video_file, audio_file):
    """
    Extract audio from video

    Parameters
    ----------
    video_file : str
        Path to video file
    audio_file : str
        Path to audio file

    Returns
    -------
    None
    """
    logging.info(
        f"Using ffmpeg to extract audio from {video_file} to {audio_file}"
    )
    try:
        (
            ffmpeg.input(video_file)
            .output(audio_file, acodec="mp3", ac=2, ar="48k", ab="192k")
            .run(overwrite_output=True)
        )
        return audio_file
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return None


def ensure_wav_16k(filename):
    input_path = transcripts_dir / f"{filename}.wav"
    output_path = transcripts_dir / f"{filename}_16k.wav"
    # always override with yes
    command = ["ffmpeg", "-y", "-i", input_path, "-ar", "16000", output_path]
    subprocess.run(command)


@timeit
def run_whisper(filename, num_threads=4, num_processors=1):
    model_path = model_dir / "ggml-large.bin"
    input_path = transcripts_dir / f"{filename}_16k.wav"
    output_path = transcripts_dir / f"{filename}.txt"

    whisper_main = whispercpp_dir / "main"
    command = f"{whisper_main} -m {model_path} -t {num_threads} -p {num_processors} -f {input_path} > {output_path}"
    subprocess.run(command, shell=True)


def main():
    parser = argparse.ArgumentParser(
        description="Automate downloading and processing audio from YouTube."
    )
    parser.add_argument("url", type=str, help="URL of the YouTube video")
    args = parser.parse_args()

    # Variable for .wav file name
    # wav_file_name = "bcc_gal3_trimmed"
    wav_file_name = extract_video_id(args.url)

    logging.info("Download audio from YouTube")
    download_audio(args.url, wav_file_name)

    logging.info("Ensure the wav file is 16 kHz")
    ensure_wav_16k(wav_file_name)

    logging.info("Run whisper.cpp using Metal")
    run_whisper(wav_file_name)


if __name__ == "__main__":
    main()
