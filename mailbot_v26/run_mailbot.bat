@echo off
chcp 65001 >nul
title MailBot Premium v26 - Launcher

echo ===========================================
echo      MAILBOT PREMIUM v26 - START
echo ===========================================

REM Папка, где лежит start.py
set BOTDIR=C:\pro\mailbot\mailpro\mailbot_v26

echo Переход в папку бота...
cd /d "%BOTDIR%"

echo Проверка Python...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found!
    pause
    exit /B 1
)

echo Активация виртуального окружения...
IF EXIST venv\Scripts\activate (
    call venv\Scripts\activate
) ELSE (
    echo Creating venv...
    python -m venv venv
    call venv\Scripts\activate
)

echo Запуск MailBot...
python start.py

echo.
echo ===========================================
echo            BOT FINISHED / STOPPED
echo ===========================================
pause
