#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 默认使用开发环境配置
COMPOSE_FILE="docker-compose.yml"

# 检查.env文件是否存在
if [ ! -f .env ]; then
    echo -e "${YELLOW}未找到.env文件，正在从模板创建...${NC}"
    cp .env.example .env
    echo -e "${RED}请编辑.env文件，填入你的BOT_TOKEN后再运行此脚本${NC}"
    exit 1
fi

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker未安装，请先安装Docker${NC}"
    echo "安装说明: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查docker compose是否可用
if ! docker compose version &> /dev/null; then
    echo -e "${RED}docker compose 命令不可用，请确保安装了最新版本的Docker${NC}"
    echo "安装说明: https://docs.docker.com/compose/install/"
    exit 1
fi

# 选择环境
select_environment() {
    echo -e "${GREEN}请选择运行环境:${NC}"
    echo "1) 开发环境 (docker-compose.yml)"
    echo "2) 生产环境 (docker-compose.prod.yml)"
    echo -n "请选择 [1/2] (默认: 1): "
    read -r env_choice
    
    case $env_choice in
        2)
            COMPOSE_FILE="docker-compose.prod.yml"
            echo -e "${GREEN}已选择生产环境配置${NC}"
            ;;
        *)
            COMPOSE_FILE="docker-compose.yml"
            echo -e "${GREEN}已选择开发环境配置${NC}"
            ;;
    esac
}

# 显示菜单
show_menu() {
    echo -e "${GREEN}Telegram 群组管理机器人 - Docker管理${NC}"
    echo "当前环境: ${COMPOSE_FILE}"
    echo "1) 启动机器人"
    echo "2) 停止机器人"
    echo "3) 重启机器人"
    echo "4) 查看日志"
    echo "5) 重新构建并启动"
    echo "6) 查看状态"
    echo "7) 切换环境"
    echo "0) 退出"
    echo -n "请选择: "
}

# 主循环
select_environment

while true; do
    show_menu
    read -r choice

    case $choice in
        1)
            echo -e "${GREEN}正在启动机器人...${NC}"
            docker compose -f $COMPOSE_FILE up -d
            echo -e "${GREEN}机器人已启动${NC}"
            ;;
        2)
            echo -e "${YELLOW}正在停止机器人...${NC}"
            docker compose -f $COMPOSE_FILE down
            echo -e "${GREEN}机器人已停止${NC}"
            ;;
        3)
            echo -e "${YELLOW}正在重启机器人...${NC}"
            docker compose -f $COMPOSE_FILE restart
            echo -e "${GREEN}机器人已重启${NC}"
            ;;
        4)
            echo -e "${GREEN}显示日志 (按Ctrl+C退出)${NC}"
            docker compose -f $COMPOSE_FILE logs -f
            ;;
        5)
            echo -e "${YELLOW}正在重新构建并启动机器人...${NC}"
            docker compose -f $COMPOSE_FILE up -d --build
            echo -e "${GREEN}机器人已重新构建并启动${NC}"
            ;;
        6)
            echo -e "${GREEN}机器人状态:${NC}"
            docker compose -f $COMPOSE_FILE ps
            ;;
        7)
            select_environment
            ;;
        0)
            echo -e "${GREEN}再见!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}无效选择，请重试${NC}"
            ;;
    esac
    
    echo ""
    read -p "按Enter键继续..."
    clear
done 