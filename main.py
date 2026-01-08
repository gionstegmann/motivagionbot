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

    # 2. Pick Source
    source_url = random.choice(sources)
    
    status_msg = await update.message.reply_text(
        f"Fetching motivation... 🏋️\nSource: {source_url} \n\nThis might take a moment.",
        disable_web_page_preview=True
    )
    
    # 3. Fetch and Send
    video_path = None
    try:
        # Direct download from the source URL
        video_path = downloader.download_video(source_url)
        
        caption = f"<a href=\"{source_url}\">Source</a>"
        await update.message.reply_video(
            video=open(video_path, 'rb'), 
            caption=caption,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error in motivate: {e}")
        await update.message.reply_text("Failed to fetch or send video. Check logs.")
    finally:
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
