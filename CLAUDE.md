# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Telegram Group Management Bot** that monitors group messages and automatically deletes inappropriate content based on reactions and LLM classification. The bot uses the python-telegram-bot library and supports both direct Python execution and Docker deployment.

## Architecture

### Core Components

- **bot.py**: Main application logic with Telegram bot handlers and LLM integration
- **Dockerfile**: Multi-stage build using Miniconda base image
- **docker-compose.yml**: Development container orchestration
- **docker-compose.prod.yml**: Production container orchestration
- **start.sh**: Interactive deployment management script
- **healthcheck.py**: Container health monitoring

### Data Storage

- **groups.json**: Monitored group configurations (chat_id, name)
- **deletion_queue.json**: Messages queued for batch deletion
- **deletion_config.json**: LLM configuration and deletion settings
- **logs/**: Daily log files with rotation

### Key Features

1. **Reaction-based deletion**: 
   - 💩 reaction → immediate deletion
   - 👎 reaction → queued for daily batch deletion
2. **LLM-based moderation**: Uses OpenAI/Groq API for content classification
3. **Admin permission monitoring**: Automatically stops monitoring if bot loses admin rights
4. **Scheduled deletion**: Daily batch processing at configurable time
5. **Interactive management**: Admin commands for configuration

## Development Commands

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt
pip install "python-telegram-bot[job-queue]"

# Set environment variables
cp .env.example .env
# Edit .env with BOT_TOKEN

# Run directly
python bot.py
```

### Docker Development
```bash
# Build and run development container
docker compose up -d

# View logs
docker compose logs -f

# Interactive management
./start.sh
```

### Production Deployment
```bash
# Production build
docker compose -f docker-compose.prod.yml up -d --build

# Using management script
./start.sh  # Select production environment
```

### Environment Management
```bash
# Update conda environment
conda-lock lock --file environment.yml
conda-lock render --kind explicit --platform linux-64 conda-lock.yml > conda-linux-64.lock

# Activate environment
source conda_active.sh
```

## Key Configuration Files

### Environment Variables (.env)
```bash
BOT_TOKEN=your_telegram_bot_token
LOG_LEVEL=INFO
LOG_DIR=logs
```

### LLM Configuration (deletion_config.json)
```json
{
    "deletion_time": "01:30",
    "classification_prompt": "Your custom LLM prompt",
    "llm_config": {
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama3-8b-8192",
        "api_key": "your_api_key"
    }
}
```

## Bot Commands

| Command | Description | Admin Required |
|---------|-------------|----------------|
| `/start` | Initialize bot | No |
| `/help` | Show command list | No |
| `/monitor` | Start monitoring current group | No |
| `/stopmonitor` | Stop monitoring current group | No |
| `/status` | Show group status and pending deletions | No |
| `/set_deletion_time HH:MM` | Set daily deletion time | Yes |
| `/trigger_deletion` | Manual batch deletion | Yes |
| `/set_classification_prompt` | Update LLM prompt | Yes |
| `/llm_config` | Configure LLM settings | Yes |

## Testing

### LLM Configuration Test
```bash
python test_llm_config.py
```

### Health Check
```bash
# Docker health check
python healthcheck.py

# Manual check
docker compose ps
```

## File Structure

```
telegram_group_manager/
├── bot.py                 # Main bot application
├── Dockerfile            # Container configuration
├── docker-compose.yml    # Development compose
├── docker-compose.prod.yml  # Production compose
├── start.sh             # Interactive deployment script
├── healthcheck.py       # Container health monitoring
├── environment.yml      # Conda dependencies
├── conda-lock.yml       # Lock file for reproducible builds
├── conda-*.lock         # Platform-specific lock files
├── data/                # Runtime data
│   ├── groups.json      # Monitored groups
│   ├── deletion_queue.json  # Pending deletions
│   └── deletion_config.json  # LLM settings
├── logs/                # Application logs
└── .env                # Environment variables
```

## Deployment Patterns

### Development
1. Edit code locally
2. Run `docker compose up -d --build`
3. Test with test group

### Production
1. Use `start.sh` script for environment selection
2. Use production lock file (conda-linux-64.lock)
3. Configure health checks and restart policies

### Monitoring
- Check `logs/bot_YYYYMMDD.log` for detailed logs
- Use `docker compose logs -f` for real-time monitoring
- Health endpoint available via `healthcheck.py`