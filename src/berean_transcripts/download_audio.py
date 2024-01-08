"""
This module contains functions to automate the process of downloading and transcribing audio from YouTube/Vimeo videos.
"""
import argparse
import logging
import re
import subprocess

import ffmpeg
from berean_transcripts.utils import (model_dir, timeit, transcripts_dir,
                                      whispercpp_dir)
from yt_dlp import YoutubeDL

log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=log_fmt)
logger = logging.getLogger(__name__)

def extract_video_id(url):
    """
    Extracts the video ID from a given URL.

    Parameters
    ----------
    url : str
        The URL from which to extract the video ID.

    Returns
    -------
    str
        The extracted video ID, or "unknown_id" if the URL does not match the expected patterns.
    """
    # Check for YouTube URL pattern
    youtube_match = re.search(r"v=([a-zA-Z0-9_-]+)", url)
    if youtube_match:
        return youtube_match.group(1)

    # Check for Vimeo URL pattern
    vimeo_match = re.search(r"vimeo.com/(\d+)", url)
    if vimeo_match:
        return vimeo_match.group(1)

    # If neither pattern is found
    return "unknown_id"


def download_audio(url, outfile_name):
    """
    Downloads the audio from a given URL and saves it to a specified output file.

    Parameters
    ----------
    url : str
        The URL from which to download the audio.
    outfile_name : str
        The name of the file to which the downloaded audio should be saved.

    Returns
    -------
    None
    """
    try:
        options = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "192",
                }
            ],
            "outtmpl": str(transcripts_dir / outfile_name),
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
    """
    Ensures that a given .wav file is at a 16 kHz sample rate.

    Parameters
    ----------
    filename : str
        The name of the .wav file to process.

    Returns
    -------
    None
    """
    input_path = transcripts_dir / f"{filename}.wav"
    output_path = transcripts_dir / f"{filename}_16k.wav"
    # always override with yes
    command = ["ffmpeg", "-y", "-i", input_path, "-ar", "16000", output_path]
    subprocess.run(command)


@timeit
def run_whisper(filename, model_name, num_threads=7, num_processors=1):
    """
    Runs the whisper.cpp program on a given .wav file using a specified model.

    Parameters
    ----------
    filename : str
        The name of the .wav file to process.
    model_name : str
        The name of the model to use for processing.
    num_threads : int, optional
        The number of threads to use for processing (default is 7).
    num_processors : int, optional
        The number of processors to use for processing (default is 1).

    Returns
    -------
    None
    """
    model_path = model_dir / model_name
    input_path = transcripts_dir / f"{filename}_16k.wav"
    output_path = transcripts_dir / f"{filename}.txt"

    whisper_main = whispercpp_dir / "main"
    command = f"{whisper_main} -m {model_path} -t {num_threads} -p {num_processors} -f {input_path} > {output_path}"
    subprocess.run(command, shell=True)


def clean_up_wav_files(base_filename):
    """
    Deletes the .wav and _16k.wav files for the given base filename.

    Parameters
    ----------
    base_filename : str
        The base name of the .wav files to delete.
    """
    try:
        wav_path = transcripts_dir / f"{base_filename}.wav"
        wav_16k_path = transcripts_dir / f"{base_filename}_16k.wav"

        # Remove the original wav file
        if wav_path.exists():
            wav_path.unlink()
            logging.info(f"Deleted {wav_path}")

        # Remove the 16kHz wav file
        if wav_16k_path.exists():
            wav_16k_path.unlink()
            logging.info(f"Deleted {wav_16k_path}")

    except Exception as e:
        logging.error(f"Error during file cleanup: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Automate downloading and processing audio from YouTube/Vimeo."
    )
    parser.add_argument("url", type=str, help="URL of the video")
    parser.add_argument(
        "--model_name",
        type=str,
        default="ggml-large.bin",
        help="Name of the whisper model to use",
    )
    args = parser.parse_args()

    # Variable for .wav file name
    wav_file_name = extract_video_id(args.url)

    logging.info("Download audio")
    download_audio(args.url, wav_file_name)

    logging.info("Ensure the wav file is 16 kHz")
    ensure_wav_16k(wav_file_name)


if __name__ == "__main__":
    main()
