import logging
import os
import random
import re
import asyncio
import datetime
from telegram import BotCommand, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import config
import downloader

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# --- Bot Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! 🚀\n"
        "I'm a minimalist motivation bot.\n"
        "Use /motivate to get a random video from my sources.\n"
        "Use /addvideo <url> to add a new Instagram Reel to the collection.\n"
        "Use /stats to see how many videos are cached."
    )


async def motivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # 1. Load Sources
    sources = config.get_sources()
    if not sources:
        await update.message.reply_text("No sources found in sources.json or environment variables.")
        return

    # 2. Fetch and Send Loop
    video_path = None
    status_msg = None
    max_retries = 3

    for attempt in range(max_retries):
        try:
            # Pick a random source
            source_url = random.choice(sources)

            # Update status message on first attempt
            if attempt == 0:
                status_msg = await update.message.reply_text(
                    f"Fetching motivation... 🏋️\nThis might take a moment.",
                    disable_web_page_preview=True
                )

            # Direct download (uses cache if available)
            video_path = downloader.download_video(source_url)

            # If successful, send video
            caption = f"<a href=\"{source_url}\">Source</a>"
            await update.message.reply_video(
                video=open(video_path, 'rb'),
                caption=caption,
                parse_mode='HTML',
                read_timeout=60,
                write_timeout=60
            )

            # Break loop on success
            break

        except Exception as e:
            logger.error(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
            video_path = None
            continue

    # After loop, check if we succeeded
    if not video_path:
        fail_msg = await update.message.reply_text("Could not fetch a video after 3 attempts. 😔")
        await asyncio.sleep(5)
        try:
            await fail_msg.delete()
        except:
            pass

    # Cleanup status message
    if status_msg:
        try:
            await status_msg.delete()
        except:
            pass


async def is_admin(update: Update) -> bool:
    """Check if the user is the configured admin."""
    if not config.ADMIN_ID:
        logger.warning("TELEGRAM_ADMIN_ID not set — blocking all users from admin commands.")
        return False
    user_id = str(update.effective_user.id)
    return user_id == config.ADMIN_ID


async def addvideo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a new Instagram Reel URL to sources.json (admin only)."""
    # Admin check
    if not await is_admin(update):
        await update.message.reply_text(
            "⛔ Sorry, only the bot admin can add videos."
        )
        return

    # Check we have a URL
    if not context.args:
        await update.message.reply_text(
            "Usage: /addvideo <instagram_reel_url>\n\n"
            "Example: /addvideo https://www.instagram.com/reel/ABC123/"
        )
        return

    url = context.args[0]

    # Basic validation — must be an Instagram post/reel URL
    if not re.match(r'https?://(www\.)?instagram\.com/(p|reel|reels)/', url):
        await update.message.reply_text(
            "That doesn't look like an Instagram Reel URL.\n"
            "Make sure it starts with:\n"
            "  https://www.instagram.com/reel/...\n"
            "  https://www.instagram.com/p/..."
        )
        return

    # Try to add it
    success = config.add_source(url)
    if success:
        await update.message.reply_text(
            f"✅ Added to collection!\n"
            f"Total sources: {len(config.get_sources())}"
        )
    else:
        await update.message.reply_text(
            "ℹ️ That URL is already in the collection."
        )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show cache stats."""
    sources = config.get_sources()
    video_dir = config.DOWNLOAD_DIR
    cached_count = 0
    if os.path.exists(video_dir):
        cached_count = len([f for f in os.listdir(video_dir) if f.endswith('.mp4')])

    await update.message.reply_text(
        f"📊 **Motivagionbot Stats**\n\n"
        f"📝 Sources: {len(sources)}\n"
        f"💾 Cached videos: {cached_count}\n"
        f"📦 Cache location: `{video_dir}`",
        parse_mode='Markdown'
    )


async def set_commands(application):
    """Register bot commands with Telegram's command menu."""
    commands = [
        BotCommand("start", "Welcome message and usage info"),
        BotCommand("motivate", "Get a random motivational video"),
        BotCommand("addvideo", "Add an Instagram Reel URL to the collection"),
        BotCommand("stats", "Show cache statistics"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Bot commands registered with Telegram menu")


# ── Daily Scheduled Motivation ─────────────────────────────────────

async def scheduled_motivate(context: ContextTypes.DEFAULT_TYPE):
    """Send a random motivational video to the configured target chat at 6am daily."""
    chat_id = context.job.data
    if not chat_id:
        logger.warning("scheduled_motivate: no target chat ID configured")
        return

    sources = config.get_sources()
    if not sources:
        logger.warning("scheduled_motivate: no sources configured")
        return

    for attempt in range(3):
        try:
            source_url = random.choice(sources)
            video_path = downloader.download_video(source_url)
            caption = f"☀️ Good morning!\n<a href=\"{source_url}\">Source</a>"
            await context.bot.send_video(
                chat_id=chat_id,
                video=open(video_path, 'rb'),
                caption=caption,
                parse_mode='HTML',
                read_timeout=60,
                write_timeout=60,
            )
            logger.info(f"scheduled_motivate: sent video to {chat_id}")
            return
        except Exception as e:
            logger.error(f"scheduled_motivate attempt {attempt + 1}/3 failed: {e}")
            continue

    logger.error("scheduled_motivate: all 3 attempts failed")


# --- Main Entry ---

def main():
    if not config.BOT_TOKEN:
        logger.error("TELEGRAM_TOKEN is not set.")
        return

    # Build bot
    application = ApplicationBuilder().token(config.BOT_TOKEN).post_init(set_commands).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("motivate", motivate))
    application.add_handler(CommandHandler("addvideo", addvideo))
    application.add_handler(CommandHandler("stats", stats))

    # Daily scheduled motivation at 6am
    if config.TARGET_CHAT_ID:
        application.job_queue.run_daily(
            scheduled_motivate,
            time=datetime.time(hour=6, minute=0),
            days=tuple(range(7)),  # every day
            data=config.TARGET_CHAT_ID,
            name="daily_motivation",
        )
        logger.info(f"Scheduled daily motivation at 06:00 for chat {config.TARGET_CHAT_ID}")

    if config.WEBHOOK_URL:
        logger.info(f"Starting webhook mode on port {config.PORT}...")
        application.run_webhook(
            listen="0.0.0.0",
            port=config.PORT,
            url_path=config.BOT_TOKEN,
            webhook_url=f"{config.WEBHOOK_URL}/{config.BOT_TOKEN}"
        )
    else:
        logger.info("Starting polling mode...")
        application.run_polling()


if __name__ == '__main__':
    main()