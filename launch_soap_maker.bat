@echo off
REM Soap Maker Auto Recipe Generator Launcher
cd /d "%~dp0"
start "Soap Maker" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0src\main_auto.py"
