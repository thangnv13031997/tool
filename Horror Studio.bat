@echo off
cd /d "%~dp0"
if not exist "env\Scripts\pythonw.exe" (
  echo Chua cai dat. Dang chay setup.bat...
  call setup.bat
)
start "" "%~dp0env\Scripts\pythonw.exe" "%~dp0app\main.py"
