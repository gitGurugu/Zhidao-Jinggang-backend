#!/bin/bash
# 知道井冈后端启动脚本 - DevContainer优化版

set -e

echo "🚀 启动知道井冈后端服务..."

# 函数：检查服务连接
check_service() {
    local host=$1
    local port=$2
    local service=$3
    local timeout=${4:-30}
    
    echo "🔍 检查 $service ($host:$port)..."
    
    local count=0
    while ! timeout 3 bash -c "</dev/tcp/$host/$port" 2>/dev/null; do
        if [ $count -eq 0 ]; then
            echo "⏳ 等待 $service 启动..."
        fi
        
        if [ $((count % 10)) -eq 0 ] && [ $count -gt 0 ]; then
            echo "⏳ 仍在等待 $service... (${count}s/${timeout}s)"
        fi
        
        sleep 1
        count=$((count + 1))
        
        if [ $count -ge $timeout ]; then
            echo "❌ $service 启动超时 (${timeout}s)"
            echo "💡 解决方案:"
            echo "   1. 在主机检查服务: docker-compose -f .devcontainer/docker-compose.yml ps"
            echo "   2. 重启服务: docker-compose -f .devcontainer/docker-compose.yml restart $service"
            echo "   3. 查看日志: docker-compose -f .devcontainer/docker-compose.yml logs $service"
            return 1
        fi
    done
    
    echo "✅ $service 已就绪"
    return 0
}

# 函数：测试数据库实际连接
test_database_connection() {
    echo "🔗 测试数据库连接..."
    
    python3 -c "
import asyncio
import sys

async def test_connection():
    try:
        import asyncpg
        conn = await asyncpg.connect(
            host='db', port=5432, user='postgres', 
            password='password', database='zhidao_jinggang'
        )
        
        # 测试查询
        result = await conn.fetchval('SELECT 1')
        if result == 1:
            print('✅ 数据库连接测试成功')
        
        await conn.close()
        return True
    except ImportError:
        print('❌ asyncpg模块未安装')
        print('💡 运行: pip install -e .[dev]')
        return False
    except Exception as e:
        print(f'❌ 数据库连接失败: {e}')
        return False

if not asyncio.run(test_connection()):
    sys.exit(1)
" || {
        echo "❌ 数据库连接测试失败"
        echo "💡 可能的解决方案:"
        echo "   1. 检查数据库是否已启动"
        echo "   2. 运行: ./.devcontainer/check-db.sh"
        echo "   3. 检查数据库配置"
        return 1
    }
}

# 等待服务启动
echo "⏳ 等待服务启动..."

# 检查PostgreSQL
if ! check_service db 5432 PostgreSQL 60; then
    exit 1
fi

# 检查Redis
if ! check_service redis 6379 Redis 30; then
    exit 1
fi

# 测试数据库连接
if ! test_database_connection; then
    exit 1
fi

echo "🎉 所有服务已准备就绪"

# 检查并安装依赖
echo "📦 检查项目依赖..."
if ! python3 -c "import fastapi, uvicorn, sqlalchemy, alembic" 2>/dev/null; then
    echo "⚠️ 检测到缺少依赖，正在安装..."
    pip install -e .[dev] || {
        echo "❌ 依赖安装失败"
        echo "💡 请手动运行: pip install -e .[dev]"
        exit 1
    }
    echo "✅ 依赖安装完成"
else
    echo "✅ 依赖检查通过"
fi

# 检查.env文件配置问题
echo "🔧 检查配置文件..."
if [ -f ".env" ]; then
    # 检查.env文件是否会导致配置错误
    if python3 -c "from app.core.config import settings" 2>/dev/null; then
        echo "✅ 配置文件正常"
    else
        echo "⚠️ .env文件存在配置问题，临时重命名"
        mv .env .env.backup.$(date +%s) 2>/dev/null || true
        echo "💡 使用DevContainer环境变量和默认配置"
    fi
else
    echo "✅ 使用DevContainer环境变量和默认配置"
fi

# 运行数据库迁移
echo "🔄 运行数据库迁移..."
if command -v alembic >/dev/null 2>&1; then
    if alembic upgrade head 2>/dev/null; then
        echo "✅ 数据库迁移完成"
    else
        echo "⚠️ 数据库迁移失败，但继续启动应用"
        echo "💡 可能是首次启动或无迁移文件"
    fi
else
    echo "⚠️ alembic命令未找到，跳过迁移"
fi

# 初始化数据库（如果有CLI工具）
if [ -f "cli.py" ]; then
    echo "🔧 检查数据库初始化..."
    python3 -c "
import asyncio
from app.db.init_db import check_db_initialized

async def check():
    if not await check_db_initialized():
        print('🔄 初始化数据库...')
        from app.db.init_db import init_db
        await init_db()
        print('✅ 数据库初始化完成')
    else:
        print('✅ 数据库已初始化')

try:
    asyncio.run(check())
except ImportError:
    print('⚠️ 跳过数据库初始化')
except Exception as e:
    print(f'⚠️ 数据库初始化失败: {e}')
" 2>/dev/null || echo "⚠️ 跳过数据库初始化检查"
fi

echo ""
echo "🌟 启动FastAPI应用..."
echo "📍 API文档: http://localhost:8000/docs"
echo "📍 健康检查: http://localhost:8000/health"
echo "📍 停止服务: 按 Ctrl+C"
echo ""

# 启动应用
if command -v uvicorn >/dev/null 2>&1; then
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "❌ uvicorn命令未找到"
    echo "💡 请安装依赖: pip install -e .[dev]"
    exit 1
fi