import yt_dlp
import os
import glob
import logging
import config

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'


def _video_id_from_url(video_url):
    """Extract a stable video ID from an Instagram URL."""
    # Strip trailing slash
    url = video_url.rstrip('/')
    # The last path segment is the ID
    return url.rsplit('/', 1)[-1]


def _cached_path(video_id):
    """Full path for a cached video by its ID."""
    return os.path.join(config.DOWNLOAD_DIR, f"{video_id}.mp4")


def download_video(video_url):
    """
    Downloads a video from a URL and caches it.
    Returns the absolute path to the file.
    """
    video_id = _video_id_from_url(video_url)
    cached = _cached_path(video_id)

    # Return cached copy if it exists
    if os.path.exists(cached):
        logging.info(f"Cache hit for {video_id} — using cached video")
        return cached

    # Ensure download dir exists
    if not os.path.exists(config.DOWNLOAD_DIR):
        try:
            os.makedirs(config.DOWNLOAD_DIR)
        except Exception as e:
            logging.warning(f"Failed to create {config.DOWNLOAD_DIR}, using current dir: {e}")
            config.DOWNLOAD_DIR = "."

    output_template = os.path.join(config.DOWNLOAD_DIR, '%(id)s.%(ext)s')

    cookie_file = os.path.join(os.path.dirname(__file__), 'cookies.txt')

    ydl_opts = {
        'outtmpl': output_template,
        'format': 'best[ext=mp4]/best',
        'quiet': True,
        'user_agent': USER_AGENT,
        'overwrites': False,  # Don't redownload on retry
        'nocheckcertificate': True,
    }

    if os.path.exists(cookie_file):
        ydl_opts['cookiefile'] = cookie_file
        logging.info("Using cookies.txt for authentication")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            # yt-dlp may save with a different extension than .mp4
            # If it saved something else, rename to .mp4 for consistency
            actual_path = filename
            if actual_path != cached and os.path.exists(actual_path):
                os.rename(actual_path, cached)
                return cached
            return actual_path
        except Exception as e:
            logging.error(f"Error downloading {video_url}: {e}")
            raise e