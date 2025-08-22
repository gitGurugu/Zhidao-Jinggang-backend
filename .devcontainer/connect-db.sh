#!/bin/bash
# DevContainer数据库连接工具

set -e

echo "🗄️ 数据库连接工具..."

# 检查数据库连接
check_db_connection() {
    python3 -c "
import asyncio
import sys

async def check():
    try:
        import asyncpg
        conn = await asyncpg.connect(
            host='db', port=5432, user='postgres', 
            password='password', database='zhidao_jinggang'
        )
        await conn.close()
        return True
    except Exception as e:
        print(f'❌ 数据库连接失败: {e}')
        return False

if not asyncio.run(check()):
    sys.exit(1)
" || {
        echo "❌ 数据库未连接或不可用"
        echo "💡 请先运行: ./.devcontainer/check-db.sh"
        echo "💡 或在主机启动: docker-compose -f .devcontainer/docker-compose.yml up -d db"
        exit 1
    }
}

# 主菜单
show_menu() {
    echo ""
    echo "🔗 数据库连接信息:"
    echo "  主机: db (容器内) / localhost:15432 (主机)"
    echo "  数据库: zhidao_jinggang"
    echo "  用户: postgres"
    echo "  密码: password"
    echo ""
    echo "📋 请选择操作:"
    echo "  1) 交互式数据库查询"
    echo "  2) 执行单个SQL语句"
    echo "  3) 显示数据库信息"
    echo "  4) 显示所有表"
    echo "  5) 显示表结构"
    echo "  6) 查看迁移历史"
    echo "  7) 数据库备份信息"
    echo "  8) 退出"
    echo ""
}

# 交互式查询
interactive_query() {
    echo "🚀 启动交互式数据库查询..."
    echo "💡 可用命令示例:"
    echo "   SELECT * FROM users LIMIT 10;"
    echo "   \\d users  (显示表结构)"
    echo "   \\dt       (显示所有表)"
    echo "   \\q        (退出)"
    echo ""
    
    python3 -c "
import asyncio
import asyncpg

async def interactive():
    conn = await asyncpg.connect(
        host='db', port=5432, user='postgres', 
        password='password', database='zhidao_jinggang'
    )
    
    print('已连接到数据库。输入SQL查询 (输入 quit 或 exit 退出):')
    
    while True:
        try:
            query = input('zhidao_jinggang=# ')
            if query.lower().strip() in ['quit', 'exit', '\\q']:
                break
            if query.strip() == '':
                continue
                
            if query.strip().lower().startswith('select') or query.strip().lower().startswith('show'):
                results = await conn.fetch(query)
                if results:
                    # 打印列名
                    if results:
                        columns = list(results[0].keys())
                        print(' | '.join(columns))
                        print('-' * (len(' | '.join(columns))))
                        for row in results:
                            print(' | '.join(str(row[col]) for col in columns))
                else:
                    print('查询无结果')
            else:
                result = await conn.execute(query)
                print(f'执行完成: {result}')
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f'错误: {e}')
    
    await conn.close()
    print('断开数据库连接')

asyncio.run(interactive())
"
}

# 执行单个SQL
execute_sql() {
    read -p "📝 请输入SQL语句: " sql
    if [ -z "$sql" ]; then
        echo "❌ SQL语句不能为空"
        return
    fi
    
    echo "🔍 执行SQL: $sql"
    python3 -c "
import asyncio
import asyncpg

async def execute():
    conn = await asyncpg.connect(
        host='db', port=5432, user='postgres', 
        password='password', database='zhidao_jinggang'
    )
    
    try:
        if '$sql'.lower().strip().startswith('select'):
            results = await conn.fetch('$sql')
            if results:
                columns = list(results[0].keys())
                print(' | '.join(columns))
                print('-' * (len(' | '.join(columns))))
                for row in results:
                    print(' | '.join(str(row[col]) for col in columns))
                print(f'\\n返回 {len(results)} 行')
            else:
                print('查询无结果')
        else:
            result = await conn.execute('$sql')
            print(f'执行结果: {result}')
    except Exception as e:
        print(f'执行失败: {e}')
    finally:
        await conn.close()

asyncio.run(execute())
"
}

