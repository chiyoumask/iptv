@echo off
chcp 65001 >nul
setlocal

echo ============================================
echo  IPTV 直播源一键更新（解析 + 提交 + 推送）
echo ============================================
echo.

echo [1/4] 解析台湾频道 YouTube 直播流...
python tv.py
if errorlevel 1 (
    echo.
    echo [X] 解析失败或所有台湾频道均不可用，已中止推送。
    echo     请检查 tv.py 输出或网络/yt-dlp 后重试。
    goto :end
)

echo.
echo.
echo [2/5] 同步远端（防止推送冲突）...
git pull --rebase
if errorlevel 1 (
    echo [X] git pull 失败，请手动解决冲突后重跑。
    goto :end
)

echo.
echo [3/5] 暂存 IPTV.m3u...
git add IPTV.m3u
if errorlevel 1 (
    echo [X] git add 失败，请确认当前目录是 git 仓库。
    goto :end
)

REM 无改动则跳过提交，避免空提交报错
git diff --cached --quiet
if not errorlevel 1 (
    echo.
    echo [!] IPTV.m3u 无变化，无需提交推送。
    goto :end
)

echo.
echo [4/5] 提交更改...
for /f "delims=" %%T in ('powershell -NoProfile -Command "Get-Date -Format \"yyyy-MM-dd HH:mm:ss\""') do set TS=%%T
git commit -m "手动更新 IPTV 直播源 %TS%"
if errorlevel 1 (
    echo [X] git commit 失败。
    goto :end
)

echo.
echo [5/5] 推送到远程仓库...
git push
if errorlevel 1 (
    echo.
    echo [X] git push 失败。请手动执行 git push 或检查权限。
    goto :end
)

echo.
echo ============================================
echo  全部完成！IPTV.m3u 已推送到远程仓库。
echo  播放器订阅链接（替换用户名/仓库名）：
echo  https://raw.githubusercontent.com/<用户名>/<仓库名>/main/IPTV.m3u
echo ============================================

:end
echo.
pause
