@echo off
cd /d E:\Projetos\Controle_de_pragas1.1
call .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
