@echo off
title Create CrossSense Desktop Shortcut
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut([Environment]::GetFolderPath('Desktop')+'\CrossSense v8.lnk'); $s.TargetPath='%CD%\run_crosssense_silent.vbs'; $s.WorkingDirectory='%CD%'; if(Test-Path '%CD%\crosssense.ico'){$s.IconLocation='%CD%\crosssense.ico'}; $s.Save()"
echo Desktop shortcut created: CrossSense v8
pause
