@echo off
REM 启动脚本 - 同时启动前端和后端服务
set Path=C:\Users\Administrator\.local\bin;%Path%

REM 启动后端服务
echo 启动后端服务...
start "后端服务" /D "%~dp0" uv run email-assistant

REM 等待后端服务启动
timeout /t 3 /nobreak >nul