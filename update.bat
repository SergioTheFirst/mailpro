@echo off
echo =============================================
echo   AUTO-UPDATE MailBot v26 → GitHub
echo =============================================

REM Переходим в каталог, где лежит bat
cd /d "%~dp0"

echo Текущая папка:
cd

echo -------------------------------
echo Удаляем старые файлы проекта...
echo -------------------------------

REM Удаляем все файлы кроме нужных
for %%F in (*) do (
    if /I not "%%F"==".gitignore" (
    if /I not "%%F"=="README.md" (
    if /I not "%%F"=="CONSTITUTION.md" (
    if /I not "%%F"=="requirements.txt" (
    if /I not "%%F"=="update.bat" (
    if /I not "%%F"=="mailpro.txt" (
    if /I not "%%F"=="patch.diff" (
        echo Удаляю файл %%F
        del /q "%%F"
    )))))))
)

REM Удаляем старые папки кроме mailbot_v26
for /d %%D in (*) do (
    if /I not "%%D"==".git" (
    if /I not "%%D"=="mailbot_v26" (
        echo Удаляю папку %%D
        rmdir /s /q "%%D"
    ))
)

echo -------------------------------
echo Добавляем новые файлы в Git...
echo -------------------------------
git add .

echo -------------------------------
echo Создаем коммит...
echo -------------------------------
git commit -m "Auto-update to MailBot v26"

echo -------------------------------
echo Отправляем на GitHub...
echo -------------------------------
git push

echo =============================================
echo   ГОТОВО! GitHub обновлен новой версией.
echo =============================================
pause
