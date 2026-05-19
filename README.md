# Motivagionbot 🚀

A Telegram bot that sends motivational Instagram Reels to you on demand. Runs wherever you like — homelab, VPS, Render, you name it.

## Features

- **Video Caching**: Videos are downloaded once and cached. Subsequent requests are instant.
- **Stateless by default**: No database needed. All state is in `sources.json` and a local video cache directory.
- **Direct Links**: Uses a curated list of specific Instagram Reels (no flaky scraping).
- **Health Check**: Native polling mode keeps the bot alive and responsive.
- **Privacy Focused**: No Instagram login required for direct link downloads (unless Instagram blocks anonymous requests — see [Cookies](#-cookies-optional-but-recommended)).

## Commands

| Command | Description |
|---|---|
| `/start` | Welcome message and command overview |
| `/motivate` | Receive a random motivational video from your collection |
| `/addvideo <url>` | Add a new Instagram Reel URL to the collection |
| `/stats` | Show source count and cache stats |

## 🛠 Configuration

### 1. Add Your Sources

Open `sources.json` and add the **direct links** to the Instagram Reels you want the bot to send.

**✅ Supported:**
- `https://www.instagram.com/reel/VIDEO_ID/`
- `https://www.instagram.com/p/VIDEO_ID/`

**❌ Not Supported:**
- Profile URLs (e.g., `instagram.com/username/`) are **not** supported due to blocking.

You can also add sources on the fly from Telegram using `/addvideo`.

### 2. Environment Variables

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_TOKEN` | ✅ | Your bot token from [@BotFather](https://t.me/BotFather) |
| `WEBHOOK_URL` | ❌ | (Optional) The public URL of your bot for webhook mode |

The bot automatically runs in **polling mode** (always-on, no public URL needed) when `WEBHOOK_URL` is not set. Polling is the recommended mode if your host is always running (homelab, VPS).

## 💻 Local Development

```bash
pip install -r requirements.txt
# Create .env with TELEGRAM_TOKEN=your_token
python main.py
```

## 🐳 Docker Deployment (Recommended)

```yaml
services:
  motivagionbot:
    build: .
    container_name: motivagionbot
    env_file: .env
    volumes:
      - .:/app               # Live code + sources.json updates
      - ./videos:/app/videos # Persistent video cache
    restart: unless-stopped
```

### Updating the bot

Since the source code is mounted as a volume, you don't need to rebuild to update:

```bash
git pull
docker restart motivagionbot
```

Or edit files directly and restart. For Dockerfile/package changes, rebuild:

```bash
docker compose up -d --build
```

## 🍪 Cookies (Optional, but recommended)

Instagram sometimes blocks anonymous requests. If you see errors downloading videos, you may need to provide your cookies.

1. **Install Extension**: Get ["Get cookies.txt LOCALLY"](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) for Chrome/Firefox.
2. **Export**: Login to Instagram with a burner account, open the extension, and export cookies for `instagram.com`.
3. **Save**: Place the file as `cookies.txt` in the project root.
4. **Mount it**: Add to your Docker volumes: `- ./cookies.txt:/app/cookies.txt`
5. **Restart** the container.

*Note: The cookies.txt file is gitignored for security.*

## 📦 Video Caching

Videos are cached in `./videos/` after first download. Subsequent requests for the same Reel skip the download entirely.

**Caching works on any platform with persistent storage** (homelab, VPS, dedicated server). On platforms with **ephemeral filesystems** (Render free tier, Heroku), the cache will be empty after each restart — videos will be re-downloaded once per instance lifecycle. The bot still works fine; just without the speed benefit.

To pre-populate the cache, run `/motivate` a few times until all your sources are downloaded.

## ☁️ Deploy to Render

1. **Push** this code to a GitHub repository.
2. Create a new **Web Service** on Render.
3. Connect your repository.
4. Use the following settings:
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
5. **Environment Variables**:
   - `TELEGRAM_TOKEN`: (Required) Your Telegram Bot Token from @BotFather.
   - `WEBHOOK_URL`: (Required for Webhooks/Anti-Sleep) The full URL of your Render service (e.g., `https://your-bot.onrender.com`).

The bot will automatically switch to **Webhook mode** when `WEBHOOK_URL` is present, preventing it from sleeping on Render's free tier.

> ⚠️ **Note on caching**: Render's filesystem is ephemeral — the video cache resets on each deploy or restart. Videos are still downloaded and sent, just not persisted between restarts.

## 🤖 Usage

- `/start` — Check if bot is alive and see available commands.
- `/motivate` — Receive a random motivational video from your collection (cached after first download).
- `/addvideo https://www.instagram.com/reel/XXXXX/` — Add a new Reel to your collection.
- `/stats` — See how many sources and cached videos you have.