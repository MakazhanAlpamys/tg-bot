"""
Main entry point for Telegram Analytics Bot.
Initializes all components and starts the bot.
"""
import asyncio
import os
import sys
import logging
from aiohttp import web
from dotenv import load_dotenv
from db import Database
from gemini_service import GeminiService
from bot import TelegramAnalyticsBot
from utils import setup_logging

logger = logging.getLogger(__name__)

# Global bot status
bot_status = {
    'running': False,
    'authenticated': False,
    'started_at': None
}


async def health_check(request):
    """Health check endpoint for Render."""
    return web.Response(text='OK', status=200)


async def status_endpoint(request):
    """Status endpoint returning bot information."""
    return web.json_response({
        'status': 'running' if bot_status['running'] else 'starting',
        'authenticated': bot_status['authenticated'],
        'started_at': bot_status['started_at']
    })


async def root_endpoint(request):
    """Root endpoint with bot information."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Telegram Analytics Bot</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-align: center;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            }
            h1 { margin-top: 0; font-size: 2.5em; }
            .status {
                font-size: 1.3em;
                margin: 20px 0;
                padding: 15px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 10px;
            }
            .features {
                text-align: left;
                background: rgba(255, 255, 255, 0.2);
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
            }
            a {
                display: inline-block;
                margin: 10px;
                padding: 15px 30px;
                background: white;
                color: #667eea;
                text-decoration: none;
                border-radius: 10px;
                font-weight: bold;
                transition: transform 0.2s;
            }
            a:hover { transform: scale(1.05); }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Telegram Analytics Bot</h1>
            <div class="status">Status: ✅ Running</div>
            <div class="features">
                <h3>📊 Features:</h3>
                <ul>
                    <li>📝 Automatic message tracking</li>
                    <li>🤖 /bot &lt;question&gt; - AI-powered Q&amp;A</li>
                    <li>📊 /report - detailed 24-hour analytics</li>
                    <li>🗑️ 14-day message retention</li>
                </ul>
            </div>
            <div>
                <a href="/status">📊 Check Status</a>
                <a href="/health">💚 Health Check</a>
            </div>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')


async def start_web_server():
    """Start HTTP server for health checks."""
    app = web.Application()
    app.router.add_get('/', root_endpoint)
    app.router.add_get('/health', health_check)
    app.router.add_get('/status', status_endpoint)
    
    port = int(os.getenv('PORT', 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"🌐 HTTP server started on port {port}")
    return runner


async def main():
    """Main function to start the bot."""
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    setup_logging()
    
    logger.info("=" * 60)
    logger.info("🚀 Telegram Analytics Bot Starting...")
    logger.info("=" * 60)
    
    # Start web server first for Render health checks
    web_runner = await start_web_server()
    
    # Validate environment variables
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    database_url = os.getenv("DATABASE_URL")
    
    if not bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
        sys.exit(1)
    
    if not gemini_api_key:
        logger.error("❌ GEMINI_API_KEY not found in environment variables")
        sys.exit(1)
    
    if not database_url:
        logger.error("❌ DATABASE_URL not found in environment variables")
        sys.exit(1)
    
    logger.info("✅ Environment variables loaded")
    
    db = None
    bot = None
    
    try:
        # Initialize database
        logger.info("📦 Initializing database connection...")
        db = Database(database_url)
        await db.connect()
        
        # Initialize Gemini service
        logger.info("🤖 Initializing Gemini AI service...")
        gemini = GeminiService(gemini_api_key)
        
        # Initialize bot
        logger.info("🤖 Initializing Telegram bot...")
        bot = TelegramAnalyticsBot(
            bot_token=bot_token,
            database=db,
            gemini_service=gemini
        )
        
        # Scheduler disabled - use /report command instead
        logger.info("💡 Automatic scheduling disabled - use /report command for reports")
        
        # Update bot status
        from datetime import datetime
        bot_status['running'] = True
        bot_status['authenticated'] = True
        bot_status['started_at'] = datetime.utcnow().isoformat()
        
        # Log startup info
        logger.info("=" * 60)
        logger.info("✅ Bot is now running!")
        logger.info("=" * 60)
        logger.info("📊 Features:")
        logger.info("  • Automatic message tracking")
        logger.info("  • /bot <question> - AI-powered Q&A")
        logger.info("  • /report - detailed 24-hour analytics report")
        logger.info("  • 14-day message retention")
        logger.info("=" * 60)
        
        # Start bot polling (runs forever until stopped)
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  Received shutdown signal (Ctrl+C)...")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
    finally:
        # Cleanup
        logger.info("🧹 Cleaning up...")
        bot_status['running'] = False
        
        if bot:
            try:
                await bot.stop()
            except Exception as e:
                logger.error(f"Error stopping bot: {e}")
        
        if db:
            try:
                await db.close()
            except Exception as e:
                logger.error(f"Error closing database: {e}")
        
        # Keep web server running for health checks
        logger.info("⚠️ Web server will continue running for health checks")
        logger.info("👋 Bot stopped. Use Ctrl+C again to fully exit.")


async def run_with_restart():
    """Run bot with automatic restart on failure."""
    import signal
    
    shutdown_requested = asyncio.Event()
    
    def signal_handler(signum):
        logger.warning(f"⚠️ Received signal {signum} - ignoring for bot stability")
        logger.info("💡 Bot will continue running. Use multiple Ctrl+C to force stop.")
    
    # Override default signal handlers to prevent premature shutdown
    loop = asyncio.get_event_loop()
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))
    
    restart_count = 0
    max_restarts = 10
    consecutive_failures = 0
    
    while restart_count < max_restarts:
        try:
            if restart_count > 0:
                logger.info(f"🔄 Restarting bot (attempt {restart_count + 1}/{max_restarts})...")
            
            await main()
            
            # If main() exits normally without error, reset failure counter
            consecutive_failures = 0
            logger.info("ℹ️ Bot exited normally, restarting in 5 seconds...")
            await asyncio.sleep(5)
            restart_count += 1
                
        except KeyboardInterrupt:
            logger.info("⏹️ Keyboard interrupt received")
            break
        except Exception as e:
            restart_count += 1
            consecutive_failures += 1
            logger.error(f"❌ Bot crashed: {e}", exc_info=True)
            
            if consecutive_failures >= 3:
                logger.error("❌ Too many consecutive failures, giving up")
                break
            
            if restart_count < max_restarts:
                wait_time = min(consecutive_failures * 10, 60)
                logger.info(f"⏳ Waiting {wait_time} seconds before restart...")
                await asyncio.sleep(wait_time)
            else:
                logger.error("❌ Max restart attempts reached")
                break
    
    logger.info("👋 Application shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(run_with_restart())
    except KeyboardInterrupt:
        pass
