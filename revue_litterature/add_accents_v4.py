"""V4 finale : derniers mots manquants + apostrophe l' agressive."""
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

SRC = r"C:\Users\4067048\AppData\Local\Temp\alycante_lit\docgen\build_doc_v5b.js"
DST = r"C:\Users\4067048\AppData\Local\Temp\alycante_lit\docgen\build_doc_v5c.js"

APO = '’'

REPL = {
    # Mots restants
    'lignee': 'lignée', 'lignees': 'lignées',
    'lumiere': 'lumière', 'lumieres': 'lumières',
    'colore': 'coloré', 'coloree': 'colorée',
    'priere': 'prière', 'prieres': 'prières',
    'maniere': 'manière', 'manieres': 'manières',
    'matiere': 'matière', 'matieres': 'matières',
    'biere': 'bière', 'bieres': 'bières',
    'cuti': 'cuti',
    'sous-cutane': 'sous-cutané',
    'sous-cutanee': 'sous-cutanée',
    'sous-cutanees': 'sous-cutanées',
    'sous-cutanes': 'sous-cutanés',
    'cutane': 'cutané', 'cutanee': 'cutanée',
    'cutanees': 'cutanées', 'cutanes': 'cutanés',
    'sub-cutane': 'sous-cutané',
    'lapparition': 'l’apparition',
    'lhypothese': 'l’hypothèse',
    'ladversaire': 'l’adversaire',
    'evolu': 'évolu',  # rare mot
    'evolutif': 'évolutif',
    'derniere': 'dernière',
    'dernieres': 'dernières',
    'dernier': 'dernier',
    'derniers': 'derniers',
    'avance': 'avancé',
    'avances': 'avancés',
    'avancee': 'avancée',
    'avancees': 'avancées',
    'evaluable': 'évaluable',
    'evaluables': 'évaluables',
    'critere': 'critère',
    'criteres': 'critères',
    'temoin': 'témoin', 'temoins': 'témoins',
    'temoigner': 'témoigner',
    'temoignage': 'témoignage',
    'temoignages': 'témoignages',
    'temoignant': 'témoignant',
    'temoignent': 'témoignent',
    'cesse': 'cesse',  # pas d'accent
    'cesser': 'cesser',
    'cesseraient': 'cesseraient',
    'cessation': 'cessation',
    'cessera': 'cessera',
    'cessation': 'cessation',
    'consequence': 'conséquence',
    'consequences': 'conséquences',
    'consequent': 'conséquent',
    'consequents': 'conséquents',
    'consequente': 'conséquente',
    'consequentes': 'conséquentes',
    'consequentialiste': 'conséquentialiste',
    'consequentment': 'conséquemment',  # rare
    'consequemment': 'conséquemment',
    'preceder': 'précéder',
    'precede': 'précède',
    'precedent': 'précèdent',
    'precedente': 'précédente',
    'precedentes': 'précédentes',
    'precedents': 'précédents',
    'survenue': 'survenue',  # pas d'accent
    'survenir': 'survenir',
    'survenait': 'survenait',
    'survenant': 'survenant',
    'survivant': 'survivant',
    'survivants': 'survivants',
    'survivante': 'survivante',
    'survivantes': 'survivantes',
    'survie': 'survie',  # pas d'accent
    'survies': 'survies',
    'survivre': 'survivre',
    'compagnie': 'compagnie',
    'mediator': 'médiator',
    'mediateur': 'médiateur',
    'mediateurs': 'médiateurs',
    'medicalement': 'médicalement',
    'periphery': 'périphérie',  # english
    'peripheries': 'périphéries',
    'peripheriques': 'périphériques',
    'peripheriquement': 'périphériquement',
    'peripherique': 'périphérique',
    'circulant': 'circulant',  # pas d'accent
    'circulants': 'circulants',
    'circulante': 'circulante',
    'circulantes': 'circulantes',
    'circulation': 'circulation',
    'circulations': 'circulations',
    'circuler': 'circuler',
    'recidive': 'récidive',
    'recidives': 'récidives',
    'recidiver': 'récidiver',
    'recidivee': 'récidivée',
    'recidive': 'récidivé',
    'recidives': 'récidivés',
    'pousse': 'pousse',  # pas d'accent
    'pousses': 'poussés',
    'poussee': 'poussée',
    'poussees': 'poussées',
    'pousseur': 'pousseur',
    'preserve': 'préservé',  # ambigu adjectif vs verbe
    'preserver': 'préserver',
    'preservation': 'préservation',
    'preservatrice': 'préservatrice',
    'preserves': 'préservés',
    'preservee': 'préservée',
    'preservees': 'préservées',
    'parametre': 'paramètre',
    'parametres': 'paramètres',
    'parametrer': 'paramétrer',
    'parametrique': 'paramétrique',
    'parametriques': 'paramétriques',
    'parametrage': 'paramétrage',
    'parametrages': 'paramétrages',
    'definir': 'définir',
    'defini': 'défini',
    'definie': 'définie',
    'definitif': 'définitif',
    'definitive': 'définitive',
    'definitifs': 'définitifs',
    'definitives': 'définitives',
    'definitivement': 'définitivement',
    'definition': 'définition',
    'definitions': 'définitions',
    'concretes': 'concrètes',
    'concrete': 'concrète',
    'concretement': 'concrètement',
    'profondement': 'profondément',
    'redaction': 'rédaction',
    'redactions': 'rédactions',
    'redacteur': 'rédacteur',
    'redacteurs': 'rédacteurs',
    'redige': 'rédigé',
    'redigee': 'rédigée',
    'redigees': 'rédigées',
    'rediges': 'rédigés',
    'rediger': 'rédiger',
    'donnees': 'données',
    'donnee': 'donnée',
    'reglee': 'réglée',
    'reglees': 'réglées',
    'regle': 'réglé',
    'regles': 'réglés',
    'regler': 'régler',
    'regulier': 'régulier',
    'reguliere': 'régulière',
    'reguliers': 'réguliers',
    'regulieres': 'régulières',
    'regulierement': 'régulièrement',
    'regularite': 'régularité',
    'regulation': 'régulation',
    'reguler': 'réguler',
    'regule': 'régulé',
    'regulee': 'régulée',
    'regulees': 'régulées',
    'regules': 'régulés',
    'regulateurs': 'régulateurs',
    'regulateur': 'régulateur',
    'regulatrice': 'régulatrice',
    'regulatrices': 'régulatrices',
    'regulation': 'régulation',
    'regulations': 'régulations',
    'systemique': 'systémique',
    'systemiques': 'systémiques',
    'fenetre': 'fenêtre',
    'fenetres': 'fenêtres',
    'forets': 'forêts',
    'foret': 'forêt',
    'tete-de-pont': 'tête-de-pont',
    'jeune': 'jeune',
    'jeunes': 'jeunes',
    'ouverture': 'ouverture',
    'ouvert': 'ouvert',
    'ouverts': 'ouverts',
    'ouverte': 'ouverte',
    'ouvertes': 'ouvertes',
    'ouvrir': 'ouvrir',
    'ouvrant': 'ouvrant',
    'ouvre': 'ouvre',
    'ouvrent': 'ouvrent',
    'mieux': 'mieux',
    'milieu': 'milieu',
    'milieux': 'milieux',
    'cle': 'clé',
    'cles': 'clés',
    'attente': 'attente',
    'attentes': 'attentes',
    'attendre': 'attendre',
    'attendant': 'attendant',
    'attentif': 'attentif',
    'attentifs': 'attentifs',
    'attentive': 'attentive',
    'attentives': 'attentives',
    'attention': 'attention',
    'eu': 'eu',  # pas d'accent en general
    'enregistre': 'enregistré',
    'enregistree': 'enregistrée',
    'enregistrees': 'enregistrées',
    'enregistres': 'enregistrés',
    'enregistrer': 'enregistrer',
    'enregistrement': 'enregistrement',
    'enregistrements': 'enregistrements',
    'avec': 'avec',  # pas d'accent
    'efficace': 'efficace',
    'efficaces': 'efficaces',
    'efficacement': 'efficacement',
    'efficacite': 'efficacité',
    'inefficacite': 'inefficacité',
    'inefficace': 'inefficace',
    'inefficaces': 'inefficaces',
}


