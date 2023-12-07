import argparse
import logging

import cv2
import numpy as np
from berean_transcripts.transcribe_youtube import extract_video_id
from berean_transcripts.utils import data_dir, dump_json_to_file, videos_dir
from yt_dlp import YoutubeDL


def frame_difference(prev_frame, curr_frame):
    """
    Calculates the difference between two frames.

    Parameters
    ----------
    prev_frame : ndarray
        The previous frame in a video.
    curr_frame : ndarray
        The current frame in a video.

    Returns
    -------
    int
        The sum of the absolute differences between the two frames.
    """
    grayA = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    grayB = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(grayA, grayB)
    return np.sum(diff)


def extract_sections(
    diff = cv2.absdiff(grayA, grayB)
    return np.sum(diff)


def extract_sections(
    video_file,
    video_file_path=videos_dir,
    video_file_ext=".mp4",
    threshold=75_000_000,
    min_seconds=2,
    frame_skip=30,
    start_time=None,
    end_time=None,
):
    """
    Extract sections from sermon video

    Threshold of 75_000_000 works for sunday sermon videos
    """
    logging.info("Identifying sections from sermon video")
    video_file_name = str(video_file_path) + "/" + str(video_file)
    cap = cv2.VideoCapture(video_file_name)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    threshold : int, optional
        The threshold for determining a section transition (default is 75_000_000).
    min_seconds : int, optional
        The minimum number of seconds between section transitions (default is 2).
    frame_skip : int, optional
        The number of frames to skip between checks for section transitions (default is 30).
    start_time : float, optional
        The start time of the video in seconds (default is None).
    end_time : float, optional
        The end time of the video in seconds (default is None).

    Returns
    -------
    list of tuple
        A list of tuples where each tuple represents a section and contains the start and end times in seconds.
    tuple
        A tuple representing the sermon section and containing the start and end times in seconds.
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

        if (
            diff > threshold
            and (timestamp - section_transitions[-1][0]) > min_seconds
        ):
            section_transitions.append((timestamp, i))

        prev_frame = curr_frame

    cap.release()

    sections = []
    for start, end in zip(section_transitions[:-1], section_transitions[1:]):
        sections.append((start[1] / fps, end[1] / fps))

    sections.append((section_transitions[-1][1] / fps, end_frame / fps))
    sermon_section = max(sections, key=lambda x: x[1] - x[0])

    logging.info(
        f"Identified {len(sections)} sections, Sermon section is between frames {sermon_section[0]} and {sermon_section[1]}"
    )

    return sections, sermon_section


def download_video(url, outfile_name, download_dir=videos_dir):
    """
    Downloads a video from a given URL and saves it to a specified output file.

    Parameters
    ----------
    url : str
        The URL from which to download the video.
    outfile_name : str
        The name of the file to which the downloaded video should be saved.
    download_dir : str, optional
        The directory to which the downloaded video should be saved (default is videos_dir).

    Returns
    -------
    None
    """
    try:
        options = {
            "format": "mp4",
            "outtmpl": str(download_dir / outfile_name),
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
    dump_json_to_file(
        sections, data_dir / "sermon_sections" / f"{video_file_name}.json"
    )


if __name__ == "__main__":
    main()
