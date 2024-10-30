# Server Archive Bot

## Overview
- Archives image links from specified Discord channels and threads
- Downloads and organizes attachments by channel and thread
- If kept running, will archive new images as they are posted

## Project Structure
```bash
server-archive-bot/
├── cogs/
│   └── events.py
├── config/
│   ├── bot_config.yaml
│   └── logging_config.yaml
├── logs/             # Auto-generated
│   ├── bot.log       # Auto-generated
│   └── errors.log    # Auto-generated
├── venv/             # Auto-generated
├── bot.py
├── config.py
├── requirements.txt
└── run.bat
```
## Setup and Configuration

1. Ensure you have Python 3.12 or later installed (May work with earlier versions, but not tested)

2. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd server-archive-bot
   ```
3. **Configure the bot:**
   - Create a `config/bot_config.yaml` file with the following structure:
     - `token`: Your Discord bot token
     - `folder_path`: Path where archived data will be stored
     - `channel_ids`: List of channel IDs to monitor
     - `archiving`: Set to `True` to enable archiving of past images

4. **Configure logging:**
   - Open `config/logging_config.yaml` to adjust logging settings if necessary

5. **Running the Bot**
Run the bot using the `run.bat` script, which automates the setup and execution process:
```bash
run.bat
```

## Autostart with Windows Fluent Terminal

To set up autostart using Windows Fluent Terminal:

1. Add a new profile in the terminal settings
2. Configure the command line:
   - Command Line: `C:\path\to\your\run.bat
   - Starting Directory: `C:\path\to\your\bot\directory`

## Notes

- Logs are stored in the logs/ folder with rotation
- The bot requires the message content intent
