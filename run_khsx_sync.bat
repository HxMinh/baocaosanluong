@echo off
REM Batch file to run KHSX TONG Sync Manager
REM This file can be used with Windows Task Scheduler

cd /d "%~dp0"
python khsx_sync_manager.py

pause
