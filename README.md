# Minimalist Motivational Bot 🚀

A simple Telegram bot that sends motivational videos to you when with the `/motivate` command. It also works in group chats.
Designed to be lightweight and easily deployable on free tier hosting services like **Render**.

## Features
- **Stateless**: No database required.
- **Direct Links**: Uses a curated list of specific Instagram Reels (no flaky scraping).
- **Health Check**: Native `aiohttp` server to satisfy Render's port requirements.
- **Privacy Focused**: No Instagram login required for direct link downloads.

## 🛠 Configuration

### 1. Add Your Sources
Open `sources.json` and add the **direct links** to the Instagram Reels you want the bot to send.

**✅ Supported:**
- `https://www.instagram.com/reel/VIDEO_ID/`
- `https://www.instagram.com/p/VIDEO_ID/`

**❌ Not Supported:**
- Profile URLs (e.g., `instagram.com/username/`) are **not** supported due to blocking.

## 💻 Local Development

1.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Configure Environment**:
    Rename `.env.example` to `.env` and add your bot token. 
    To get a bot token, use @BotFather on Telegram.

3.  **Run**:
    ```bash
    python main.py
    ```

### 🍪 Cookies (Optional, but recommended)

While this bot might works without, Instagram sometimes blocks anonymous requests. If you see errors downloading videos, you may need to provide your cookies.

1.  **Install Extension**: Get "Get cookies.txt LOCALLY" for Chrome/Firefox.
2.  **Export**: Login to Instagram with a burner account, open the extension, and export cookies for `instagram.com`.
3.  **Save**: Rename the file to `cookies.txt` and place it in the project root.
    *   *Note: This file is ignored by git for security.*

## ☁️ Deploy to Render

This bot is pre-configured for Render.com.

1.  **Push** this code to a GitHub repository.
2.  Create a new **Web Service** on Render.
3.  Connect your repository.
4.  Use the following settings:
    *   **Runtime**: `Python 3`
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `python main.py`
5.  **Environment Variables**:
    *   `TELEGRAM_TOKEN`: (Required) Your Telegram Bot Token from @BotFather.

The bot will automatically start a health-check server on port `10000`.

## 🤖 Usage
- `/start` - Check if bot is alive.
- `/motivate` - Receive a random motivational video from your list.
