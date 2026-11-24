@echo off
cd /d %~dp0
if not exist .venv (
  py -m venv .venv
)
call .venv\Scriptsctivate
python -m pip install --upgrade pip
pip install -r requirements.txt
python run_app.py
pause
