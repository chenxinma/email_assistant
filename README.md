# 邮件助手

一款智能桌面应用，帮助用户高效管理邮件、提取关键信息并自动化邮件处理流程。

## 功能特点

- 智能邮件摘要生成：自动生成每日邮件摘要和待办事项清单
- 邮件知识库系统：将邮件内容向量化存储，支持语义搜索
- 邮件智能检索：通过自然语言查询历史邮件内容
- 邮件同步功能：支持增量邮件同步与属性提取
- 智能问答助手：提供基于邮件内容的AI问答服务

## 技术架构

### 后端
- **Python 3.11+**：主要编程语言
- **FastAPI**：高性能Web框架
- **SQLite + sqlite-vec**：本地数据库和向量存储
- **OpenAI API**：AI处理和嵌入模型
- **IMAPClient**：邮件协议处理

### 前端
- **Electron**：跨平台桌面应用框架
- **React 19**：前端UI库
- **Ant Design**：UI组件库
- **Vite**：构建工具

## 安装

### 环境要求
- Python 3.11+
- Node.js 16+
- npm 或 yarn

### 后端安装
1. 克隆项目代码
2. 安装依赖: `uv sync`
3. 启动应用: `uv run email-assistant`

### 前端安装
1. 进入前端目录: `cd frontend`
2. 安装依赖: `npm install`

## 使用说明

### 启动开发环境
1. 初始化数据库: `uv run email-assistant --init`
2. 启动API服务: `uv run email-assistant --api` (在端口9000运行API)
3. 或者直接启动完整的桌面应用: `uv run email-assistant`

### 构建应用
1. 构建前端: `cd frontend && npm run build`
2. 构建Electron应用: `cd frontend && npm run electron:build`

### 使用应用
1. 配置邮箱账户信息
2. 启动应用后，应用会自动获取邮件并生成摘要
3. 邮件刷新: `/api/emails/refresh` 支持流式响应返回邮件处理进度
4. AI功能: `/` 端点提供智能邮件搜索、摘要生成等交互

## 配置说明

应用使用 `data/config.json` 文件进行配置，首次运行时会自动生成默认配置：
```json
{
  "mail": {
    "refreshInterval": 15,
    "indexedFolders": ["INBOX"],
    "emailAddress": "your_email@example.com",
    "emailPassword": "your_email_password",
    "imapServer": "imap.example.com",
    "imapPort": 993,
    "smtpServer": "smtp.example.com",
    "smtpPort": 465
  },
  "ai": {
    "embeddingModel": "bge-large-zh-v1.5",
    "embeddingBaseUrl": "http://localhost:9997/v1",
    "embeddingApiKey": "empty password",
    "summaryLength": 512,
    "whoami": "我是谁？"
  }
}
```

## 核心API端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/emails/refresh` | POST | 刷新邮件，支持设置天数参数 |
| `/` | POST | AI代理交互端点，支持邮件搜索、摘要等功能 |
| `/docs` | GET | Swagger API文档界面 |

## 忽略的文件和目录

为了保护敏感信息和避免提交不必要的文件，本项目使用 .gitignore 文件来忽略以下文件和目录：

- Python生成的文件（如 `__pycache__/`, `*.pyc`, `build/`, `dist/` 等）
- 虚拟环境目录（`.venv`）
- 本地配置文件（`.env`）
- 前端依赖和构建目录（`frontend/node_modules/`, `frontend/dist/`）
- 数据和日志目录（`data/`, `logs/`）

这些文件和目录不会被版本控制系统跟踪，应用在运行时也不会读取这些被忽略的文件和目录，以确保敏感信息的安全。

## API文档

启动应用后访问: http://0.0.0.0:9000/docs