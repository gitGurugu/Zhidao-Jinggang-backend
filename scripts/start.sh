#!/bin/bash

# 知道井冈 - 企业级FastAPI后端服务启动脚本（生产环境）

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Python版本
check_python_version() {
    log_info "检查Python版本..."
    python_version=$(python --version 2>&1 | awk '{print $2}')
    
    if [[ "$python_version" < "3.8" ]]; then
        log_error "Python版本过低，需要3.8+，当前版本: $python_version"
        exit 1
    fi
    
    log_info "Python版本: $python_version ✓"
}

# 检查环境变量
check_environment() {
    log_info "检查环境变量..."
    
    # 检查必需的环境变量
    required_vars=("DATABASE_URL" "SECRET_KEY" "REDIS_URL")
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            log_error "缺少环境变量: $var"
            exit 1
        fi
    done
    
    log_info "环境变量检查通过 ✓"
}

# 检查数据库连接
check_database() {
    log_info "检查数据库连接..."
    
    # 等待数据库准备就绪
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if python -c "
import asyncio
import asyncpg
import os
from urllib.parse import urlparse

async def check_db():
    try:
        url = os.environ['DATABASE_URL']
        parsed = urlparse(url)
        conn = await asyncpg.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:]
        )
        await conn.close()
        return True
    except Exception as e:
        print(f'数据库连接失败: {e}')
        return False

result = asyncio.run(check_db())
exit(0 if result else 1)
" 2>/dev/null; then
            log_info "数据库连接成功 ✓"
            return 0
        fi
        
        log_warn "数据库连接失败，重试 $attempt/$max_attempts"
        sleep 2
        ((attempt++))
    done
    
    log_error "数据库连接超时"
    return 1
}

# 检查Redis连接
check_redis() {
    log_info "检查Redis连接..."
    
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if python -c "
import redis
import os
from urllib.parse import urlparse

try:
    url = os.environ['REDIS_URL']
    parsed = urlparse(url)
    r = redis.Redis(
        host=parsed.hostname,
        port=parsed.port or 6379,
        password=parsed.password,
        decode_responses=True
    )
    r.ping()
    print('Redis连接成功')
    exit(0)
except Exception as e:
    print(f'Redis连接失败: {e}')
    exit(1)
" 2>/dev/null; then
            log_info "Redis连接成功 ✓"
            return 0
        fi
        
        log_warn "Redis连接失败，重试 $attempt/$max_attempts"
        sleep 2
        ((attempt++))
    done
    
    log_error "Redis连接超时"
    return 1
}

# 运行数据库迁移
run_migrations() {
    log_info "运行数据库迁移..."
    
    # 检查是否有待迁移的更改
    if python -m alembic current &>/dev/null; then
        python -m alembic upgrade head
        log_info "数据库迁移完成 ✓"
    else
        log_warn "数据库迁移跳过（首次运行或无变更）"
    fi
}

# 预热应用
warmup_application() {
    log_info "预热应用..."
    
    # 预加载模型和缓存
    python -c "
import asyncio
from app.main import app
from app.core.config import settings

async def warmup():
    print('预热应用组件...')
    # 这里可以添加应用预热逻辑
    print('应用预热完成')

asyncio.run(warmup())
" 2>/dev/null || log_warn "应用预热失败"
    
    log_info "应用预热完成 ✓"
}

# 启动应用
start_application() {
    log_info "启动知道井冈后端服务..."
    
    # 生产环境配置
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    
    # 启动参数
    HOST=${HOST:-0.0.0.0}
    PORT=${PORT:-8000}
    WORKERS=${WORKERS:-4}
    
    log_info "启动配置:"
    log_info "  主机: $HOST"
    log_info "  端口: $PORT"
    log_info "  工作进程: $WORKERS"
    
    # 使用Gunicorn启动（生产环境推荐）
    if command -v gunicorn &> /dev/null; then
        log_info "使用Gunicorn启动..."
        exec gunicorn app.main:app \
            --bind $HOST:$PORT \
            --workers $WORKERS \
            --worker-class uvicorn.workers.UvicornWorker \
            --max-requests 1000 \
            --max-requests-jitter 50 \
            --timeout 60 \
            --keep-alive 5 \
            --log-level info \
            --access-logfile - \
            --error-logfile - \
            --log-config logging.conf
    else
        log_warn "Gunicorn未安装，使用Uvicorn启动..."
        exec uvicorn app.main:app \
            --host $HOST \
            --port $PORT \
            --workers $WORKERS \
            --log-level info \
            --access-log \
            --no-use-colors
    fi
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 等待服务启动
    sleep 5
    
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:${PORT:-8000}/health &> /dev/null; then
            log_info "健康检查通过 ✓"
            return 0
        fi
        
        log_warn "健康检查失败，重试 $attempt/$max_attempts"
        sleep 2
        ((attempt++))
    done
    
    log_error "健康检查失败"
    return 1
}

# 清理函数
cleanup() {
    log_info "清理临时文件..."
    
    # 清理Python缓存
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    
    # 清理日志文件
    if [ -d "logs" ]; then
        find logs -name "*.log" -type f -mtime +7 -delete
    fi
    
    log_info "清理完成 ✓"
}

# 信号处理
graceful_shutdown() {
    log_info "收到关闭信号，正在优雅关闭..."
    
    # 停止接收新请求
    log_info "停止接收新请求..."
    
    # 等待现有请求完成
    log_info "等待现有请求完成..."
    sleep 5
    
    # 清理资源
    cleanup
    
    log_info "服务已关闭"
    exit 0
}

# 设置信号处理
trap graceful_shutdown SIGTERM SIGINT

# 显示帮助信息
show_help() {
    echo "知道井冈 - 生产环境启动脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help          显示帮助信息"
    echo "  --skip-migrations   跳过数据库迁移"
    echo "  --skip-warmup       跳过应用预热"
    echo "  --health-check      仅执行健康检查"
    echo ""
    echo "环境变量:"
    echo "  HOST                服务器主机地址 (默认: 0.0.0.0)"
    echo "  PORT                服务器端口 (默认: 8000)"
    echo "  WORKERS             工作进程数 (默认: 4)"
    echo "  DATABASE_URL        数据库连接URL"
    echo "  REDIS_URL           Redis连接URL"
    echo "  SECRET_KEY          应用密钥"
    echo ""
}

# 主函数
main() {
    log_info "=== 知道井冈后端服务启动 ==="
    
    # 检查环境
    check_python_version
    check_environment
    
    # 检查服务依赖
    check_database
    check_redis
    
    # 运行数据库迁移
    if [[ "$SKIP_MIGRATIONS" != "true" ]]; then
        run_migrations
    fi
    
    # 应用预热
    if [[ "$SKIP_WARMUP" != "true" ]]; then
        warmup_application
    fi
    
    # 清理临时文件
    cleanup
    
    # 启动应用
    start_application
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --skip-migrations)
            SKIP_MIGRATIONS=true
            shift
            ;;
        --skip-warmup)
            SKIP_WARMUP=true
            shift
            ;;
        --health-check)
            health_check
            exit $?
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 执行主流程
main 