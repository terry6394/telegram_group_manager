# 构建阶段
FROM python:3.9-slim AS builder

WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖到指定目录
RUN pip install --no-cache-dir --user -r requirements.txt && \
    pip install --no-cache-dir --user "python-telegram-bot[job-queue]"

# 最终阶段
FROM python:3.9-slim

WORKDIR /app

# 从构建阶段复制安装的依赖
COPY --from=builder /root/.local /root/.local

# 确保 pip 安装的包在 PATH 中
ENV PATH=/root/.local/bin:$PATH

# 复制项目文件
COPY . .

# 确保健康检查脚本是可执行的
RUN chmod +x healthcheck.py

# 创建日志目录
RUN mkdir -p logs

# 运行机器人
CMD ["python", "bot.py"] 