@echo off
chcp 65001 >nul
python -m unittest discover -v
if errorlevel 1 pause
