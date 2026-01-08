import logging
import os
import random
# import asyncio  <-- Removed as run_polling/run_webhook handles it
# from aiohttp import web <-- Removed
from telegram import Update
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
        "Use /motivate to get a random video from my sources."
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
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            # Pick a random source
            source_url = random.choice(sources)
            
            # Update status message on first attempt, or edit it on retries?
            # Simpler to just let them know we are trying.
            if attempt == 0:
                 status_msg = await update.message.reply_text(
                    f"Fetching motivation... 🏋️\nSource: {source_url} \n\nThis might take a moment.",
                    disable_web_page_preview=True
                )
            
            # Direct download
            video_path = downloader.download_video(source_url)
            
            # If successful, send video
            caption = f"<a href=\"{source_url}\">Source</a>"
            await update.message.reply_video(
                video=open(video_path, 'rb'), 
                caption=caption,
                parse_mode='HTML'
            )
            
            # Break loop on success
            break

        except Exception as e:
            logger.error(f"Attempt {attempt + 1}/{max_retries} failed for {source_url}: {e}")
            video_path = None # Reset
            continue
    
    # After loop, check if we succeeded
    if not video_path:
        fail_msg = await update.message.reply_text("Could not fetch a video after 3 attempts. 😔")
        # Auto-delete failure message after 5 seconds
        await asyncio.sleep(5)
        try:
            await fail_msg.delete()
        except:
            pass

    # Cleanup
    if status_msg:
        try:
            await status_msg.delete()
        except:
            pass
    if video_path and os.path.exists(video_path):
        try:
            os.remove(video_path)
        except:
            pass

# --- Main Entry ---

def main():
    if not config.BOT_TOKEN:
        logger.error("TELEGRAM_TOKEN is not set.")
        return

    # Build bot
    application = ApplicationBuilder().token(config.BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("motivate", motivate))

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
