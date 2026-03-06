# 部署说明

## 本地部署

### 环境要求
- Python 3.11+
- uv 包管理器

### 安装步骤
```bash
# 1. 克隆项目代码
# 2. 安装依赖
uv sync

# 3. 初始化数据库
uv run email-assistant --init
```

### 服务启动方式

#### API 模式
```bash
uv run email-assistant --api
```
这将以 API 服务模式启动，监听端口 9000。

#### 桌面应用模式
```bash
uv run email-assistant
```
这将以完整桌面应用程序模式启动。

## 生产部署

### 系统环境准备
- 确保安装了所需 Python 版本
- 预先安装系统依赖包（如 SQLite 扩展支持）
- 确保有足够磁盘空间用于数据库文件（data/ 目录）

### 配置优化
- 根据生产需求调整 `data/config.json` 中的配置
- 配置日志保留策略（日志目录 logs/）
- 设置合适的邮件轮询间隔 `refreshInterval`

### 运行环境设置
- 设置环境变量以指向正确的数据库位置
- 保障服务持续运行的进程监控方案（如 systemd, supervisor）

## 前端集成

### 连接后端 API
前端应用需要配置以连接到部署的后端 API：
- API 地址: `http://<server-ip>:9000`
- 支持 CORS 来源包括 `http://localhost` 和 `http://localhost:3000`

## 服务管理

### 启动脚本
可用启动脚本位于项目根目录：
- Linux/macOS: `start.sh`
- Windows: `start.bat`

### 配置重载
目前需要重启服务才能应用新的配置变更。

## 监控和维护

### 日志文件
- 日志路径: `logs/` 目录
- 日志格式: 结构化日志（便于分析）

### 数据库维护
- 数据库存储路径: `data/email_assistant.db`
- 支持定期备份和迁移