#!/bin/bash
# ============================================================
# ALYCANTE - Telechargement automatique des 120 PDFs
# Script tout-en-un pour Mac
# ============================================================
# Usage : double-clic ou ./lancer_telechargement.sh

set -e

# Couleurs pour la console
BLEU='\033[0;34m'
VERT='\033[0;32m'
JAUNE='\033[0;33m'
ROUGE='\033[0;31m'
NC='\033[0m' # No color

echo -e "${BLEU}=============================================="
echo "  ALYCANTE - Telechargement des 120 PDFs"
echo -e "==============================================${NC}"
echo ""

# Repertoire ou se trouve ce script (= dossier revue_litterature)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Etape 1 : Verifier Python
echo -e "${BLEU}[1/4]${NC} Verification de Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${ROUGE}Python3 n'est pas installe.${NC}"
    echo "Installez-le via : brew install python3"
    echo "Ou telechargez sur https://www.python.org/downloads/"
    read -p "Appuyez sur Entree pour quitter..."
    exit 1
fi
echo -e "${VERT}OK${NC} - $(python3 --version)"

# Etape 2 : Installer requests si necessaire
echo -e "${BLEU}[2/4]${NC} Verification du module 'requests'..."
if ! python3 -c "import requests" &> /dev/null; then
    echo "Installation du module requests..."
    pip3 install requests --quiet --user 2>/dev/null || pip3 install requests --quiet
fi
echo -e "${VERT}OK${NC}"

# Etape 3 : Demander l'email (sauvegarde dans un fichier pour reutilisation)
EMAIL_FILE="$HOME/.alycante_email"
if [ -f "$EMAIL_FILE" ]; then
    EMAIL=$(cat "$EMAIL_FILE")
    echo -e "${BLEU}[3/4]${NC} Email Unpaywall : ${EMAIL} (depuis $EMAIL_FILE)"
else
    echo -e "${BLEU}[3/4]${NC} Premiere utilisation - email pour l'API Unpaywall"
    read -p "Votre email (sera sauvegarde dans $EMAIL_FILE) : " EMAIL
    if [ -z "$EMAIL" ]; then
        EMAIL="anonymous@example.com"
    fi
    echo "$EMAIL" > "$EMAIL_FILE"
fi

# Etape 4 : Lancer le script
echo ""
echo -e "${BLEU}[4/4]${NC} Telechargement en cours (3-4 min pour 120 references)..."
echo -e "${JAUNE}Source 1 : Europe PMC (open access gratuit)${NC}"
echo -e "${JAUNE}Source 2 : Unpaywall (versions Author Manuscript)${NC}"
echo ""

OUTPUT_DIR="$SCRIPT_DIR/pdfs_revue"
python3 fetch_pdfs.py --email "$EMAIL" --out "$OUTPUT_DIR"

# Resume
echo ""
echo -e "${VERT}=============================================="
echo "  Telechargement termine !"
echo -e "==============================================${NC}"
echo ""
echo "Dossier des resultats : $OUTPUT_DIR"
echo ""

if [ -d "$OUTPUT_DIR/pdfs" ]; then
    N_PDFS=$(ls "$OUTPUT_DIR/pdfs"/*.pdf 2>/dev/null | wc -l | tr -d ' ')
    TAILLE=$(du -sh "$OUTPUT_DIR/pdfs" 2>/dev/null | cut -f1)
    echo -e "${VERT}PDFs telecharges : $N_PDFS sur 120 ($TAILLE)${NC}"
fi

echo ""
echo "Pour les PDFs manquants, ouvrez :"
echo "  $OUTPUT_DIR/index.html"
echo ""

# Ouvrir index.html dans le navigateur par defaut
if [ -f "$OUTPUT_DIR/index.html" ]; then
    echo "Ouverture de index.html dans votre navigateur..."
    open "$OUTPUT_DIR/index.html"
fi

# Ouvrir le Finder sur le dossier des PDFs
if [ -d "$OUTPUT_DIR/pdfs" ]; then
    open "$OUTPUT_DIR/pdfs"
fi

echo ""
read -p "Appuyez sur Entree pour fermer..."
