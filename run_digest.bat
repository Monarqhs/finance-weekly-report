@echo off
REM Wrapper untuk cron: pindah ke folder & jalankan digest via Python absolut.
cd /d "C:\2026\Finance\Digest-Weekly"
"C:\Users\ghali\AppData\Local\Programs\Python\Python312\python.exe" main.py
exit /b %ERRORLEVEL%
