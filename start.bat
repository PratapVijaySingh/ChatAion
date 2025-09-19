@echo off
echo Starting Virtual Human System...
echo.

echo [1/3] Starting Backend Server...
cd backend
start "Virtual Human Backend" cmd /k "python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak >nul

echo [2/3] Starting Frontend...
cd ..\frontend
start "Virtual Human Frontend" cmd /k "npm start"
timeout /t 3 /nobreak >nul

echo [3/3] Opening Browser...
start http://localhost:3000

echo.
echo Virtual Human System Started!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to exit...
pause >nul 