import yt_dlp
import os
import random
import glob
import logging
import config

# Configure headers to mimic a browser to avoid some blocks
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'



def download_video(video_url):
    """
    Downloads a video from a URL to a temporary file.
    Returns the absolute path to the file.
    """
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
        'format': 'best[ext=mp4]/best', # Prefer mp4
        'quiet': True,
        'user_agent': USER_AGENT,
        'overwrites': True,
        'nocheckcertificate': True,
    }

    if os.path.exists(cookie_file):
        ydl_opts['cookiefile'] = cookie_file
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            return filename
        except Exception as e:
            logging.error(f"Error downloading {video_url}: {e}")
            raise e