def apply_replacements(text):
    sorted_keys = sorted(REPL.keys(), key=len, reverse=True)
    for ascii_word in sorted_keys:
        accented = REPL[ascii_word]
        if ascii_word == accented:
            continue
        pattern = r'\b' + re.escape(ascii_word) + r'\b'
        text = re.sub(pattern, accented, text)
    return text


def apply_lprime(text):
    """Remplace 'l X' (l espace X) par 'l’X' quand X commence par voyelle ou h"""
    # Pattern : 'l ' suivi d'un mot commencant par voyelle ou h
    # On ne touche que les contextes texte (pas le code JS)
    # Pattern conservateur : "l accent" -> "l'accent"
    text = re.sub(
        r"\bl ([aâàäeéèêëiîïoôöuûüùhAÂÀÄEÉÈÊËIÎÏOÔÖUÛÜÙHéàêëôöïâüù])",
        lambda m: f"l{APO}{m.group(1)}",
        text
    )
    text = re.sub(
        r"\bL ([aâàäeéèêëiîïoôöuûüùhAÂÀÄEÉÈÊËIÎÏOÔÖUÛÜÙHéàêëôöïâüù])",
        lambda m: f"L{APO}{m.group(1)}",
        text
    )
    return text


with open(SRC, 'r', encoding='utf-8') as f:
    text = f.read()
original = text
text = apply_replacements(text)
text = apply_lprime(text)
n_diff = sum(1 for a, b in zip(original, text) if a != b)
print(f"Modifications: {n_diff}")
with open(DST, 'w', encoding='utf-8') as f:
    f.write(text)
print(f"Ecrit: {DST}")
