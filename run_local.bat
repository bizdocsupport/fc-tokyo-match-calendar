@echo off
chcp 65001 > nul
python -m pip install -r requirements.txt
python -m streamlit run legacy_app.py
pause
