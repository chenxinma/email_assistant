@echo off
REM �����ű� - ͬʱ����ǰ�˺ͺ�˷���
set Path=C:\Users\Administrator\.local\bin;%Path%

REM ������˷���
echo ������˷���...
start "��˷���" /D "%~dp0" uv run email-assistant

REM �ȴ���˷�������
timeout /t 3 /nobreak >nul