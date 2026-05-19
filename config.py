import os
import json
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token from Environment Variable
BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
PORT = int(os.getenv('PORT', '10000'))

# Directory for cached video downloads (persistent, not /tmp)
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), 'videos')

# Path to sources.json (inside the mounted repo)
SOURCES_PATH = os.path.join(os.path.dirname(__file__), 'sources.json')

def get_sources():
    """Load sources from sources.json."""
    if os.path.exists(SOURCES_PATH):
        try:
            with open(SOURCES_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return []

def add_source(url):
    """Add a new source URL to sources.json and return True on success."""
    sources = get_sources()
    url = url.strip().rstrip('/')  # Normalize: strip trailing slash

    if url in sources:
        return False  # Already exists

    sources.append(url)
    # Make sure the directory exists
    os.makedirs(os.path.dirname(SOURCES_PATH), exist_ok=True)
    with open(SOURCES_PATH, 'w') as f:
        json.dump(sources, f, indent=4)
    return True