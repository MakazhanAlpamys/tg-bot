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
        
        # Start bot polling
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  Received shutdown signal...")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup
        logger.info("🧹 Cleaning up...")
        bot_status['running'] = False
        try:
            await bot.stop()
            await db.close()
            if 'web_runner' in locals():
                await web_runner.cleanup()
        except:
            pass
        logger.info("👋 Bot stopped. Goodbye!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
