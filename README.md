# RealityAi Lawyer Bot

AI-powered Telegram Legal Assistant for Indian Law — built with Python.

## Features

| Feature | Command | Description |
|---------|---------|-------------|
| Case Management | /newcase, /cases, /case, /closecase, /deletecase | Create, view, close, delete cases |
| Drafting | /draft, /linkcase | Draft legal documents (11 types) |
| Strategy | /strategy [case_id] | AI-generated legal strategy |
| Search | /search [query], /section [num] | Search law/judgments/sections |
| Evidence | /evidence, /addevidence, /evidencestatus | Track evidence per case |
| Hearings | /hearing, /cancelhearing, /calendar | Manage court dates + reminders |
| Documents | Upload PDF/Image | AI analyzes legal documents |
| Voice | Send voice note | Transcribe + legal advice |
| Summary | /summary, /weekly | Daily/weekly case overview |
| Multi-User | /register, /profile | Multiple advocates, isolated data |
| Admin | /broadcast, /stats, /export, /users | Owner-only admin commands |
| Auto Language | — | Detects Hindi/English/Hinglish |

## Setup

### 1. Get Telegram Bot Token
1. Telegram pe **@BotFather** ko message karo
2. `/newbot` → naam do → token mil jayega

### 2. Get OpenRouter API Key
1. Go to https://openrouter.ai
2. Sign up → Get API key (free credits available)

### 3. Install & Configure

```bash
# Clone/copy the project
cd realityai_lawyer

# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy env file
copy .env.example .env   # Windows
# cp .env.example .env    # Linux/Mac

# Edit .env — add your tokens
notepad .env              # Windows
nano .env                 # Linux/Mac
```

### 4. Configure .env

```env
BOT_TOKEN=your_telegram_bot_token
OWNER_ID=your_telegram_user_id   # Get from @userinfobot

# AI - OpenRouter (Primary)
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-xxx
OPENROUTER_MODEL=z-ai/glm-5-turbo

# Optional fallbacks
GEMINI_API_KEY=
GROQ_API_KEY=
```

### 5. Run

```bash
python bot.py
```

## Deploy on VPS (24/7)

### Using systemd (Recommended)

```bash
# On your VPS (Ubuntu/Debian):
sudo apt update && sudo apt install python3 python3-pip python3-venv -y

# Copy project
scp -r realityai_lawyer/ user@your-vps:~/realityai_lawyer/

# SSH into VPS
ssh user@your-vps
cd ~/realityai_lawyer

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env  # Add tokens

# Test
python3 bot.py

# Create systemd service
sudo nano /etc/systemd/system/lawyer-bot.service
```

```ini
[Unit]
Description=RealityAi Lawyer Bot
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/home/yourusername/realityai_lawyer
ExecStart=/home/yourusername/realityai_lawyer/venv/bin/python bot.py
Restart=always
RestartSec=10
Environment=PATH=/home/yourusername/realityai_lawyer/venv/bin

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable lawyer-bot
sudo systemctl start lawyer-bot
sudo systemctl status lawyer-bot
```

### Using PM2

```bash
npm install -g pm2

# Start
pm2 start bot.py --name lawyer-bot --interpreter python3

# Auto-restart on reboot
pm2 startup
pm2 save
```

## Commands Reference

| Command | Usage |
|---------|-------|
| /start | Bot start |
| /help | All commands |
| /register | Advocate registration |
| /profile | View profile |
| /newcase | Create new case |
| /cases [page] | List all cases |
| /case [ID] | Case details |
| /closecase [ID] | Close a case |
| /deletecase [ID] | Delete a case |
| /draft [type] | Draft document |
| /linkcase [ID] | Link case context |
| /strategy [ID] | Generate legal strategy |
| /search [query] | Search law/judgments |
| /section [num] | Section lookup |
| /evidence [ID] | Evidence checklist |
| /addevidence [ID] [desc] | Add evidence |
| /evidencestatus [ID] [status] | Update status |
| /hearing [ID] [date] [time] [purpose] | Set hearing |
| /cancelhearing [ID] | Cancel hearing |
| /calendar | Upcoming hearings |
| /summary | Daily summary |
| /weekly | Weekly summary |
| /broadcast [msg] | Admin: broadcast |
| /stats | Admin: bot stats |
| /export | Admin: data backup |
| /users | Admin: user list |

## Troubleshooting

- **Bot not starting**: Check BOT_TOKEN in .env
- **AI not responding**: Check OPENROUTER_API_KEY
- **Voice not working**: Install ffmpeg (`apt install ffmpeg`)
- **OCR not working**: Install Tesseract OCR (`apt install tesseract-ocr tesseract-ocr-hin`)
- **Rate limited**: Max 20 AI calls per user per hour

## License

Private project. All rights reserved.
