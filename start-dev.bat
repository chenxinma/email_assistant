@echo off
REM �����ű� - ͬʱ����ǰ�˺ͺ�˷���
set Path=C:\Users\Administrator\.local\bin;%Path%
echo ���������ʼ����ֿ�������...

REM ������˷���
echo ������˷���...
start "��˷���" /D "%~dp0" uv run email-assistant

REM �ȴ���˷�������
timeout /t 3 /nobreak >nul

REM ����ǰ�˿���������
echo ����ǰ�˿���������...
cd frontend
start "ǰ�˿���������" npm run start

REM �ȴ�ǰ�˷�������
timeout /t 5 /nobreak >nul

echo ��������������!
echo ���API: http://localhost:8000
echo ǰ��ҳ��: http://localhost:3000