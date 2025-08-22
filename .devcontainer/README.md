# 知道井冈 DevContainer 开发指南

## 🚀 实际开发流程

### **第一次启动**
```bash
# 1. 在VS Code中打开DevContainer
# Ctrl+Shift+P → "Dev Containers: Reopen in Container"

# 2. 快速环境检查
./.devcontainer/quick-check.sh

# 3. 启动开发环境
./.devcontainer/start.sh
```

### **日常开发流程**
```bash
# 每次开发前检查环境
./.devcontainer/quick-check.sh

# 如果环境正常，直接启动应用
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 如果有问题，使用启动脚本
./.devcontainer/start.sh
```

## 🛠️ 脚本使用指南

### **核心脚本 (按使用频率排序)**

#### **1. `quick-check.sh` - 环境状态检查**
**用途**: 快速检查开发环境是否就绪
**使用场景**: 每次开发前、问题排查
```bash
./.devcontainer/quick-check.sh
```
**输出**: 服务状态、依赖状态、建议操作

#### **2. `start.sh` - 应用启动**
**用途**: 一键启动完整开发环境
**使用场景**: 首次启动、环境有问题时
```bash
./.devcontainer/start.sh
```
**功能**: 等待服务 → 检查连接 → 运行迁移 → 启动应用

#### **3. `connect-db.sh` - 数据库操作**
**用途**: 数据库交互工具
**使用场景**: 查看数据、执行SQL、检查表结构
```bash
./.devcontainer/connect-db.sh
```
**功能**: 
- 交互式SQL查询
- 显示表结构和数据
- 查看迁移历史
- 数据库备份指导

#### **4. `check-db.sh` - 数据库诊断**
**用途**: 详细的数据库连接诊断
**使用场景**: 数据库连接问题排查
```bash
./.devcontainer/check-db.sh
```
**功能**: 
- 端口连通性测试
- 数据库认证测试
- 依赖检查
- 故障排除建议

## 📋 开发工作流程图

```
开始开发
    ↓
运行 quick-check.sh
    ↓
环境是否就绪？
    ├─ 是 → 直接启动应用 (uvicorn)
    └─ 否 → 运行 start.sh
               ↓
           应用启动成功？
               ├─ 是 → 开始开发
               └─ 否 → 运行 check-db.sh 排查问题
```

## 🎯 实际使用场景

### **场景1: 每日开发启动**
```bash
# 快速检查
./.devcontainer/quick-check.sh

# 如果显示"环境就绪"，直接启动
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### **场景2: 首次或问题启动**
```bash
# 完整启动流程
./.devcontainer/start.sh
```

### **场景3: 数据库开发**
```bash
# 查看表结构
./.devcontainer/connect-db.sh
# 选择 "5) 显示表结构"

# 执行SQL查询
./.devcontainer/connect-db.sh
# 选择 "2) 执行单个SQL语句"
```

### **场景4: 问题排查**
```bash
# 详细诊断
./.devcontainer/check-db.sh

# 查看服务日志 (在主机执行)
docker-compose -f .devcontainer/docker-compose.yml logs db
docker-compose -f .devcontainer/docker-compose.yml logs redis
```

### **场景5: 数据库迁移**
```bash
# 创建迁移
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head

# 查看迁移历史
./.devcontainer/connect-db.sh
# 选择 "6) 查看迁移历史"
```

## 🔧 故障排除

### **常见问题 & 解决方案**

#### **1. 服务连接失败**
```bash
# 问题: PostgreSQL/Redis 连接失败
# 解决: 在主机启动服务
docker-compose -f .devcontainer/docker-compose.yml up -d db redis
```

#### **2. 依赖缺失**
```bash
# 问题: Python包导入失败
# 解决: 安装开发依赖
pip install -e .[dev]
```

#### **3. 应用启动失败**
```bash
# 问题: FastAPI应用无法启动
# 解决: 检查详细错误
./.devcontainer/check-db.sh

# 手动启动查看错误
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### **4. 数据库迁移问题**
```bash
# 问题: 迁移失败
# 解决: 检查迁移状态
alembic current
alembic history

# 如果需要，回滚并重新迁移
alembic downgrade -1
alembic upgrade head
```

## 📊 访问地址

启动成功后可访问:
- **🌍 API文档**: http://localhost:8000/docs
- **💓 健康检查**: http://localhost:8000/health
- **📊 API基础**: http://localhost:8000/api/v1
- **📈 监控指标**: http://localhost:8000/metrics

## 💡 最佳实践

1. **每次开发前**: 运行 `quick-check.sh` 确保环境正常
2. **使用make命令**: `make run`, `make test`, `make format`
3. **数据库操作**: 优先使用 `connect-db.sh` 而不是直接连接
4. **问题排查**: 先用 `quick-check.sh`，再用 `check-db.sh`
5. **保持更新**: 定期运行 `pip install -e .[dev]` 更新依赖

## 🚨 注意事项

- 脚本在DevContainer内部运行，不需要docker-compose命令
- 数据库和Redis服务在主机上运行，容器内通过网络连接
- 如果脚本权限问题，在主机执行: `chmod +x .devcontainer/*.sh`
- 所有脚本都针对DevContainer环境优化，不适用于本地直接运行

---

**快速开始**: 运行 `./.devcontainer/quick-check.sh` 检查环境，然后根据提示进行操作！