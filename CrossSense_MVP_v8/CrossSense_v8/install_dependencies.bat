@echo off
title Install CrossSense v8 dependencies
cd /d "%~dp0"
echo Installing CrossSense dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
echo Done. Now run run_crosssense.bat as administrator.
pause
