# 知道井冈 - 企业级FastAPI后端服务

基于FastAPI的现代化企业级后端服务，支持Docker容器化部署和DevContainer开发环境。

## ✨ 项目特性

- **现代化架构**: FastAPI + SQLAlchemy + Alembic + Redis
- **容器化部署**: Docker + Docker Compose
- **开发环境**: VS Code DevContainer支持
- **监控系统**: Prometheus + Grafana
- **代码质量**: Black + Ruff + MyPy + Pre-commit
- **安全认证**: JWT + OAuth2
- **API文档**: 自动生成OpenAPI文档

## 🚀 快速开始

### 1. DevContainer开发（推荐）

在VS Code中：
1. 安装Dev Containers扩展
2. 打开项目根目录
3. 按 `Ctrl+Shift+P` 打开命令面板
4. 运行 "Dev Containers: Reopen in Container"
5. 等待容器构建完成

启动应用：
```bash
# 使用启动脚本
./.devcontainer/start.sh

# 或手动启动
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Docker Compose部署

```bash
# 构建并启动所有服务
docker-compose up --build

# 后台运行
docker-compose up -d
```

### 3. 本地开发

```bash
# 安装依赖
pip install -e .[dev]

# 启动数据库（Docker）
docker-compose up db redis -d

# 运行迁移
alembic upgrade head

# 启动应用
uvicorn app.main:app --reload
```

## 📁 项目结构

```
Zhidao-Jinggang-backend/
├── app/                    # 应用代码
│   ├── api/               # API路由
│   ├── core/              # 核心配置
│   ├── db/                # 数据库模块
│   ├── schemas/           # Pydantic模型
│   ├── services/          # 业务逻辑
│   └── main.py           # 应用入口
├── .devcontainer/         # DevContainer配置
├── migrations/            # 数据库迁移
├── tests/                 # 测试文件
├── docker-compose.yml     # Docker编排
├── Dockerfile            # 容器镜像
└── pyproject.toml        # 项目配置
```

## 🔧 开发工具

### 数据库管理
```bash
# 创建迁移
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head

# 查看历史
alembic history
```

### 代码质量
```bash
# 格式化代码
black .
ruff check . --fix

# 类型检查
mypy .

# 运行测试
pytest
```

### 使用Makefile
```bash
# 查看所有命令
make help

# 运行应用
make run

# 运行测试
make test

# 代码格式化
make format

# 代码检查
make lint
```

## 🌐 API端点

| 端点 | 描述 | 访问地址 |
|------|------|----------|
| API文档 | Swagger UI | http://localhost:8000/docs |
| API文档 | ReDoc | http://localhost:8000/redoc |
| API | REST API | http://localhost:8000/api/v1 |
| 健康检查 | 服务状态 | http://localhost:8000/health |
| 监控指标 | Prometheus | http://localhost:8000/metrics |

## 🗄️ 数据库

- **数据库**: PostgreSQL 15
- **缓存**: Redis 7
- **ORM**: SQLAlchemy 2.0
- **迁移**: Alembic

**连接信息**：
- 主机: localhost
- 端口: 5432
- 用户: postgres
- 密码: password
- 数据库: zhidao_jinggang

## 📊 监控

### Prometheus指标
访问: http://localhost:9090
- HTTP请求计数
- 响应时间分布
- 错误率统计

### Grafana仪表板
访问: http://localhost:3000
- 用户名: admin
- 密码: admin

## 🔒 安全

- JWT认证
- 密码加密
- 速率限制
- CORS配置
- 安全头设置

## 🚀 部署

### Docker生产部署
```bash
# 构建生产镜像
docker build -t zhidao-jinggang-backend .

# 运行生产容器
docker run -p 8000:8000 zhidao-jinggang-backend
```

### 环境变量
复制 `env.example` 到 `.env` 并配置：
```bash
cp env.example .env
```

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=app tests/

# 运行特定测试
pytest tests/api/test_auth.py
```

## 📦 依赖管理

项目使用 `pyproject.toml` 管理依赖：
```bash
# 安装开发依赖
pip install -e .[dev]

# 仅安装运行依赖
pip install -e .
```

## 🤝 贡献

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📧 联系

项目维护者: Zhidao Jinggang Team
邮箱: dev@zhidao-jinggang.com

---

⭐ 如果这个项目对你有帮助，请给我们一个星标！