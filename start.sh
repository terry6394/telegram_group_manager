#!/bin/bash

# Color definitions
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default to development environment
COMPOSE_FILE="docker-compose.yml"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}.env file not found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${RED}Please edit the .env file and enter your BOT_TOKEN before running this script.${NC}"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    echo "Installation guide: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if docker compose is available
if ! docker compose version &> /dev/null; then
    echo -e "${RED}docker compose command is not available. Please ensure you have the latest version of Docker installed.${NC}"
    echo "Installation guide: https://docs.docker.com/compose/install/"
    exit 1
fi

# Environment selection
select_environment() {
    echo -e "${GREEN}Please select the running environment:${NC}"
    echo "1) Development (docker-compose.yml)"
    echo "2) Production (docker-compose.prod.yml)"
    echo -n "Select [1/2] (default: 1): "
    read -r env_choice

    case $env_choice in
        2)
            COMPOSE_FILE="docker-compose.prod.yml"
            echo -e "${GREEN}Production environment selected.${NC}"
            ;;
        *)
            COMPOSE_FILE="docker-compose.yml"
            echo -e "${GREEN}Development environment selected.${NC}"
            ;;
    esac
}

# Show menu
show_menu() {
    echo -e "${GREEN}Telegram Group Manager Bot - Docker Management${NC}"
    echo "Current environment: ${COMPOSE_FILE}"
    echo "1) Start the bot"
    echo "2) Stop the bot"
    echo "3) Restart the bot"
    echo "4) Show logs"
    echo "5) Rebuild and start"
    echo "6) Show status"
    echo "7) Switch environment"
    echo "0) Exit"
    echo -n "Please select: "
}

# 根据环境选择 LOCK_FILE
set_lock_file() {
    if [ "$COMPOSE_FILE" = "docker-compose.prod.yml" ]; then
        LOCK_FILE="conda-linux-64.lock"
    else
        LOCK_FILE="conda-linux-aarch64.lock"
    fi
}

# Main loop
select_environment
set_lock_file

while true; do
    show_menu
    read -r choice

    case $choice in
        1)
            echo -e "${GREEN}Regenerating lock file and building image...${NC}"
            conda-lock lock --file environment.yml
            if [ "$COMPOSE_FILE" = "docker-compose.prod.yml" ]; then
                conda-lock render --kind explicit --platform linux-64 conda-lock.yml > conda-linux-64.lock
            else
                conda-lock render --kind explicit --platform linux-aarch64 conda-lock.yml > conda-linux-aarch64.lock
            fi
            set_lock_file
            docker compose -f $COMPOSE_FILE build --build-arg LOCK_FILE=$LOCK_FILE --no-cache
            docker compose -f $COMPOSE_FILE up -d
            echo -e "${GREEN}Bot started.${NC}"
            ;;
        2)
            echo -e "${YELLOW}Stopping the bot...${NC}"
            docker compose -f $COMPOSE_FILE down
            echo -e "${GREEN}Bot stopped.${NC}"
            ;;
        3)
            echo -e "${YELLOW}Restarting the bot...${NC}"
            docker compose -f $COMPOSE_FILE restart
            echo -e "${GREEN}Bot restarted.${NC}"
            ;;
        4)
            echo -e "${GREEN}Showing logs (press Ctrl+C to exit)${NC}"
            docker compose -f $COMPOSE_FILE logs -f
            ;;
        5)
            echo -e "${YELLOW}Regenerating lock file and rebuilding the bot...${NC}"
            conda-lock lock --file environment.yml
            if [ "$COMPOSE_FILE" = "docker-compose.prod.yml" ]; then
                conda-lock render --kind explicit --platform linux-64 conda-lock.yml > conda-linux-64.lock
            else
                conda-lock render --kind explicit --platform linux-aarch64 conda-lock.yml > conda-linux-aarch64.lock
            fi
            set_lock_file
            docker compose -f $COMPOSE_FILE build --build-arg LOCK_FILE=$LOCK_FILE --no-cache
            docker compose -f $COMPOSE_FILE up -d
            echo -e "${GREEN}Bot rebuilt and started.${NC}"
            ;;
        6)
            echo -e "${GREEN}Bot status:${NC}"
            docker compose -f $COMPOSE_FILE ps
            ;;
        7)
            select_environment
            set_lock_file
            ;;
        0)
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid selection, please try again.${NC}"
            ;;
    esac

    echo ""
    read -p "Press Enter to continue..."
    clear
done 