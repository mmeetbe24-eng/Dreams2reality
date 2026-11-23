@echo off
setlocal enabledelayedexpansion
title Dreams2Reality BCI Cockpit
cd /d "%~dp0"

echo ========================================================
echo    Dreams2Reality: Two-Electrode BCI Neural Cockpit
echo ========================================================

set "PYTHON_EXE="

:: 1. Direct explicit paths to Python 3.11
if exist "C:\Users\HP\AppData\Local\Programs\Python311\python.exe" (
    set "PYTHON_EXE=C:\Users\HP\AppData\Local\Programs\Python311\python.exe"
    goto :VERIFY
)

if exist "%LOCALAPPDATA%\Programs\Python311\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python311\python.exe"
    goto :VERIFY
)

:: 2. Check py launcher
where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PYTHON_EXE=py -3.11"
    goto :VERIFY
)

:: 3. Check python command in PATH
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PYTHON_EXE=python"
    goto :VERIFY
)

:VERIFY
if "%PYTHON_EXE%"=="" (
    echo [ERROR] No valid Python installation detected.
    echo Please ensure Python 3.11 is installed in C:\Users\HP\AppData\Local\Programs\Python311
    pause
    exit /b 1
)

echo [OK] Using Python: %PYTHON_EXE%
%PYTHON_EXE% -V
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Selected Python failed verification check.
    pause
    exit /b 1
)

echo.
echo Starting Dreams2Reality Server on http://localhost:8000 ...
echo Launching your browser in 2 seconds...

:: Launch browser in background after short delay
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:8000"

:: Start FastAPI backend
"%PYTHON_EXE%" main.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo [NOTICE] Dreams2Reality server terminated with code %ERRORLEVEL%.
    pause
)
