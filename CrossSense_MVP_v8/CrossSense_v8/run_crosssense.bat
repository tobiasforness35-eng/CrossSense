@echo off
title CrossSense v8 launcher
cd /d "%~dp0"
echo CrossSense v8 launcher
echo.
echo Updating pip...
python -m pip install --upgrade pip
if errorlevel 1 goto pyerr

echo.
echo Installing/updating dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 goto depserr

echo.
echo Starting CrossSense v8...
python main.py
pause
exit /b 0

:pyerr
echo.
echo ERROR: Python or pip failed. Install Python 3.12/3.13 from python.org and tick "Add Python to PATH".
pause
exit /b 1

:depserr
echo.
echo ERROR: Could not install dependencies. Check internet connection and Python version.
pause
exit /b 1
