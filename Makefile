# 知道井冈 - 项目管理 Makefile

.PHONY: help install test lint format clean build run dev deploy

# 默认目标
.DEFAULT_GOAL := help

# 项目配置
PROJECT_NAME := zhidao-jinggang-backend
PYTHON := python3
UV := uv
DOCKER_IMAGE := $(PROJECT_NAME):latest

help: ## 显示帮助信息
	@echo "知道井冈 - 企业级FastAPI后端服务"
	@echo ""
	@echo "可用命令："
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## 安装项目依赖
	@echo "🔧 安装项目依赖..."
	$(UV) pip install -e .
	@echo "✅ 依赖安装完成"

install-dev: ## 安装开发依赖
	@echo "🔧 安装开发依赖..."
	$(UV) pip install -e .[dev,test,docs]
	@echo "✅ 开发依赖安装完成"

test: ## 运行测试
	@echo "🧪 运行测试..."
	$(UV) run pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing
	@echo "✅ 测试完成"

lint: ## 代码检查
	@echo "🔍 代码检查..."
	$(UV) run black --check app tests
	$(UV) run isort --check-only app tests
	$(UV) run flake8 app tests
	$(UV) run mypy app
	@echo "✅ 代码检查完成"

format: ## 格式化代码
	@echo "🎨 格式化代码..."
	$(UV) run black app tests
	$(UV) run isort app tests
	@echo "✅ 代码格式化完成"

clean: ## 清理缓存和临时文件
	@echo "🧹 清理缓存..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	@echo "✅ 清理完成"

build: ## 构建Docker镜像
	@echo "🏗️  构建Docker镜像..."
	docker build -t $(DOCKER_IMAGE) .
	@echo "✅ Docker镜像构建完成"

run: ## 运行应用
	@echo "🚀 启动应用..."
	$(UV) run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev: ## 开发模式运行
	@echo "🔧 开发模式启动..."
	docker-compose up --build

deploy: ## 部署到生产环境
	@echo "🚀 部署到生产环境..."
	./scripts/deploy.sh

# 数据库相关
migrate: ## 运行数据库迁移
	@echo "🔄 运行数据库迁移..."
	$(UV) run alembic upgrade head
	@echo "✅ 数据库迁移完成"

migrate-create: ## 创建新的迁移文件
	@read -p "请输入迁移描述: " message; \
	$(UV) run alembic revision --autogenerate -m "$$message"

migrate-rollback: ## 回滚数据库迁移
	@echo "⏪ 回滚数据库迁移..."
	$(UV) run alembic downgrade -1
	@echo "✅ 数据库回滚完成"

# Docker相关
docker-build: build ## 构建Docker镜像

docker-run: ## 运行Docker容器
	@echo "🐳 运行Docker容器..."
	docker run -d --name $(PROJECT_NAME) -p 8000:8000 $(DOCKER_IMAGE)

docker-stop: ## 停止Docker容器
	@echo "🛑 停止Docker容器..."
	docker stop $(PROJECT_NAME) || true
	docker rm $(PROJECT_NAME) || true

docker-logs: ## 查看Docker容器日志
	docker logs -f $(PROJECT_NAME)

# 生产环境相关
prod-up: ## 启动生产环境
	@echo "🚀 启动生产环境..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-down: ## 停止生产环境
	@echo "🛑 停止生产环境..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

prod-logs: ## 查看生产环境日志
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# 监控相关
monitor-up: ## 启动监控服务
	@echo "📊 启动监控服务..."
	docker-compose -f docker-compose.monitoring.yml up -d

monitor-down: ## 停止监控服务
	@echo "📊 停止监控服务..."
	docker-compose -f docker-compose.monitoring.yml down

# 安全相关
security-check: ## 安全检查
	@echo "🔒 运行安全检查..."
	$(UV) run bandit -r app/
	$(UV) run safety check
	@echo "✅ 安全检查完成"

# 性能测试
perf-test: ## 性能测试
	@echo "⚡ 运行性能测试..."
	$(UV) run locust -f tests/performance/locustfile.py --host=http://localhost:8000

# 文档生成
docs: ## 生成文档
	@echo "📚 生成文档..."
	$(UV) run sphinx-build -b html docs/ docs/_build/html/
	@echo "✅ 文档生成完成"

# 备份
backup: ## 备份数据
	@echo "💾 备份数据..."
	./scripts/backup.sh
	@echo "✅ 备份完成"

# 还原
restore: ## 还原数据
	@echo "🔄 还原数据..."
	./scripts/restore.sh
	@echo "✅ 还原完成"

# 健康检查
health: ## 健康检查
	@echo "🏥 健康检查..."
	curl -f http://localhost:8000/health || exit 1
	@echo "✅ 服务健康"

# 版本管理
version: ## 显示版本信息
	@echo "📋 版本信息:"
	@echo "  项目: $(PROJECT_NAME)"
	@echo "  Git: $$(git describe --tags --always)"
	@echo "  Python: $$(python --version)"
	@echo "  Docker: $$(docker --version)"

# 初始化项目
init: ## 初始化项目
	@echo "🎯 初始化项目..."
	$(UV) venv
	$(UV) pip install -e .[dev,test,docs]
	$(UV) run pre-commit install
	@echo "✅ 项目初始化完成" 