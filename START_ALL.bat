@echo off
title Risk System Launcher
color 0A

echo ==================================================
echo      KHOI DONG HE THONG DANH GIA RUI RO
echo ==================================================

echo.
echo [1/4] Dang kiem tra ha tang Docker (Kafka, Mongo)...
docker-compose up -d

echo.
echo [2/4] Dang bat Backend API (Python FastAPI)...
:: Mở cửa sổ mới, vào thư mục backend và chạy main.py
start "Backend API Server" cmd /k "cd backend && python main.py"

echo.
echo [3/4] Dang bat AI Worker (Xu ly ngam)...
:: Mở cửa sổ mới, vào thư mục backend và chạy worker.py
start "AI Worker Service" cmd /k "cd backend && python worker.py"

echo.
echo [4/4] Dang bat Frontend Dashboard (ReactJS)...
:: Mở cửa sổ mới, vào thư mục frontend và chạy npm start
start "Frontend Dashboard" cmd /k "cd frontend && npm start"

echo.
echo ==================================================
echo      DA KHOI DONG THANH CONG! 
echo      Hay doi trinh duyet tu dong mo ra...
echo ==================================================
timeout /t 5