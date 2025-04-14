# Docker 部署指南

本文档提供了使用 Docker 部署 Telegram 群组管理机器人的详细步骤。

## 前提条件

- 安装了 Docker 和 Docker Compose
- 拥有 Telegram Bot Token（可以通过 [@BotFather](https://t.me/BotFather) 获取）
- 基本的命令行操作知识

## 安装 Docker

### Ubuntu/Debian

```bash
# 更新包索引
sudo apt update

# 安装必要的依赖
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# 添加 Docker 的官方 GPG 密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# 添加 Docker 仓库
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

# 更新包索引
sudo apt update

# 安装 Docker
sudo apt install -y docker-ce docker-ce-cli containerd.io

# 启动 Docker 服务
sudo systemctl start docker

# 设置 Docker 开机自启
sudo systemctl enable docker

# 将当前用户添加到 docker 组（可选，这样可以不使用 sudo 运行 docker 命令）
sudo usermod -aG docker $USER
```

注意：添加用户到 docker 组后，需要注销并重新登录才能生效。

### CentOS/RHEL

```bash
# 安装必要的依赖
sudo yum install -y yum-utils device-mapper-persistent-data lvm2

# 添加 Docker 仓库
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# 安装 Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io

# 启动 Docker 服务
sudo systemctl start docker

# 设置 Docker 开机自启
sudo systemctl enable docker

# 将当前用户添加到 docker 组（可选）
sudo usermod -aG docker $USER
```

### macOS

1. 下载并安装 [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
2. 启动 Docker Desktop 应用程序

### Windows

1. 下载并安装 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
2. 启动 Docker Desktop 应用程序

## 部署步骤

1. **克隆仓库**

   ```bash
   git clone https://github.com/yourusername/telegram_group_manager.git
   cd telegram_group_manager
   ```

   如果你没有 Git，也可以直接下载项目的 ZIP 文件并解压。

2. **配置环境变量**

   ```bash
   cp .env.example .env
   ```

   使用文本编辑器编辑 `.env` 文件，填入你的 Telegram Bot Token：

   ```bash
   # Linux/macOS
   nano .env
   
   # Windows
   notepad .env
   ```

   修改以下内容：

   ```
   BOT_TOKEN=your_bot_token_here
   ```

   将 `your_bot_token_here` 替换为你从 @BotFather 获取的实际 Token。

3. **使用启动脚本（推荐）**

   ```bash
   # 赋予脚本执行权限
   chmod +x start.sh
   
   # 运行脚本
   ./start.sh
   ```

   然后在菜单中选择 "1) 启动机器人"。

4. **或者直接使用 Docker Compose 命令**

   ```bash
   # 构建并启动容器
   docker compose up -d
   
   # 查看日志
   docker compose logs -f
   
   # 停止容器
   docker compose down
   ```

## 管理机器人

### 使用启动脚本

启动脚本 `start.sh` 提供了一个交互式菜单，可以方便地管理机器人：

```bash
./start.sh
```

菜单选项包括：
- 启动机器人
- 停止机器人
- 重启机器人
- 查看日志
- 重新构建并启动
- 查看状态

### 使用 Docker Compose 命令

如果你更喜欢直接使用命令行，以下是一些常用的 Docker Compose 命令：

```bash
# 启动容器
docker compose up -d

# 停止容器
docker compose down

# 重启容器
docker compose restart

# 查看日志
docker compose logs -f

# 重新构建并启动
docker compose up -d --build

# 查看容器状态
docker compose ps
```

## 更新机器人

当有新版本的机器人代码时，可以按照以下步骤更新：

```bash
# 拉取最新代码
git pull

# 重新构建并启动容器
docker compose up -d --build
```

或者使用启动脚本中的 "重新构建并启动" 选项。

## 故障排除

### 容器无法启动

检查日志以获取更多信息：

```bash
docker compose logs
```

### 机器人无法连接到 Telegram

1. 确认你的 BOT_TOKEN 是正确的
2. 检查网络连接是否正常
3. 查看容器日志以获取更多信息

### 机器人无法删除消息

确保机器人在群组中具有管理员权限，并且有删除消息的权限。

## 备份

机器人的日志存储在 `logs` 目录中。如果你需要备份这些日志，可以使用以下命令：

```bash
# 创建备份
tar -czvf telegram_bot_logs_backup.tar.gz logs/

# 恢复备份
tar -xzvf telegram_bot_logs_backup.tar.gz
```

## 安全建议

1. 不要将包含 BOT_TOKEN 的 `.env` 文件提交到版本控制系统
2. 定期更新 Docker 镜像和依赖，以修复安全漏洞
3. 使用防火墙限制服务器的访问
4. 定期备份重要数据 