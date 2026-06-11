@echo off
title ALTF4 Streamer Agency - Dev Server
cd /d "C:\Users\Jedi PC\streamer-agency"
call venv\Scripts\activate
cd app
echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   ALTF4 Streamer Agency - Starting...   ║
echo  ╚══════════════════════════════════════════╝
echo.
echo  🌐 Open browser: http://127.0.0.1:5000
echo.
echo  👑 Admin: admin1 / admin123
echo  👑 Admin: admin2 / admin123
echo  👤 Staff: staff1 / staff123
echo  👤 Staff: staff2 / staff123
echo.
echo  Press CTRL+C to stop the server
echo.
python main.py
pause
