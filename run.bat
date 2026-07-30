@echo off
setlocal
cd /d "%~dp0"
if not defined PORT set "PORT=8011"
python -m uvicorn main:app --host 127.0.0.1 --port %PORT%
