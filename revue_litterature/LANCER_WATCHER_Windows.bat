@echo off
REM ============================================================
REM ALYCANTE PDF Watcher - Windows
REM Surveille pdfs_revue_litterature/pdfs/ et met a jour INDEX.html
REM ============================================================
title ALYCANTE PDF Watcher

cd /d "%~dp0"
echo.
echo ========================================================
echo   ALYCANTE PDF Watcher - mise a jour automatique
echo ========================================================
echo.
echo Le HTML INDEX.html sera regenere automatiquement
echo a chaque ajout/suppression de PDF dans le dossier reseau.
echo.
echo Ctrl+C pour arreter.
echo.
python watch_pdfs.py
pause
