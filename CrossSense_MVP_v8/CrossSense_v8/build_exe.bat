@echo off
title Build CrossSense v8 EXE
cd /d "%~dp0"
echo.
echo === CrossSense v8 EXE Builder ===
echo This creates dist\CrossSense.exe with no black CMD window.
echo.
py -m pip install --upgrade pip
py -m pip install pyinstaller
py -m PyInstaller --version
py -m pip install -r requirements.txt
echo.
echo Building CrossSense.exe...
if exist crosssense.ico (
  py -m PyInstaller --noconfirm --windowed --onefile --collect-binaries vgamepad --name CrossSense --icon crosssense.ico main.py
) else (
  py -m PyInstaller --noconfirm --windowed --onefile --collect-binaries vgamepad --name CrossSense main.py
)
echo.
if exist dist\CrossSense.exe (
  echo SUCCESS: dist\CrossSense.exe was created.
  echo You can move that EXE to Desktop if you want.
) else (
  echo BUILD FAILED. Send a screenshot of the error above.
)
echo.
pause
