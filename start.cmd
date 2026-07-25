@echo off
cd /d "%~dp0"
set PYTHONDONTWRITEBYTECODE=1
python -B main.py
if errorlevel 1 pause
