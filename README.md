# Telegram Group Management Bot

A Telegram bot that automatically deletes inappropriate messages based on reactions.

## Features

- Monitor message reactions in group chats
- Messages with 1 or more 💩 reactions are deleted immediately.
- Messages with 👎 reactions are queued for daily batch deletion.
- Periodically check bot admin permissions and stop monitoring if permissions are lost
- Manual trigger for batch deletion with `/trigger_deletion`

## Requirements

- Python 3.9+
- python-telegram-bot 21.7+
- python-dotenv
- httpx

## Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/telegram_group_manager.git
cd telegram_group_manager
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
pip install "python-telegram-bot[job-queue]"
```

### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env and set your BOT_TOKEN
```

### 4. Run the bot

```bash
python bot.py
```

## Docker (Recommended)

```bash
docker compose up -d
# View logs
docker compose logs -f
```

## Usage

1. Add the bot to your Telegram group.
2. Grant admin rights with delete message permission.
3. Use `/monitor` to start reaction monitoring.
4. Use `/help` to view all commands and examples.

## Available Commands

| Command                    | Description                                                      |
|----------------------------|------------------------------------------------------------------|
| `/start`                   | Start the bot                                                    |
| `/help`                    | Show help message with command list and examples                 |
| `/monitor`                 | Enable reaction monitoring in the current group                  |
| `/stopmonitor`             | Disable reaction monitoring in the current group                 |
| `/status`                  | Show current group status and pending deletions                  |
| `/set_deletion_time HH:MM` | Schedule daily batch deletion of 💩-marked messages at given time |
| `/trigger_deletion`        | Manually trigger batch deletion now                              |

## Configuration

Adjust behavior using environment variables in `.env`:

- `BOT_TOKEN` — Telegram bot token
- `LOG_LEVEL` — Logging level (INFO, DEBUG, WARNING, ERROR)
- `LOG_DIR` — Directory for log files

## License

This project is licensed under the MIT License.
