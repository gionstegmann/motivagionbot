import logging
import os
import random
import asyncio
from aiohttp import web
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

# --- Health Check Server ---

async def health_check(request):
    return web.Response(text="Bot is running!")

async def start_health_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()
    logger.info("Health check server started on port 10000")

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

async def main():
    if not config.BOT_TOKEN:
        logger.error("TELEGRAM_TOKEN is not set.")
        return

    # Start health check server
    await start_health_server()

    # Build bot
    application = ApplicationBuilder().token(config.BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("motivate", motivate))

    logger.info("Starting bot polling...")
    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
