#!/bin/bash
# DevContainer内部数据库状态检查脚本

set -e

echo "🔍 检查数据库和服务状态..."

# 函数：检查端口连通性
check_port() {
    local host=$1
    local port=$2
    local service=$3
    
    if timeout 3 bash -c "</dev/tcp/$host/$port" 2>/dev/null; then
        echo "✅ $service 端口可达 ($host:$port)"
        return 0
    else
        echo "❌ $service 端口不可达 ($host:$port)"
        return 1
    fi
}

# 函数：测试PostgreSQL实际连接
test_postgres() {
    python3 -c "
import asyncio
import sys

async def test_db():
    try:
        import asyncpg
        conn = await asyncpg.connect(
            host='db', port=5432, user='postgres', 
            password='password', database='zhidao_jinggang'
        )
        result = await conn.fetchval('SELECT version()')
        print('✅ PostgreSQL连接正常')
        print(f'📋 版本: {result[:50]}...')
        
        # 检查表是否存在
        tables = await conn.fetch(\"\"\"
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
        \"\"\")
        if tables:
            print(f'📊 已有 {len(tables)} 个数据表')
            for table in tables[:3]:  # 显示前3个表
                print(f'   - {table[\"tablename\"]}')
        else:
            print('📊 数据库为空，可能需要运行迁移')
            
        await conn.close()
        return True
    except ImportError:
        print('⚠️ asyncpg模块未安装')
        return False
    except Exception as e:
        print(f'❌ 数据库连接失败: {e}')
        if 'password authentication failed' in str(e):
            print('💡 密码认证失败，请检查数据库配置')
        elif 'does not exist' in str(e):
            print('💡 数据库不存在，可能需要初始化')
        else:
            print('💡 数据库可能还在初始化中')
        return False

if asyncio.run(test_db()):
    sys.exit(0)
else:
    sys.exit(1)
"
}

# 函数：测试Redis连接
test_redis() {
    python3 -c "
import socket
import sys

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('redis', 6379))
    sock.send(b'PING\r\n')
    response = sock.recv(1024)
    sock.close()
    
    if b'PONG' in response:
        print('✅ Redis响应正常')
        
        # 测试Redis基本操作
        try:
            import redis
            r = redis.Redis(host='redis', port=6379, db=0)
            r.set('test_key', 'test_value')
            value = r.get('test_key')
            r.delete('test_key')
            print('✅ Redis读写操作正常')
        except ImportError:
            print('⚠️ redis-py模块未安装，但连接正常')
        except Exception as e:
            print(f'⚠️ Redis操作测试失败: {e}')
        return True
    else:
        print(f'⚠️ Redis响应异常: {response}')
        return False
except Exception as e:
    print(f'❌ Redis连接失败: {e}')
    return False
"
}

# 主检查流程
echo "🗄️ 检查PostgreSQL..."
if check_port db 5432 PostgreSQL; then
    test_postgres
else
    echo "💡 请在主机执行: docker-compose -f .devcontainer/docker-compose.yml up -d db"
fi

echo ""
echo "💾 检查Redis..."
if check_port redis 6379 Redis; then
    test_redis
else
    echo "💡 请在主机执行: docker-compose -f .devcontainer/docker-compose.yml up -d redis"
fi

echo ""
echo "📋 开发环境信息:"
echo "  🐍 Python: $(python3 --version)"
echo "  👤 当前用户: $(whoami)"
echo "  📁 工作目录: $(pwd)"
echo "  🏠 HOME: $HOME"
echo "  🌐 DevContainer网络模式"

# 检查关键依赖
echo ""
echo "📦 检查Python依赖:"
python3 -c "
packages = ['fastapi', 'uvicorn', 'sqlalchemy', 'alembic', 'asyncpg', 'redis']
for pkg in packages:
    try:
        __import__(pkg)
        print(f'✅ {pkg}')
    except ImportError:
        print(f'❌ {pkg} (未安装)')
"

echo ""
echo "🏁 检查完成"