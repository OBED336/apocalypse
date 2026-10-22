@echo off
chcp 65001 >nul
cd /d "%~dp0"
python apocalypse_ultimate.py
if errorlevel 1 (
  echo.
  echo No se pudo iniciar el juego. Requiere Python y pygame.
  echo Para instalar pygame: python -m pip install -r requirements.txt
  pause
)
