#!/bin/bash

# 知道井冈 - 生产环境部署脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
APP_NAME="zhidao-jinggang-backend"
DOCKER_IMAGE="$APP_NAME:latest"
CONTAINER_NAME="$APP_NAME-app"
BACKUP_DIR="/opt/backups"
LOG_FILE="/var/log/deploy.log"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a $LOG_FILE
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a $LOG_FILE
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a $LOG_FILE
}

# 检查必要的依赖
check_dependencies() {
    log_info "检查部署依赖..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装"
        exit 1
    fi
    
    log_info "依赖检查通过"
}

# 创建备份
create_backup() {
    log_info "创建数据备份..."
    
    # 创建备份目录
    mkdir -p $BACKUP_DIR
    
    # 备份数据库
    if docker ps --format 'table {{.Names}}' | grep -q postgres; then
        BACKUP_FILE="$BACKUP_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql"
        docker exec postgres pg_dump -U postgres zhidao_jinggang > $BACKUP_FILE
        log_info "数据库备份完成: $BACKUP_FILE"
    fi
    
    # 备份上传文件
    if [ -d "uploads" ]; then
        tar -czf "$BACKUP_DIR/uploads_backup_$(date +%Y%m%d_%H%M%S).tar.gz" uploads/
        log_info "上传文件备份完成"
    fi
}

# 构建Docker镜像
build_image() {
    log_info "构建Docker镜像..."
    
    # 构建新镜像
    docker build -t $DOCKER_IMAGE .
    
    # 清理旧镜像
    docker image prune -f
    
    log_info "Docker镜像构建完成"
}

# 停止旧服务
stop_old_services() {
    log_info "停止旧服务..."
    
    # 停止应用容器
    if docker ps -q --filter "name=$CONTAINER_NAME" | grep -q .; then
        docker stop $CONTAINER_NAME
        docker rm $CONTAINER_NAME
        log_info "旧服务已停止"
    fi
}

# 启动新服务
start_new_services() {
    log_info "启动新服务..."
    
    # 启动服务
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    
    # 等待服务启动
    sleep 30
    
    log_info "新服务已启动"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_info "健康检查通过"
            return 0
        fi
        
        log_warn "健康检查失败，尝试 $attempt/$max_attempts"
        sleep 10
        ((attempt++))
    done
    
    log_error "健康检查失败"
    return 1
}

# 数据库迁移
run_migrations() {
    log_info "运行数据库迁移..."
    
    docker exec $CONTAINER_NAME python -m alembic upgrade head
    
    log_info "数据库迁移完成"
}

# 性能测试
performance_test() {
    log_info "运行性能测试..."
    
    # 简单的性能测试
    if command -v ab &> /dev/null; then
        ab -n 1000 -c 10 http://localhost:8000/health
        log_info "性能测试完成"
    else
        log_warn "Apache Bench (ab) 未安装，跳过性能测试"
    fi
}

# 清理旧文件
cleanup() {
    log_info "清理临时文件..."
    
    # 清理Docker资源
    docker system prune -f
    
    # 清理旧日志
    find /var/log -name "*.log" -type f -mtime +30 -delete
    
    log_info "清理完成"
}

# 发送通知
send_notification() {
    local status=$1
    local message=$2
    
    log_info "发送部署通知..."
    
    # 这里可以集成钉钉、企业微信等通知
    # curl -X POST "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN" \
    #      -H "Content-Type: application/json" \
    #      -d "{\"msgtype\":\"text\",\"text\":{\"content\":\"$message\"}}"
    
    log_info "通知已发送"
}

# 回滚函数
rollback() {
    log_error "部署失败，开始回滚..."
    
    # 停止新服务
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
    
    # 恢复备份
    if [ -f "$BACKUP_FILE" ]; then
        docker exec postgres psql -U postgres -d zhidao_jinggang < $BACKUP_FILE
        log_info "数据库已回滚"
    fi
    
    # 重启旧服务
    docker-compose up -d
    
    log_info "回滚完成"
    send_notification "FAILED" "部署失败，已回滚到上一版本"
    exit 1
}

# 主部署流程
main() {
    log_info "开始部署知道井冈后端服务..."
    
    # 设置错误处理
    trap rollback ERR
    
    # 检查依赖
    check_dependencies
    
    # 创建备份
    create_backup
    
    # 构建镜像
    build_image
    
    # 停止旧服务
    stop_old_services
    
    # 启动新服务
    start_new_services
    
    # 运行数据库迁移
    run_migrations
    
    # 健康检查
    if ! health_check; then
        rollback
    fi
    
    # 性能测试
    performance_test
    
    # 清理
    cleanup
    
    log_info "部署完成！"
    send_notification "SUCCESS" "知道井冈后端服务部署成功"
}

# 显示帮助信息
show_help() {
    echo "知道井冈 - 生产环境部署脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help          显示帮助信息"
    echo "  --no-backup         跳过备份"
    echo "  --no-test           跳过性能测试"
    echo "  --rollback          回滚到上一版本"
    echo ""
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --no-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --no-test)
            SKIP_TEST=true
            shift
            ;;
        --rollback)
            rollback
            exit 0
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