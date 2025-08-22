#!/bin/bash
# 环境快速检查脚本 - DevContainer开发环境状态检查

set -e

echo "⚡ 环境状态检查..."

# 检查服务连接
check_service() {
    local host=$1
    local port=$2
    local name=$3
    
    if timeout 2 bash -c "</dev/tcp/$host/$port" 2>/dev/null; then
        echo "✅ $name"
        return 0
    else
        echo "❌ $name"
        return 1
    fi
}

# 检查应用状态
check_app() {
    if curl -f http://localhost:8000/health 2>/dev/null >/dev/null; then
        echo "✅ FastAPI应用"
        return 0
    else
        echo "❌ FastAPI应用 (未启动)"
        return 1
    fi
}

# 并行检查服务
echo "🌐 服务状态:"
db_ok=false
redis_ok=false
app_ok=false

check_service db 5432 "PostgreSQL   " && db_ok=true
check_service redis 6379 "Redis        " && redis_ok=true
check_app && app_ok=true

# 快速依赖检查
echo ""
echo "📦 核心依赖:"
deps_ok=true
python3 -c "
import sys
deps = ['fastapi', 'uvicorn', 'sqlalchemy', 'alembic', 'asyncpg']
missing = []
for dep in deps:
    try:
        __import__(dep)
        print(f'✅ {dep}')
    except ImportError:
        print(f'❌ {dep}')
        missing.append(dep)
if missing:
    sys.exit(1)
" 2>/dev/null || deps_ok=false

# 项目结构检查
echo ""
echo "📊 项目结构:"
[ -f "alembic.ini" ] && echo "✅ Alembic配置" || echo "❌ Alembic配置"
[ -f "pyproject.toml" ] && echo "✅ 项目配置" || echo "❌ 项目配置"
[ -d "app" ] && echo "✅ 应用目录" || echo "❌ 应用目录"

# 总结和建议
echo ""
echo "📋 状态总结:"
if $db_ok && $redis_ok && $deps_ok; then
    echo "✅ 环境就绪 - 可以开始开发"
    if ! $app_ok; then
        echo "💡 运行应用: ./.devcontainer/start.sh"
    fi
else
    echo "❌ 环境存在问题:"
    if ! $db_ok || ! $redis_ok; then
        echo "  - 服务未启动，在主机运行: docker-compose -f .devcontainer/docker-compose.yml up -d"
    fi
    if ! $deps_ok; then
        echo "  - 依赖缺失，运行: pip install -e .[dev]"
    fi
    echo "💡 详细检查: ./.devcontainer/check-db.sh"
fi

