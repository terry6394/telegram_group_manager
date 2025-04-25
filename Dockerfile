# 构建阶段
FROM continuumio/miniconda3:4.12.0

WORKDIR /app

# 复制环境文件和代码
COPY environment.yml ./
COPY . .

# 创建并激活环境，安装依赖
RUN conda env update -f environment.yml --prune && \
    conda clean -afy

# 确保健康检查脚本是可执行的
RUN chmod +x healthcheck.py

# 创建日志目录
RUN mkdir -p logs

# 启动命令：激活环境并运行 bot.py
CMD ["/bin/bash", "-c", "source activate telegram-bot && python bot.py"]