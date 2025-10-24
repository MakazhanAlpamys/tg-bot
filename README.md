# 📊 Telegram Group Analytics Bot

An intelligent Telegram bot that monitors group conversations, stores message history, and provides AI-powered analytics using Google's Gemini 2.5 Flash model.

## ✨ Features

- 🔍 **Message Tracking**: Automatically captures and stores all group messages
- 📈 **Daily Reports**: AI-generated analytics reports sent daily at 23:59
- 🤖 **AI Q&A**: Ask questions about chat history with `/bot <question>`
- 🗄️ **Smart Storage**: Keeps 14 days of message history with automatic cleanup
- 🚀 **Auto-Initialize**: Database tables created automatically on first run
- ⏰ **Scheduled Tasks**: Daily reports and cleanup handled automatically

## 🏗️ Architecture

```
telegram/
├── main.py              # Entry point and orchestration
├── bot.py               # Bot handlers and message processing
├── db.py                # PostgreSQL database operations
├── gemini_service.py    # Gemini AI integration
├── scheduler.py         # Scheduled tasks (reports, cleanup)
├── utils.py             # Helper functions
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
└── README.md           # This file
```

## 🛠️ Tech Stack

- **Python 3.10+**
- **aiogram 3.7**: Modern async Telegram bot framework
- **asyncpg**: High-performance PostgreSQL client
- **APScheduler**: Background job scheduling
- **Google Gemini 2.5 Flash**: AI-powered analytics and Q&A
- **PostgreSQL**: Database (Neon recommended)

## 📦 Installation

### 1. Clone and Setup

```bash
# Navigate to project directory
cd telegram

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://user:password@host:5432/database
```

### 3. Get Your Credentials

#### **Telegram Bot Token**
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow instructions
3. Copy the bot token provided
4. Add your bot to your group and make it an admin

#### **Gemini API Key**
1. Visit [Google AI Studio](https://aistudio.google.com/apikey)
2. Create a new API key
3. Copy the key to your `.env` file

#### **PostgreSQL Database (Neon)**
1. Sign up at [Neon.tech](https://neon.tech)
2. Create a new project
3. Copy the connection string to `DATABASE_URL`
4. Format: `postgresql://user:password@host/database`


## 🚀 Running the Bot

### Local Development

```bash
python main.py
```

The bot will:
- ✅ Connect to PostgreSQL
- ✅ Create database tables automatically
- ✅ Clean up messages older than 14 days
- ✅ Start listening for messages
- ✅ Schedule daily reports (23:59) and cleanup (00:30)

### Logs

Logs are written to:
- **Console**: Real-time output
- **bot.log**: Persistent log file

## 🎯 Usage

### For Group Members

The bot works silently in the background:

1. **Normal messages**: Automatically tracked (no response)
2. **Ask questions**: `/bot What were the main topics today?`
3. **Daily reports**: Sent automatically at 23:59

### Example Commands

```
/bot What did we discuss about AI this week?
/bot Who was most active in the group?
/bot Summarize the key decisions made recently
```

## 📊 Database Schema

```sql
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    platform TEXT DEFAULT 'telegram',
    chat_id BIGINT,
    user_id TEXT,
    user_name TEXT,
    message_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Retention**: Only the last 14 days of messages are stored.

## ⏰ Scheduled Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| **Daily Report** | 23:59 daily | AI-generated analytics sent to group |
| **Cleanup** | 00:30 daily | Delete messages older than 14 days |

## 🌐 Deployment

### Deploy on [Render](https://render.com)

1. Create a new **Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
4. Add environment variables in Render dashboard
5. Deploy!

### Deploy on [Railway](https://railway.app)

1. Create new project
2. Connect your GitHub repo
3. Add PostgreSQL database (Railway provides one)
4. Set environment variables
5. Deploy automatically

### Deploy on [Fly.io](https://fly.io)

Create `fly.toml`:

```toml
app = "telegram-analytics-bot"

[build]
  builder = "paketobuildpacks/builder:base"

[env]
  PORT = "8080"

[[services]]
  internal_port = 8080
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = 80
```

Deploy:
```bash
fly launch
fly secrets set TELEGRAM_BOT_TOKEN=xxx GEMINI_API_KEY=xxx DATABASE_URL=xxx
fly deploy
```

## 🐛 Troubleshooting

### Bot not responding
- Check if bot token is correct
- Ensure bot is added to group as admin
- Check logs in `bot.log`

### Database connection errors
- Verify `DATABASE_URL` format
- Check if database is accessible
- Ensure asyncpg is installed

### Gemini API errors
- Verify API key is valid
- Check API quota limits
- Review error messages in logs

### Commands not working in groups
- Disable Privacy Mode via @BotFather (`/setprivacy` → Disable)
- OR use commands with bot mention: `/report@your_bot_name`
- Ensure bot is added to the group
- Make bot an admin for full functionality

## 📈 Daily Report Format

Example report generated by Gemini:

```markdown
📊 **Daily Analytics Report**

## 📊 Overview
- Total Messages: 247
- Active Users: 12
- Time Range: Oct 19 23:59 - Oct 20 23:59

## 🔥 Hot Topics

| Topic | Messages | Top Participants |
|-------|----------|------------------|
| Python Development | 89 | @john, @sarah, @mike |
| AI & Machine Learning | 67 | @alice, @bob |
| Project Planning | 45 | @team_lead, @dev1 |
| General Chat | 46 | @everyone |

## 💬 Key Highlights
- Major discussion about migrating to Python 3.11
- New AI model deployment planned for next week
- Team decided on sprint goals

## 📈 Activity Patterns
Peak activity: 2pm-4pm and 8pm-10pm

## 🎯 Insights
High engagement on technical topics. Team is actively collaborating on AI initiatives.
```

## 🔐 Security Best Practices

- ✅ Never commit `.env` file to version control
- ✅ Use environment variables for all secrets
- ✅ Restrict database access with firewall rules
- ✅ Keep dependencies updated
- ✅ Monitor API usage and set alerts

## 📝 License

MIT License - feel free to use and modify!

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 💡 Future Enhancements

- [ ] Support for multiple groups
- [ ] Web dashboard for analytics
- [ ] Export reports to PDF
- [ ] Custom report scheduling
- [ ] Sentiment analysis
- [ ] User activity leaderboards
- [ ] Media message tracking

## 📞 Support

For issues or questions:
- Check the logs first
- Review this README
- Open an issue on GitHub

---

Made with ❤️ using Python, Gemini AI, and aiogram
