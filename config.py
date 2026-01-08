import os
import json
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token from Environment Variable
BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Directory for temporary downloads
DOWNLOAD_DIR = "/tmp/motivagion_downloads"

def get_sources():
    """Load sources from sources.json or environment variable."""
    # 1. Try JSON file
    json_path = os.path.join(os.path.dirname(__file__), 'sources.json')
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r') as f:
                return json.load(f)
        except Exception:
            pass

    return []

