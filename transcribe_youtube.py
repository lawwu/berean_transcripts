def extract_video_id(url):\n    """\n    Extracts the video ID from a given URL.\n\n    Parameters:\n    - url (str): The URL of the video.\n\n    Returns:\n    - str: The extracted video ID.\n    """
    """
    Extracts the video ID from a given URL.

    Parameters:
    - url (str): The URL of the video.

    Returns:
    - str: The extracted video ID.
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
def download_audio(url):
    """
    Downloads audio from the given URL.

    Parameters:
    - url (str): The URL of the video.

    Returns:
    - str: The extracted video ID.
    """