# 显示数据库信息
show_db_info() {
    echo "📊 数据库信息:"
    python3 -c "
import asyncio
import asyncpg

async def show_info():
    conn = await asyncpg.connect(
        host='db', port=5432, user='postgres', 
        password='password', database='zhidao_jinggang'
    )
    
    # 基本信息
    version = await conn.fetchval('SELECT version()')
    print(f'PostgreSQL版本: {version}')
    
    db_name = await conn.fetchval('SELECT current_database()')
    print(f'当前数据库: {db_name}')
    
    user = await conn.fetchval('SELECT current_user')
    print(f'当前用户: {user}')
    
    # 数据库大小
    size = await conn.fetchval(\"\"\"
        SELECT pg_size_pretty(pg_database_size(current_database()))
    \"\"\")
    print(f'数据库大小: {size}')
    
    await conn.close()

asyncio.run(show_info())
"
}

# 显示所有表
show_tables() {
    echo "📋 数据库表列表:"
    python3 -c "
import asyncio
import asyncpg

async def show_tables():
    conn = await asyncpg.connect(
        host='db', port=5432, user='postgres', 
        password='password', database='zhidao_jinggang'
    )
    
    tables = await conn.fetch(\"\"\"
        SELECT 
            schemaname as schema,
            tablename as table_name,
            tableowner as owner
        FROM pg_tables 
        WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
        ORDER BY schemaname, tablename
    \"\"\")
    
    if tables:
        print('Schema | 表名 | 所有者')
        print('-' * 40)
        for table in tables:
            print(f\"{table['schema']} | {table['table_name']} | {table['owner']}\")
        print(f'\\n共 {len(tables)} 个表')
    else:
        print('数据库中没有用户表')
        print('💡 可能需要运行迁移: alembic upgrade head')
    
    await conn.close()

asyncio.run(show_tables())
"
}

# 显示表结构
show_table_structure() {
    read -p "📝 请输入表名: " table_name
    if [ -z "$table_name" ]; then
        echo "❌ 表名不能为空"
        return
    fi
    
    echo "🔍 表结构: $table_name"
    python3 -c "
import asyncio
import asyncpg

async def show_structure():
    conn = await asyncpg.connect(
        host='db', port=5432, user='postgres', 
        password='password', database='zhidao_jinggang'
    )
    
    columns = await conn.fetch(\"\"\"
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns 
        WHERE table_name = '$table_name'
        ORDER BY ordinal_position
    \"\"\")
    
    if columns:
        print('列名 | 类型 | 可空 | 默认值')
        print('-' * 50)
        for col in columns:
            nullable = '是' if col['is_nullable'] == 'YES' else '否'
            default = col['column_default'] or ''
            print(f\"{col['column_name']} | {col['data_type']} | {nullable} | {default}\")
    else:
        print(f'表 {table_name} 不存在或无权限查看')
    
    await conn.close()

asyncio.run(show_structure())
"
}

# 查看迁移历史
show_migrations() {
    echo "📜 Alembic迁移历史:"
    if command -v alembic >/dev/null 2>&1; then
        alembic history --verbose
        echo ""
        echo "📍 当前版本:"
        alembic current
    else
        echo "❌ alembic命令未找到"
        echo "💡 请安装: pip install alembic"
    fi
}

# 数据库备份信息
show_backup_info() {
    echo "💾 数据库备份信息:"
    echo "容器内备份命令:"
    echo "  pg_dump -h db -U postgres -d zhidao_jinggang > backup.sql"
    echo ""
    echo "恢复命令:"
    echo "  psql -h db -U postgres -d zhidao_jinggang < backup.sql"
    echo ""
    echo "💡 备份文件位置建议: /app/backups/"
}

# 主程序
check_db_connection
echo "✅ 数据库连接正常"

while true; do
    show_menu
    read -p "请选择 (1-8): " choice
    
    case $choice in
        1)
            interactive_query
            ;;
        2)
            execute_sql
            ;;
        3)
            show_db_info
            ;;
        4)
            show_tables
            ;;
        5)
            show_table_structure
            ;;
        6)
            show_migrations
            ;;
        7)
            show_backup_info
            ;;
        8)
            echo "👋 再见!"
            exit 0
            ;;
        *)
            echo "❌ 无效选项，请选择 1-8"
            ;;
    esac
    
    echo ""
    read -p "按 Enter 继续..."
done