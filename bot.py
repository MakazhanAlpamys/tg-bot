"""
Main bot logic and message handlers.
"""
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
from db import Database
from gemini_service import GeminiService
from utils import chunk_text, format_username

logger = logging.getLogger(__name__)


class TelegramAnalyticsBot:
    def __init__(
        self,
        bot_token: str,
        database: Database,
        gemini_service: GeminiService
    ):
        self.bot = Bot(token=bot_token)
        self.dp = Dispatcher()
        self.db = database
        self.gemini = gemini_service
        
        # Register handlers
        self._register_handlers()

    def _register_handlers(self):
        """Register all message and command handlers."""
        # Command handler for /bot
        self.dp.message(Command("bot"))(self.handle_bot_command)
        
        # Command handler for /report
        self.dp.message(Command("report"))(self.handle_report_command)
        
        # Handler for all other messages (store in DB)
        self.dp.message(F.text)(self.handle_message)

    async def handle_message(self, message: Message):
        """
        Store all group messages in the database.
        Ignores commands and only stores regular text messages.
        """
        logger.info(f"Received message: chat_type={message.chat.type}, text='{message.text[:50]}...'")
        
        # Skip if it's a command
        if message.text and message.text.startswith('/'):
            logger.info("Skipping command message")
            return
        
        # Only process group messages
        if message.chat.type not in ['group', 'supergroup']:
            logger.info(f"Skipping non-group message: {message.chat.type}")
            return
        
        try:
            user_id = str(message.from_user.id)
            user_name = format_username(message.from_user)
            chat_id = message.chat.id
            message_text = message.text or ""
            
            # Store message in database
            await self.db.insert_message(
                chat_id=chat_id,
                user_id=user_id,
                user_name=user_name,
                message_text=message_text
            )
            
            logger.debug(f"Stored message from {user_name} in chat {chat_id}")
            
        except Exception as e:
            logger.error(f"Error storing message: {e}")

    async def handle_report_command(self, message: Message):
        """
        Handle /report command.
        Generates detailed analytics report for last 24 hours.
        """
        chat_id = message.chat.id
        
        # Only process in group chats
        if message.chat.type not in ['group', 'supergroup']:
            await message.reply("📊 This command only works in group chats!")
            return
        
        try:
            # Send "typing" action
            await self.bot.send_chat_action(chat_id, "typing")
            
            # Send processing message
            status_msg = await message.reply("📊 Generating detailed report... This may take up to 30 seconds.")
            
            # Fetch messages from last 24 hours
            messages = await self.db.get_messages_last_24h(chat_id)
            
            if not messages:
                await status_msg.edit_text("📊 **Daily Report**\n\nNo messages found in the last 24 hours.")
                return
            
            logger.info(f"Generating report with {len(messages)} messages for chat {chat_id}")
            
            # Generate report using Gemini
            report = await self.gemini.generate_daily_report(messages)
            
            # Delete status message
            try:
                await status_msg.delete()
            except:
                pass
            
            # Send report (split if needed)
            chunks = chunk_text(report)
            
            for i, chunk in enumerate(chunks):
                try:
                    if i == 0:
                        await self.bot.send_message(
                            chat_id,
                            f"📊 **Daily Analytics Report**\n\n{chunk}",
                            parse_mode="Markdown"
                        )
                    else:
                        await self.bot.send_message(chat_id, chunk, parse_mode="Markdown")
                except Exception as markdown_error:
                    logger.warning(f"Markdown error in report, sending as plain text: {markdown_error}")
                    if i == 0:
                        await self.bot.send_message(
                            chat_id,
                            f"📊 Daily Analytics Report\n\n{chunk}"
                        )
                    else:
                        await self.bot.send_message(chat_id, chunk)
            
            logger.info(f"✅ Report sent to chat {chat_id}")
            
        except Exception as e:
            logger.error(f"Error handling /report command: {e}")
            await message.reply(
                f"❌ Failed to generate report: {str(e)}"
            )

    async def handle_bot_command(self, message: Message):
        """
        Handle /bot <question> command.
        Retrieves last 14 days of messages and asks Gemini to answer.
        """
        # Only process in group chats
        if message.chat.type not in ['group', 'supergroup']:
            await message.reply("🤖 This command only works in group chats!")
            return
        
        # Extract question from command
        command_parts = message.text.split(maxsplit=1)
        if len(command_parts) < 2:
            await message.reply(
                "Please provide a question after /bot\n"
                "Example: `/bot What were the main topics discussed this week?`",
                parse_mode="Markdown"
            )
            return
        
        question = command_parts[1]
        chat_id = message.chat.id
        
        try:
            # Send "typing" action
            await self.bot.send_chat_action(chat_id, "typing")
            
            # Fetch messages from last 14 days
            messages = await self.db.get_messages_last_14_days(chat_id)
            
            if not messages:
                await message.reply(
                    "I don't have any message history yet. Start chatting and ask me again later!"
                )
                return
            
            logger.info(f"Processing /bot command with {len(messages)} messages")
            
            # Get answer from Gemini
            answer = await self.gemini.answer_question(question, messages)
            
            # Split response if too long for Telegram
            chunks = chunk_text(answer)
            
            for chunk in chunks:
                try:
                    await message.reply(chunk, parse_mode="Markdown")
                except Exception as markdown_error:
                    logger.warning(f"Markdown error, sending as plain text: {markdown_error}")
                    await message.reply(chunk)
            
        except Exception as e:
            logger.error(f"Error handling /bot command: {e}")
            await message.reply(
                f"❌ Sorry, I encountered an error while processing your question:\n{str(e)}"
            )

    async def send_daily_report(self, chat_id: int):
        """
        Generate and send daily analytics report to the group.
        Called by scheduler at 23:59 daily.
        """
        try:
            logger.info(f"Generating daily report for chat {chat_id}")
            
            # Fetch messages from last 24 hours
            messages = await self.db.get_messages_last_24h(chat_id)
            
            if not messages:
                logger.info(f"No messages in last 24h for chat {chat_id}")
                await self.bot.send_message(
                    chat_id,
                    "📊 **Daily Report**\n\nNo messages were recorded in the last 24 hours."
                )
                return
            
            # Generate report using Gemini
            report = await self.gemini.generate_daily_report(messages)
            
            # Send report (split if needed)
            chunks = chunk_text(report)
            
            for i, chunk in enumerate(chunks):
                try:
                    if i == 0:
                        await self.bot.send_message(
                            chat_id,
                            f"📊 **Daily Analytics Report**\n\n{chunk}",
                            parse_mode="Markdown"
                        )
                    else:
                        await self.bot.send_message(chat_id, chunk, parse_mode="Markdown")
                except Exception as markdown_error:
                    logger.warning(f"Markdown error in daily report, sending as plain text: {markdown_error}")
                    if i == 0:
                        await self.bot.send_message(
                            chat_id,
                            f"📊 Daily Analytics Report\n\n{chunk}"
                        )
                    else:
                        await self.bot.send_message(chat_id, chunk)
            
            logger.info(f"✅ Daily report sent to chat {chat_id}")
            
        except Exception as e:
            logger.error(f"Error sending daily report: {e}")
            try:
                await self.bot.send_message(
                    chat_id,
                    f"❌ Failed to generate daily report: {str(e)}"
                )
            except:
                pass

    async def start(self):
        """Start the bot."""
        logger.info("🤖 Starting Telegram Analytics Bot...")
        await self.dp.start_polling(self.bot)

    async def stop(self):
        """Stop the bot."""
        logger.info("Stopping bot...")
        await self.bot.session.close()
