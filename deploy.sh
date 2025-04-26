#!/bin/bash

set -e

# 配置
ENV_NAME="telegram_group_manager_env"
REPO_DIR="$(pwd)"
LOG_FILE="$REPO_DIR/run.log"

# 1. 检查 conda 是否已安装
if ! command -v conda &> /dev/null; then
    echo "Conda 未安装，请先安装 Miniconda 或 Anaconda。"
    exit 1
fi

# 2. 拉取最新代码（假设已是 git 仓库）
echo "拉取最新代码..."
git pull || echo "警告：git pull 失败，请手动检查仓库状态。"

# 3. 检查并更新 conda 环境
source "$(conda info --base)/etc/profile.d/conda.sh"
if conda info --envs | grep -q "$ENV_NAME"; then
    echo "检测到 conda 环境 $ENV_NAME，尝试更新依赖..."
    conda env update -f environment.yml -n $ENV_NAME
else
    echo "未检测到 conda 环境 $ENV_NAME，正在创建..."
    conda env create -f environment.yml -n $ENV_NAME
fi

# 4. 激活环境
conda activate $ENV_NAME

# 5. 检查 .env 文件
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo ".env 已生成，请手动填写 BOT_TOKEN 等敏感信息后重新运行脚本。"
        exit 1
    else
        echo ".env.example 不存在，请手动创建 .env 文件。"
        exit 1
    fi
fi

# 6. 杀死已运行的 bot.py
PID=$(pgrep -f "python bot.py" || true)
if [ -n "$PID" ]; then
    echo "检测到已运行的 bot.py，正在终止..."
    kill $PID
    sleep 2
fi

# 7. 启动 bot
nohup python bot.py > "$LOG_FILE" 2>&1 &
echo "Bot 已在后台启动，日志见 $LOG_FILE"
