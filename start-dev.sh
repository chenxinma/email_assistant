#!/bin/bash
# 启动脚本 - 同时启动前端和后端服务

echo "正在启动邮件助手开发环境..."

# 启动后端服务
echo "启动后端服务..."
uv run email-assistant &

# 等待后端服务启动
sleep 3

# 启动前端开发服务器
echo "启动前端开发服务器..."
cd frontend
npm run dev &

# 等待前端服务启动
sleep 5

echo "开发环境已启动!"
echo "后端API: http://localhost:8000"
echo "前端页面: http://localhost:3000"