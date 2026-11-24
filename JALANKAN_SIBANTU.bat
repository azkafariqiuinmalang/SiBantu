@echo off
setlocal
cd /d "%~dp0"
title SiBantu - Server Lokal
set "GDSS_PORT=5050"

echo Menjalankan SiBantu...
echo Buka http://127.0.0.1:5050/login setelah muncul pesan Running on.
if exist "instance\AKUN_AWAL_SIBANTU.txt" (
    echo Email dan kata sandi awal tersedia di instance\AKUN_AWAL_SIBANTU.txt.
) else (
    echo Jika belum punya akun, jalankan python -m flask --app app create-user --role bpbd.
)
echo Biarkan jendela ini terbuka selama memakai SiBantu.
echo Tekan Ctrl+C untuk menghentikan server.
echo.

python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Python atau Flask belum tersedia di terminal ini.
    echo Jalankan python -m pip install -r requirements.txt dari folder UAS.
    pause
    exit /b 1
)

python app.py
echo.
echo Server berhenti. Jika ada pesan error, kirimkan isi jendela ini.
pause
endlocal
