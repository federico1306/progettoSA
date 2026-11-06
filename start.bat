@echo off
echo Starting AI Assisted Software Architecting Council on http://127.0.0.1:8000 ...
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

