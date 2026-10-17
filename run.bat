@echo off
setlocal
rem ------------------------------------------------------------------
rem 图书管理系统 · 一键启动（run.ps1 的 Windows 双击 / cmd 入口）
rem 用法：run.bat [参数]   参数原样透传给 run.ps1，例如：
rem        run.bat -Reset        先重置演示数据再启动
rem        run.bat -BackendOnly  只启动后端
rem        run.bat -Open         启动后自动打开浏览器
rem        run.bat -Stop         停止后台残留进程
rem ------------------------------------------------------------------
cd /d "%~dp0"

where powershell >nul 2>nul
if errorlevel 1 (
    echo [ERROR] 未找到 PowerShell，请确认系统已启用 Windows PowerShell 5.1+。
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1" %*
set "code=%ERRORLEVEL%"

if not "%code%"=="0" (
    echo.
    echo [ERROR] 启动脚本异常退出，代码 %code%。日志见 logs\ 目录。
    pause
)
exit /b %code%
