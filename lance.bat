@echo off
title DF Modelfit
cd /d "%~dp0"

if not exist requirements.txt (
  echo Erreur: requirements.txt introuvable.
  pause
  exit /b 1
)

echo Verification des dependances (requirements.txt)...
if exist .venv\Scripts\activate.bat (
  call .venv\Scripts\activate.bat
  pip install -r requirements.txt -q
) else (
  pip install -r requirements.txt -q
)
if errorlevel 1 (
  echo Erreur lors de l'installation des dependances.
  pause
  exit /b 1
)
echo Dependances OK.

echo Demarrage du serveur DF Modelfit...
start "DF Modelfit - Serveur" /D "%~dp0" cmd /k "if exist .venv\Scripts\activate.bat (.venv\Scripts\activate.bat && python main.py) else (python main.py)"

echo Attente du demarrage du serveur (3 s)...
timeout /t 3 /nobreak >nul

echo Ouverture du navigateur sur http://localhost:5050
start "" "http://localhost:5050"

echo.
echo Le serveur tourne dans l'autre fenetre. Fermez-la pour arreter.
pause
