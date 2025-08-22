#!/usr/bin/env python
"""
知道井冈 - 命令行管理工具
"""

import asyncio
import click
from loguru import logger

from app.core.config import settings
from app.db.init_db import init_db, create_sample_data


@click.group()
def cli():
    """知道井冈后端管理工具"""
    pass


@cli.command()
def init():
    """初始化数据库"""
    click.echo("正在初始化数据库...")
    asyncio.run(init_db())
    click.echo("✅ 数据库初始化完成")


@cli.command()
def create_samples():
    """创建示例数据"""
    click.echo("正在创建示例数据...")
    asyncio.run(create_sample_data())
    click.echo("✅ 示例数据创建完成")


@cli.command()
@click.option('--host', default='0.0.0.0', help='服务器主机地址')
@click.option('--port', default=8000, help='服务器端口')
@click.option('--reload', is_flag=True, help='启用热重载')
def serve(host, port, reload):
    """启动开发服务器"""
    import uvicorn
    
    click.echo(f"🚀 启动服务器 http://{host}:{port}")
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


@cli.command()
@click.option('--username', prompt='用户名', help='用户名')
@click.option('--email', prompt='邮箱', help='邮箱地址')
@click.option('--password', prompt=True, hide_input=True, help='密码')
@click.option('--superuser', is_flag=True, help='创建超级用户')
def create_user(username, email, password, superuser):
    """创建新用户"""
    async def _create_user():
        from app.core.security import get_password_hash
        from app.db.session import AsyncSessionLocal
        from app.db.models.user import User
        
        async with AsyncSessionLocal() as session:
            # 检查用户是否已存在
            from app.db.repositories.user_repository import user_repository
            existing_user = await user_repository.get_by_username(session, username=username)
            if existing_user:
                click.echo(f"❌ 用户 {username} 已存在")
                return
            
            existing_email = await user_repository.get_by_email(session, email=email)
            if existing_email:
                click.echo(f"❌ 邮箱 {email} 已被使用")
                return
            
            # 创建用户
            hashed_password = get_password_hash(password)
            user_obj = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
                is_superuser=superuser,
                is_active=True,
                is_verified=True,
            )
            
            session.add(user_obj)
            await session.commit()
            
            user_type = "超级用户" if superuser else "普通用户"
            click.echo(f"✅ {user_type} {username} 创建成功")
    
    asyncio.run(_create_user())


@cli.command()
def test():
    """运行测试"""
    import subprocess
    import sys
    
    click.echo("🧪 运行测试...")
    result = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"])
    
    if result.returncode == 0:
        click.echo("✅ 所有测试通过")
    else:
        click.echo("❌ 测试失败")
        sys.exit(1)


@cli.command()
def lint():
    """运行代码检查"""
    import subprocess
    import sys
    
    click.echo("🔍 运行代码检查...")
    
    # 运行 black
    click.echo("运行 Black 格式化...")
    subprocess.run([sys.executable, "-m", "black", "app/", "tests/"])
    
    # 运行 ruff
    click.echo("运行 Ruff 检查...")
    result = subprocess.run([sys.executable, "-m", "ruff", "check", "app/", "tests/"])
    
    # 运行 mypy
    click.echo("运行 MyPy 类型检查...")
    subprocess.run([sys.executable, "-m", "mypy", "app/"])
    
    if result.returncode == 0:
        click.echo("✅ 代码检查通过")
    else:
        click.echo("⚠️ 代码检查发现问题，请查看上述输出")


@cli.command()
def db_migrate():
    """运行数据库迁移"""
    import subprocess
    
    click.echo("📦 运行数据库迁移...")
    result = subprocess.run(["alembic", "upgrade", "head"])
    
    if result.returncode == 0:
        click.echo("✅ 数据库迁移完成")
    else:
        click.echo("❌ 数据库迁移失败")


@cli.command()
@click.option('--message', '-m', prompt='迁移信息', help='迁移描述信息')
def db_revision(message):
    """创建新的数据库迁移"""
    import subprocess
    
    click.echo(f"📝 创建数据库迁移: {message}")
    result = subprocess.run(["alembic", "revision", "--autogenerate", "-m", message])
    
    if result.returncode == 0:
        click.echo("✅ 迁移文件创建成功")
    else:
        click.echo("❌ 迁移文件创建失败")


@cli.command()
def info():
    """显示项目信息"""
    click.echo("📋 项目信息")
    click.echo(f"项目名称: {settings.PROJECT_NAME}")
    click.echo(f"版本: {settings.VERSION}")
    click.echo(f"环境: {settings.ENVIRONMENT}")
    click.echo(f"数据库: {settings.DATABASE_URL}")
    click.echo(f"Redis: {settings.redis_url}")
    click.echo(f"调试模式: {settings.DEBUG}")


@cli.command()
def shell():
    """启动交互式Shell"""
    import IPython
    from app.db.session import AsyncSessionLocal
    from app.db.models import *
    from app.core.config import settings
    
    click.echo("🐍 启动交互式Shell")
    click.echo("可用对象: settings, AsyncSessionLocal, User, Item")
    
    IPython.embed()


if __name__ == "__main__":
    cli() 