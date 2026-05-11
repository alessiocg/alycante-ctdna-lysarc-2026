#!/bin/bash
# ALYCANTE PDF Watcher - Mac
cd "$(dirname "$0")"
echo ""
echo "========================================================"
echo "   ALYCANTE PDF Watcher - mise a jour automatique"
echo "========================================================"
echo ""
python3 watch_pdfs.py
read -p "Appuyez sur Entree pour fermer..."
