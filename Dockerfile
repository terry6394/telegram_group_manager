# 构建阶段
FROM continuumio/miniconda3:4.12.0

WORKDIR /app

# 多平台自动构建支持
ARG LOCK_FILE=conda-linux-64.lock
COPY ${LOCK_FILE} ./
COPY . .

RUN conda create -n telegram-bot --file ${LOCK_FILE} && \
    conda clean -afy

# 确保健康检查脚本是可执行的
RUN chmod +x healthcheck.py

# 创建日志目录
RUN mkdir -p logs

# 启动命令：激活环境并运行 bot.py
CMD ["/bin/bash", "-c", "source activate telegram-bot && python bot.py"]