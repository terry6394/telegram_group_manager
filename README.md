# Telegram 群组管理机器人

这是一个基于反应（Reactions）功能的Telegram群组管理机器人，可以自动删除收到负面反应的消息。

## 功能

- 监控群组中的消息反应
- 当消息收到一定数量的👎反应时，自动删除该消息
- 支持普通反应和匿名反应
- 定期检查机器人权限，确保正常运行

## 环境要求

- Python 3.9+
- python-telegram-bot 21.7+
- python-dotenv

## 安装与设置

### 方法一：直接运行

1. 克隆仓库
   ```bash
   git clone https://github.com/yourusername/telegram_group_manager.git
   cd telegram_group_manager
   ```

2. 安装依赖
   ```bash
   pip install -r requirements.txt
   pip install "python-telegram-bot[job-queue]"
   ```

3. 配置环境变量
   ```bash
   cp .env.example .env
   # 编辑.env文件，填入你的BOT_TOKEN
   ```

4. 运行机器人
   ```bash
   python bot.py
   ```

### 方法二：使用Docker（推荐）

1. 克隆仓库
   ```bash
   git clone https://github.com/yourusername/telegram_group_manager.git
   cd telegram_group_manager
   ```

2. 配置环境变量
   ```bash
   cp .env.example .env
   # 编辑.env文件，填入你的BOT_TOKEN
   ```

3. 构建并启动Docker容器
   ```bash
   docker compose up -d
   ```

4. 查看日志
   ```bash
   docker compose logs -f
   ```

## 使用方法

1. 将机器人添加到你的Telegram群组
2. 确保机器人具有管理员权限，并能够删除消息
3. 在群组中发送 `/monitor` 命令开始监控
4. 使用 `/help` 查看所有可用命令

## 可用命令

- `/start` - 启动机器人
- `/help` - 显示帮助信息
- `/monitor` - 开始监控当前群组的反应
- `/stopmonitor` - 停止监控当前群组
- `/status` - 显示机器人状态

## 配置说明

机器人的行为可以通过环境变量进行配置：

- `BOT_TOKEN` - Telegram机器人令牌
- `LOG_LEVEL` - 日志级别（INFO, DEBUG, WARNING, ERROR）
- `LOG_DIR` - 日志文件存储目录

## 许可证

[MIT](LICENSE)
