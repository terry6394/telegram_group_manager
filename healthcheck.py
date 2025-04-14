#!/usr/bin/env python3
"""
健康检查脚本，用于Docker容器的健康检查
"""
import os
import sys
import logging
import psutil
import time

# 配置日志
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("healthcheck")

def check_process_running(process_name="python"):
    """检查指定进程是否在运行"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # 检查命令行是否包含bot.py
            if proc.info['name'] == process_name or \
               (proc.info['cmdline'] and any('bot.py' in cmd for cmd in proc.info['cmdline'])):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def main():
    """主函数"""
    # 检查机器人进程是否在运行
    if not check_process_running():
        logger.error("机器人进程未运行")
        sys.exit(1)
    
    # 检查日志文件是否最近有更新
    log_dir = os.getenv("LOG_DIR", "logs")
    if os.path.exists(log_dir):
        log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
        if log_files:
            # 获取最新的日志文件
            latest_log = max(log_files, key=lambda x: os.path.getmtime(os.path.join(log_dir, x)))
            log_path = os.path.join(log_dir, latest_log)
            
            # 检查日志文件的最后修改时间
            last_modified = os.path.getmtime(log_path)
            current_time = time.time()
            
            # 如果日志文件超过1小时没有更新，可能表示机器人已经停止工作
            if current_time - last_modified > 3600:
                logger.warning("日志文件超过1小时未更新，机器人可能已停止工作")
                sys.exit(1)
    
    logger.info("健康检查通过")
    sys.exit(0)

if __name__ == "__main__":
    main() 