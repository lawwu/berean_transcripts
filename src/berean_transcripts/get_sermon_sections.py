import subprocess
import argparse
from yt_dlp import YoutubeDL
import re
import ffmpeg
import logging
import cv2
import json
import logging
import numpy as np

from berean_transcripts.transcribe_youtube import extract_video_id
from berean_transcripts.utils import (
    transcripts_dir,
    videos_dir,
    data_dir,
    dump_json_to_file,
)

def frame_difference(prev_frame, curr_frame):
    grayA = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    grayB = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(grayA, grayB)
    return np.sum(diff)


def extract_sections(video_file, 
                     video_file_path=videos_dir,
                     video_file_ext=".mp4",
                     threshold=75_000_000, 
                     min_seconds=2, 
                     frame_skip=30, 
                     start_time=None, 
                     end_time=None):
    """
    Extract sections from sermon video

    Threshold of 75_000_000 works for sunday sermon videos
    """
    logging.info("Identifying sections from sermon video")
    video_file_name = str(video_file_path) + "/" + str(video_file)
    cap = cv2.VideoCapture(video_file_name)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    logging(f"Frame rate of the video is: {fps} FPS")

    # Convert start_time and end_time to start_frame and end_frame
    start_frame = int(start_time * fps) if start_time is not None else 0
    end_frame = int(end_time * fps) if end_time is not None else frame_count
    
    # Set the initial position if start_time is provided
    if start_time is not None:
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    ret, prev_frame = cap.read()
    section_transitions = [(start_time or 0, start_frame)]

    for i in range(start_frame, end_frame, frame_skip):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, curr_frame = cap.read()
        if not ret:
            break

        diff = frame_difference(prev_frame, curr_frame)
        timestamp = i / fps

        if diff > threshold and (timestamp - section_transitions[-1][0]) > min_seconds:
            section_transitions.append((timestamp, i))

        prev_frame = curr_frame

    cap.release()

    sections = []
    for start, end in zip(section_transitions[:-1], section_transitions[1:]):
        sections.append((start[1]/fps, end[1]/fps))

    sections.append((section_transitions[-1][1]/fps, end_frame/fps))
    sermon_section = max(sections, key=lambda x: x[1] - x[0])

    logging.info(f"Identified {len(sections)} sections, Sermon section is between frames {sermon_section[0]} and {sermon_section[1]}")
    
    return sections, sermon_section


def download_video(url, outfile_name, download_dir=videos_dir):
    try:
        options = {
            # "format": "bestvideo+bestaudio/best",
            'format': 'mp4',
            "outtmpl": str(download_dir / outfile_name),
            # 'postprocessors': [{
            #     'key': 'FFmpegVideoConvertor',
            #     'preferedformat': 'mp4',
            # }]
        }
        with YoutubeDL(options) as ydl:
            print(f"Downloading: {url}")
            ydl.download([url])
    except Exception as e:
        print(f"Error in download_video: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Automate downloading and processing audio from YouTube."
    )
    parser.add_argument("url", type=str, help="URL of the YouTube video")
    args = parser.parse_args()
    video_file_name = extract_video_id(args.url)

    logging.info("Download audio from YouTube")
    download_video(args.url, video_file_name)

    logging.info(f"Get sermon sections for {video_file_name}")
    sections, sermon_section = extract_sections(video_file_name)

    logging.info("Creating dictionary with sections and video_id")
    sections = {
        "video_id": video_file_name,
        "sermon_section": sermon_section,
        "sections": sections,
    }

    logging.info("Dumping sections to json")
    dump_json_to_file(sections, 
                      data_dir / "sermon_sections" / f"{video_file_name}.json")


if __name__ == "__main__":
    main()
