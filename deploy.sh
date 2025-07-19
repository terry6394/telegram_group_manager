#!/bin/bash

# Telegram Group Manager - 部署与卸载工具
# 支持部署、卸载、重启、状态检查等功能

set -e

# 配置变量
SCRIPT_NAME="telegram_group_manager"
ENV_NAME="${SCRIPT_NAME}_env"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$REPO_DIR/logs/deploy.log"
PID_FILE="$REPO_DIR/logs/${SCRIPT_NAME}.pid"
VENV_DIR="$REPO_DIR/venv"

# 颜色输出 - 检测是否支持彩色
if [ -t 1 ] && [ "$TERM" != "dumb" ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

# 日志函数
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

# 显示帮助信息
show_help() {
    cat << EOF
Telegram Group Manager - 部署与卸载工具

用法:
    $0 [命令] [选项]

命令:
    install     安装并启动服务（首次部署）
    start       启动服务
    stop        停止服务
    restart     重启服务
    status      查看服务状态
    update      更新代码并重启
    uninstall   完全卸载（包括环境）
    logs        查看实时日志
    help        显示此帮助信息

选项:
    -f, --force   强制操作（跳过确认）

示例:
    $0 install          # 首次安装
    $0 start            # 启动服务
    $0 stop             # 停止服务
    $0 restart          # 重启服务
    $0 uninstall        # 完全卸载
    $0 logs             # 查看日志

EOF
}

# 检查依赖
check_dependencies() {
    log "检查系统依赖..."
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        error "Python3 未安装"
        exit 1
    fi
    
    # 检查 pip
    if ! command -v pip3 &> /dev/null; then
        error "pip3 未安装"
        exit 1
    fi
    
    info "系统依赖检查完成"
}

# 创建必要的目录
create_directories() {
    mkdir -p "$REPO_DIR/logs"
    mkdir -p "$REPO_DIR/data"
}

# 获取进程PID
get_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE"
    else
        pgrep -f "python.*bot.py" || echo ""
    fi
}

# 检查服务状态
check_status() {
    local pid=$(get_pid)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        echo "running"
    else
        echo "stopped"
    fi
}

# 安装服务
install_service() {
    log "开始安装 Telegram Group Manager..."
    
    # 检查 .env 文件
    if [ ! -f "$REPO_DIR/.env" ]; then
        if [ -f "$REPO_DIR/.env.example" ]; then
            cp "$REPO_DIR/.env.example" "$REPO_DIR/.env"
            warning ".env 文件已创建，请编辑后重新运行安装"
            info "请执行: nano $REPO_DIR/.env"
            exit 1
        else
            error ".env.example 不存在，请手动创建 .env 文件"
            exit 1
        fi
    fi
    
    # 创建虚拟环境
    if [ ! -d "$VENV_DIR" ]; then
        log "创建 Python 虚拟环境..."
        python3 -m venv "$VENV_DIR"
    fi
    
    # 安装 Python 依赖
    log "安装 Python 依赖..."
    
    # 使用 requirements.txt（推荐方式）
    if [ -f "$REPO_DIR/requirements.txt" ]; then
        source "$VENV_DIR/bin/activate"
        pip install --upgrade pip
        pip install -r "$REPO_DIR/requirements.txt"
        log "依赖安装完成（使用 requirements.txt）"
    else
        error "未找到 requirements.txt 文件"
        exit 1
    fi
    
    # 启动服务
    start_service
    
    log "安装完成！服务已启动"
    info "查看日志: $0 logs"
    info "查看状态: $0 status"
}

# 启动服务
start_service() {
    log "启动 Telegram Group Manager..."
    
    if [ "$(check_status)" = "running" ]; then
        warning "服务已在运行中"
        $0 status
        return 0
    fi
    
    # 根据环境类型启动
    if [ -f "$REPO_DIR/requirements.txt" ]; then
        # 使用虚拟环境
        source "$VENV_DIR/bin/activate"
        nohup python "$REPO_DIR/bot.py" > "$LOG_FILE" 2>&1 &
    elif [ -f "$REPO_DIR/environment.yml" ]; then
        # 使用 conda 环境
        source "$(conda info --base)/etc/profile.d/conda.sh"
        conda activate "$ENV_NAME"
        nohup python "$REPO_DIR/bot.py" > "$LOG_FILE" 2>&1 &
    else
        error "未找到依赖配置文件"
        exit 1
    fi
    
    echo $! > "$PID_FILE"
    
    sleep 2
    
    if [ "$(check_status)" = "running" ]; then
        log "服务启动成功 (PID: $(get_pid))"
    else
        error "服务启动失败"
        exit 1
    fi
}

# 停止服务
stop_service() {
    log "停止 Telegram Group Manager..."
    
    local pid=$(get_pid)
    if [ -z "$pid" ] || [ "$pid" = "" ]; then
        warning "服务未运行"
        return 0
    fi
    
    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid"
        sleep 2
        
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null || true
        fi
        
        rm -f "$PID_FILE"
        log "服务已停止"
    else
        warning "进程 $pid 不存在"
        rm -f "$PID_FILE"
    fi
}

# 重启服务
restart_service() {
    log "重启 Telegram Group Manager..."
    stop_service
    sleep 2
    start_service
}

# 更新服务
update_service() {
    log "更新服务..."
    
    # 拉取最新代码
    log "拉取最新代码..."
    git pull origin main
    
    # 重启服务
    restart_service
    
    log "更新完成"
}

# 查看状态
show_status() {
    echo "=== Telegram Group Manager 状态 ==="
    
    local status=$(check_status)
    local pid=$(get_pid)
    
    if [ "$status" = "running" ]; then
        echo "状态: 运行中 (PID: $pid)"
        echo "日志文件: $LOG_FILE"
        echo "配置文件: $REPO_DIR/.env"
    else
        echo "状态: 已停止"
    fi
    
    # 显示最近的日志
    if [ -f "$LOG_FILE" ]; then
        echo ""
        echo "最近日志:"
        tail -n 5 "$LOG_FILE" 2>/dev/null || echo "无日志"
    fi
}

# 查看日志
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        warning "日志文件不存在"
    fi
}

# 卸载服务
uninstall_service() {
    echo "警告：这将完全卸载 Telegram Group Manager"
    echo "此操作将："
    echo "  - 停止并删除服务"
    echo "  - 删除虚拟环境"
    echo "  - 保留配置文件和数据"
    
    read -p "确认卸载? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "开始卸载..."
        
        # 停止服务
        stop_service
        
        # 删除虚拟环境
        if [ -d "$VENV_DIR" ]; then
            rm -rf "$VENV_DIR"
            log "虚拟环境已删除"
        fi
        
        # 清理日志（可选）
        # rm -rf "$REPO_DIR/logs"
        
        log "卸载完成！"
        info "配置文件和数据已保留，如需重新安装请运行: $0 install"
    else
        log "卸载已取消"
    fi
}

# 主函数
main() {
    # 创建必要的目录
    create_directories
    
    # 检查参数
    case "${1:-help}" in
        install)
            check_dependencies
            install_service
            ;;
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        status)
            show_status
            ;;
        update)
            update_service
            ;;
        uninstall)
            uninstall_service
            ;;
        logs)
            show_logs
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 设置执行权限
chmod +x "$0"

# 运行主程序
main "$@"