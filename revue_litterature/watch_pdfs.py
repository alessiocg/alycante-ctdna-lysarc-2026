"""
Watcher : surveille le dossier pdfs/ et regenere INDEX.html automatiquement
quand un nouveau PDF est ajoute ou supprime.

Usage :
    python watch_pdfs.py
    (laissez tourner en arriere-plan, Ctrl+C pour arreter)

Le HTML inclut un auto-refresh JavaScript pour rafraichir la page toutes les 5 sec.
"""
import os
import sys
import time
import subprocess
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

# Chemins
SCRIPT_DIR = Path(__file__).parent
GENERATOR = SCRIPT_DIR / "generate_html_final.py"
# Le watcher surveille le dossier sur le reseau
WATCH_DIR = Path(r"//Hmn-cifs-hnas.wprod.ds.aphp.fr/shares/IMMUNOLOGIE-BIOLOGIQUE/SECTEUR MALADIES LYMPHOPROLIFERATIVES/D_PROTOCOLES/DLBCL/protocole ALYCANTE/Réunion LYSARC 2026/output/pdfs_revue_litterature/pdfs")

print("=" * 60)
print("  ALYCANTE PDF Watcher - mise a jour automatique")
print("=" * 60)
print(f"Surveille : {WATCH_DIR}")
print(f"Generateur : {GENERATOR}")
print()

if not WATCH_DIR.exists():
    print(f"ERREUR : dossier {WATCH_DIR} introuvable")
    sys.exit(1)

def snapshot():
    """Retourne l'ensemble des fichiers PDF dans le dossier."""
    try:
        return set(f.name for f in WATCH_DIR.iterdir()
                   if f.suffix.lower() == '.pdf')
    except Exception as e:
        print(f"  [erreur scan] {e}")
        return None

def regenerate():
    """Lance le generateur HTML."""
    print(f"  [{time.strftime('%H:%M:%S')}] Regeneration INDEX.html...", end=' ', flush=True)
    try:
        r = subprocess.run(
            [sys.executable, str(GENERATOR)],
            capture_output=True, text=True, timeout=60
        )
        if r.returncode == 0:
            # Extract n_ok / n_manq de la sortie
            out = r.stdout
            ok = manq = '?'
            for line in out.split('\n'):
                if 'PDFs locaux' in line:
                    ok = line.split(':')[1].strip()
                if 'Manquants' in line:
                    manq = line.split(':')[1].strip()
            print(f"OK ({ok} dispos, {manq} restants)")
        else:
            print(f"ERREUR : {r.stderr[:200]}")
    except Exception as e:
        print(f"EXCEPTION : {e}")

# Premier scan + premiere regeneration
print(f"Snapshot initial...")
prev = snapshot()
print(f"  Fichiers PDF actuels : {len(prev) if prev else 0}")
regenerate()

print()
print("En attente de changements (Ctrl+C pour arreter)...")
print()

try:
    while True:
        time.sleep(3)  # poll toutes les 3 secondes
        curr = snapshot()
        if curr is None or curr == prev:
            continue
        # Changement detecte
        added = curr - prev
        removed = prev - curr
        if added:
            for f in added:
                print(f"  [{time.strftime('%H:%M:%S')}] + AJOUTE : {f}")
        if removed:
            for f in removed:
                print(f"  [{time.strftime('%H:%M:%S')}] - SUPPRIME : {f}")
        regenerate()
        prev = curr
except KeyboardInterrupt:
    print()
    print("Watcher arrete.")
