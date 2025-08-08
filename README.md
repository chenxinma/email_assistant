# 邮件助手

一款智能桌面应用，帮助用户高效管理邮件、提取关键信息并自动化邮件处理流程。

## 功能特点

- 智能邮件摘要生成
- 邮件知识库系统
- 智能邮件发送
- 邮件模板管理
- 自然语言查询邮件

## 安装

### 后端安装
1. 克隆项目代码
2. 安装依赖: `uv sync`
3. 启动应用: `uv run email-assistant`

### 前端安装
1. 进入前端目录: `cd frontend`
2. 安装依赖: `npm install`

## 使用说明

### 启动开发环境
1. 启动后端服务: `python run.py`
2. 启动前端开发服务器: `cd frontend && npm run dev`
3. 启动Electron应用: `cd frontend && npm run electron:serve`

在Windows上，你可以使用启动脚本同时启动前后端服务：
```bash
start-dev.bat
```

在Unix/Linux/MacOS上，使用：
```bash
./start-dev.sh
```

### 构建应用
1. 构建前端: `cd frontend && npm run build`
2. 构建Electron应用: `cd frontend && npm run electron:build`

### 使用应用
1. 配置邮箱账户信息
2. 启动应用后，应用会自动获取邮件并生成摘要
3. 可以使用知识库功能查询历史邮件
4. 使用模板功能快速发送邮件

## API文档

启动应用后访问: http://127.0.0.1:8000/docs