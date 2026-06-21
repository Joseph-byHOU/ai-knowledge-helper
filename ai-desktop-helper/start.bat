@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title AI Desktop Helper Launcher

echo AI 桌面学习助手 - Windows 启动器
echo ========================================
echo.

cd /d "%~dp0"

set "VENV_PYTHON=python-runtime\Scripts\python.exe"
set "VENV_PIP=python-runtime\Scripts\pip.exe"
set "REQ_FILE=my-ai-daily-news\references\requirements.txt"

where node >nul 2>nul
if errorlevel 1 (
    echo [!] 未检测到 Node.js，请先安装 Node.js 18+ 后再运行。
    echo     下载地址: https://nodejs.org/
    echo.
    pause
    exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
    echo [!] 未检测到 npm，请确认 Node.js 已正确安装。
    echo.
    pause
    exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
    where py >nul 2>nul
    if errorlevel 1 (
        echo [!] 未检测到 Python，请先安装 Python 3.9+，并勾选 "Add Python to PATH"。
        echo     下载地址: https://www.python.org/downloads/
        echo.
        pause
        exit /b 1
    )
)

if not exist "%REQ_FILE%" (
    echo [!] 未找到 Python 依赖文件: %REQ_FILE%
    echo.
    pause
    exit /b 1
)

if not exist "%VENV_PYTHON%" (
    echo [*] 首次运行：创建 Python 虚拟环境...
    where python >nul 2>nul
    if errorlevel 1 (
        py -3 -m venv python-runtime
    ) else (
        python -m venv python-runtime
    )
    if errorlevel 1 (
        echo [!] Python 虚拟环境创建失败。
        echo.
        pause
        exit /b 1
    )
) else (
    echo [✓] Python 虚拟环境已存在
)

echo [*] 安装 / 更新 Python 依赖...
"%VENV_PYTHON%" -m pip install --upgrade pip
if errorlevel 1 (
    echo [!] pip 升级失败，请检查网络或 Python 环境。
    echo.
    pause
    exit /b 1
)

"%VENV_PIP%" install -r "%REQ_FILE%"
if errorlevel 1 (
    echo [!] Python 依赖安装失败，请检查网络后重试。
    echo.
    pause
    exit /b 1
)

if not exist "node_modules" (
    echo [*] 首次运行：安装 Node.js 依赖...
    npm install
    if errorlevel 1 (
        echo [!] npm install 失败，请检查网络或 npm 配置。
        echo.
        pause
        exit /b 1
    )
) else (
    echo [✓] Node.js 依赖目录已存在
)

if exist "python-runtime\Scripts\playwright.exe" (
    echo [*] 检查 Playwright Chromium（首次可能需要安装）...
    python-runtime\Scripts\playwright.exe install chromium
    if errorlevel 1 (
        echo [!] Playwright 浏览器安装失败，应用仍可启动，但部分浏览器备选采集功能可能不可用。
    )
)

echo.
echo [*] 启动 Electron 应用...
echo [*] 如果出现安全提示，请选择允许或继续运行。
echo.

npm start
set "APP_EXIT_CODE=%ERRORLEVEL%"

echo.
if "%APP_EXIT_CODE%"=="0" (
    echo [✓] 应用已正常退出。
) else (
    echo [!] 应用退出，返回码: %APP_EXIT_CODE%
)
echo.
pause
exit /b %APP_EXIT_CODE%
