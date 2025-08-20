@echo off
REM 启动脚本 - 同时启动前端和后端服务
set Path=C:\Users\Administrator\.local\bin;%Path%
echo 正在启动邮件助手开发环境...

REM 启动后端服务
echo 启动后端服务...
start "后端服务" /D "%~dp0" uv run email-assistant

REM 等待后端服务启动
timeout /t 3 /nobreak >nul

REM 启动前端开发服务器
echo 启动前端开发服务器...
cd frontend
start "前端开发服务器" npm run start

REM 等待前端服务启动
timeout /t 5 /nobreak >nul

echo 开发环境已启动!
echo 后端API: http://localhost:8000
echo 前端页面: http://localhost:3000