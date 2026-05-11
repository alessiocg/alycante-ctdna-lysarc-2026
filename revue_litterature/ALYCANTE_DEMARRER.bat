@echo off
REM ============================================================
REM ALYCANTE - Demarrage tout-en-un (Windows)
REM 1. Ouvre INDEX.html dans le navigateur par defaut
REM 2. Lance le watcher (regenere INDEX.html quand vous ajoutez des PDFs)
REM ============================================================
title ALYCANTE PDF Watcher
cd /d "%~dp0"

REM Verifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR : Python n'est pas installe ou pas dans le PATH.
    echo Telechargez Python sur https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Verifier que generate_html_final.py et watch_pdfs.py existent
if not exist "generate_html_final.py" (
    echo ERREUR : generate_html_final.py introuvable.
    pause
    exit /b 1
)
if not exist "watch_pdfs.py" (
    echo ERREUR : watch_pdfs.py introuvable.
    pause
    exit /b 1
)

REM Ouvre INDEX.html dans le navigateur par defaut (asynchrone, ne bloque pas)
echo Ouverture de INDEX.html dans votre navigateur...
start "" "INDEX.html"

echo.
echo ============================================================
echo   ALYCANTE - Watcher actif
echo ============================================================
echo.
echo   - Ajoutez vos PDFs dans le dossier 'pdfs/'
echo   - INDEX.html se met a jour automatiquement
echo   - Fermez cette fenetre pour arreter le watcher
echo.
echo ============================================================
echo.

REM Lance le watcher (reste actif jusqu'a Ctrl+C ou fermeture)
python watch_pdfs.py

echo.
echo Watcher arrete. Appuyez sur une touche pour fermer...
pause >nul
