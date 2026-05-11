#!/bin/bash
# ============================================================
# ALYCANTE - Demarrage tout-en-un (Mac)
# 1. Ouvre INDEX.html dans le navigateur par defaut
# 2. Lance le watcher (regenere INDEX.html quand vous ajoutez des PDFs)
# ============================================================

cd "$(dirname "$0")"

# Verifier Python3
if ! command -v python3 &> /dev/null; then
    echo "ERREUR : Python3 n'est pas installe."
    echo "Installez via : brew install python3"
    read -p "Appuyez sur Entree pour fermer..."
    exit 1
fi

# Verifier les scripts
if [ ! -f "generate_html_final.py" ] || [ ! -f "watch_pdfs.py" ]; then
    echo "ERREUR : Scripts Python introuvables dans ce dossier."
    read -p "Appuyez sur Entree pour fermer..."
    exit 1
fi

# Ouvre INDEX.html dans le navigateur
echo "Ouverture de INDEX.html dans votre navigateur..."
open "INDEX.html"

echo ""
echo "============================================================"
echo "   ALYCANTE - Watcher actif"
echo "============================================================"
echo ""
echo "  - Ajoutez vos PDFs dans le dossier 'pdfs/'"
echo "  - INDEX.html se met a jour automatiquement (auto-refresh 8s)"
echo "  - Fermez ce terminal pour arreter le watcher"
echo ""
echo "============================================================"
echo ""

# Lance le watcher
python3 watch_pdfs.py

echo ""
read -p "Watcher arrete. Appuyez sur Entree pour fermer..."
