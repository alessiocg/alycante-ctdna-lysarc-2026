# Plan Statistique

## ctDNA comme biomarqueur dans le DLBCL sous CAR-T cells — Étude ALYCANTE

**Version 3 — Mars 2026 — Volet ctDNA / MRD**

> Modifications V2 → V3 :
> - Clarification des deux types de ΔctDNA (delta ratio vs. delta quantité) dans la section 2.3
> - Ajout du ΔSUVmax dans les variables disponibles (section 2.3)
> - Note sur le paradoxe d'effectif M9/M12 (section 2.2)
> - Ajout section 4.3bis : Analyse combinée ctDNA + TEP (modèle intégré)
> - Ajout section 4.7.5 : Profils de réponse moléculaire (clearance patterns)
> - Ajout section 4.7.6 : Courbes ROC temps-dépendantes
> - Enrichissement de la section 4.3 : corrélation ΔctDNA vs. ΔSUVmax
> - Enrichissement de la section 5 : analyse en risques compétitifs

---

## 1. Contexte et objectifs

Cette analyse porte sur le suivi longitudinal du ctDNA (ADN tumoral circulant) mesuré par phased-variants chez des patients atteints de DLBCL (lymphome diffus à grandes cellules B) traités par CAR-T cells dans l'étude ALYCANTE. Le ctDNA est évalué comme biomarqueur de MRD (maladie résiduelle mesurable) et comme outil de monitoring de la réponse au traitement.

Les données de profil tumoral (mutation, variants somatiques) ne sont pas encore disponibles et feront l'objet d'un plan statistique complémentaire ultérieur.

### Objectif principal

Évaluer la valeur pronostique du ctDNA (quantitatif brut et en décroissance) et de la MRD qualitative sur la survie (PFS, OS) chez les patients DLBCL traités par CAR-T, et sa capacité à prédire la réponse au traitement (réponse TEP).

### Objectifs secondaires

- Étudier la corrélation entre ctDNA et réponse métabolique (TEP Deauville et ΔSUVmax)
- Étudier la corrélation entre ctDNA baseline et volume tumoral métabolique (TMTV)
- Définir des seuils optimaux de ctDNA (quantitatif brut et en décroissance) pour la prédiction de la survie
- Évaluer l'impact de l'informativité des échantillons (nombre de régions couvertes) sur la fiabilité des résultats de MRD, et proposer un seuil d'informativité minimum (a priori autour de 100 000)
- Décrire la cinétique longitudinale du ctDNA de la leucaphérèse à M12
- **[V3]** Évaluer la valeur pronostique d'un modèle combiné ctDNA + TEP (réponse moléculaire + métabolique)
- **[V3]** Caractériser les profils de clearance moléculaire (patterns de réponse ctDNA) et leur impact pronostique

---

## 2. Description des données

### 2.1 Population

62 patients évaluables, avec un suivi longitudinal de la leucaphérèse à M12. L'attrition progressive (62 → 38–43 à M9–M12) est attendue et sera documentée.

### 2.2 Timepoints et effectifs

Le tableau ci-dessous résume les timepoints disponibles et leur rôle dans le plan d'analyse :

| Timepoint | Description | N obs. | Rôle analytique |
|---|---|---|---|
| GG Initial | Biopsie ganglionnaire initiale | ~11 patients (sous-groupe) | Tumeur de référence |
| Leucaphérèse | Prélèvement des lymphocytes | 62 | Baseline ctDNA |
| J–5 | Lymphodéplétion | 60 | Baseline alternative / cinétique précoce |
| J0 | Injection CAR-T | 59 | Baseline alternative / cinétique précoce |
| J14 | Suivi précoce | 56 | MRD très précoce |
| M1 | Suivi 1 mois | 55 | MRD précoce |
| M3 | Suivi 3 mois | 50 | MRD intérimaire |
| M6 | Suivi 6 mois | 42 | MRD intérimaire |
| M9 | Suivi 9 mois | 38 | MRD intérimaire |
| M12 | Suivi 12 mois | 43 | MRD long terme |
| Rechute/Progression | Si événement | 16 | Dynamique à la rechute |

> **[V3] Note sur l'effectif M9/M12 :** L'effectif à M9 (n=38) est paradoxalement inférieur à celui de M12 (n=43). Plusieurs hypothèses explicatives : (1) prélèvements M9 manqués puis rattrapés à M12, (2) fenêtres de visite décalées avec attribution au timepoint le plus proche, (3) erreurs de codage. **Action requise : clarifier avec le data management LYSARC la raison de cette inversion avant les analyses.** Selon le cas, il faudra soit ré-attribuer certains prélèvements au bon timepoint, soit documenter le pattern de données manquantes à M9 spécifiquement.

### 2.3 Variables ctDNA disponibles

| Variable | Type | Description | Timepoints |
|---|---|---|---|
| MRD_quali | Qualitatif | POSITIF / NEGATIF / NI | Tous |
| MRD_quanti_quota | Quantitatif continu | Fraction de phased-variants (UMI mutés / UMI totaux, 0–1) | Tous |
| MRD_quanti_heg | Quantitatif continu | haploid Equivalent Genomes (hEG/mL), intègre la mesure du cfDNA total | Tous |
| nbre_total_regions_couvertes | Quantitatif entier | Profondeur cumulée = informativité de l'échantillon | Tous |
| **ΔctDNA_ratio** | **Quantitatif dérivé** | **Delta du ratio de phased-variants (quota) : log10[quota(Tx) / quota(baseline)]. Reflète la décroissance de la fraction tumorale relative (UMI mutés / UMI totaux), indépendamment de la quantité totale de cfDNA.** | **J14–M12** |
| **ΔctDNA_quantité** | **Quantitatif dérivé** | **Delta de la quantité absolue (hEG) : log10[hEG(Tx) / hEG(baseline)]. Reflète la décroissance de la charge tumorale absolue, en tenant compte à la fois de la fraction tumorale ET de la concentration en cfDNA total (hEG/mL).** | **J14–M12** |
| Réponse TEP (Deauville) | Ordinal / binarisé | Score de Deauville (1–5), binarisé en ≤3 vs. >3 | M3, M6 |
| **ΔSUVmax** | **Quantitatif continu** | **Variation relative du SUVmax entre baseline et timepoint d'évaluation. À fournir par données imagerie.** | **M3, M6** |
| TMTV | Quantitatif continu | Total Metabolic Tumor Volume. À fournir par données imagerie | Baseline |
| PFS | Survie | Temps jusqu'à progression/décès | Clinique |
| OS | Survie | Temps jusqu'au décès | Clinique |

> **[V3] Note importante sur les deux types de ΔctDNA :**
>
> Il est essentiel de distinguer ces deux métriques de décroissance, car elles ne mesurent pas la même chose :
>
> - **ΔctDNA_ratio** (delta du ratio / quota) : mesure la variation de la *fraction de molécules mutées* dans le cfDNA. C'est un indicateur de la proportion tumorale relative. Si le cfDNA total augmente (inflammation post-CAR-T, CRS) sans que le nombre d'UMI mutés ne change, le ratio baisse → peut donner un faux signal de réponse.
>
> - **ΔctDNA_quantité** (delta de la quantité / hEG) : mesure la variation de la *charge tumorale absolue* en intégrant la concentration totale de cfDNA. C'est théoriquement un meilleur reflet de la masse tumorale réelle, mais plus sensible aux variations pré-analytiques (volume de sang, extraction).
>
> **Les deux métriques seront systématiquement analysées en parallèle dans toutes les sections du plan (4.1 à 4.6).** Les discordances entre les deux deltas seront documentées et discutées, en particulier dans le contexte du CRS post-CAR-T (relargage massif de cfDNA non tumoral).

Note : les hEG avec valeur quota = 0 génèrent une erreur de calcul (#NUM!) dans le fichier source (log d'un zéro). Ces 153 observations correspondent à des échantillons MRD-négatifs et seront traitées spécifiquement (cf. section gestion des données).

### 2.4 Variables cliniques à fournir

Les variables suivantes ne figurent pas dans le fichier ctDNA et devront être fournies par le data management / CRF ALYCANTE :

- **PFS et OS** (dates d'événement, statut de censure, date de point)
- **Réponse TEP** : score de Deauville par timepoint (évaluation centralisée si disponible), **ΔSUVmax**, TMTV baseline
- **Caractéristiques baseline** : âge, sexe, stade Ann Arbor, IPI/aaIPI, nombre de lignes antérieures, sous-type histologique (GCB vs. non-GCB), produit CAR-T utilisé, statut réfractaire vs. rechute
- **CRS/ICANS** : grade max (ASTCT), date de survenue
- **Données biologiques accessoires** si disponibles : LDH baseline, β2-microglobuline, lymphocytes absolus (expansion CAR-T)

---

## 3. Gestion et préparation des données

### 3.1 Nettoyage

- **Valeurs #NUM! et #DIV/0!** : recalculer les hEG à partir de quota, ou imputer hEG = 0 quand quota = 0 (cohérent avec MRD négative)
- **Statut NI (Non Informatif)** : 5 patients concernés à la leucaphérèse — à traiter comme données manquantes pour les analyses de survie, sauf analyse de sensibilité spécifique (cf. objectif informativité)
- **Statut NA** : à différencier entre « prélèvement non réalisé » et « résultat non interprétable »
- **[V3] Vérification M9/M12** : après retour du data management, corriger les affectations de timepoints si nécessaire

### 3.2 Variables dérivées

- **ΔctDNA_ratio** = log10[quota(Tx) / quota(baseline)]. Trois baselines possibles : leucaphérèse, J–5, J0.
- **ΔctDNA_quantité** = log10[hEG(Tx) / hEG(baseline)]. Mêmes trois baselines.
- **[V3] Gestion des zéros dans les deltas :** pour les patients MRD-négatifs au timepoint Tx (quota = 0), le log du ratio est indéfini. Stratégie : (a) imputer une valeur plancher correspondant à la limite de détection du test (ex. 1 UMI muté / UMI totaux observés), ou (b) coder comme « réponse complète moléculaire » (CMR) et traiter séparément dans une analyse catégorielle. Les deux approches seront comparées en sensibilité.
- **Dichotomisation du ctDNA quantitatif** en catégories « haut » vs. « bas » selon des seuils optimisés (cf. section méthodologie des seuils)
- **MRD qualitative recodage** : POSITIF = 1, NEGATIF = 0, NI et NA = manquant
- **Conversion du ctDNA** : variable de changement catégoriel (ex. conversion MRD+ → MRD− entre deux timepoints)
- **[V3] Catégories de réponse moléculaire** (cf. section 4.7.5) :
  - CMR (Complete Molecular Response) : MRD négative confirmée (2 timepoints consécutifs)
  - PMR (Partial Molecular Response) : décroissance ≥ 2-log mais MRD toujours positive
  - SMD (Stable Molecular Disease) : décroissance < 2-log
  - MPD (Molecular Progressive Disease) : augmentation du ctDNA ≥ 0.5-log par rapport au nadir

---

## 4. Plan d'analyse

### 4.0 Analyses descriptives préliminaires

- **Description de la cohorte** : tableau 1 des caractéristiques patients (médiane, IQR pour les variables continues ; effectifs et % pour les variables catégorielles)
- **Description de la distribution du ctDNA** (quota et hEG) par timepoint : médiane, IQR, range, proportion de MRD+ vs. MRD− vs. NI
- **Taux de disponibilité des échantillons** par timepoint (flowchart / CONSORT-like)
- **[V3] Flowchart spécifique M9/M12** : documenter les raisons de non-disponibilité et les éventuels chevauchements
- **Cinétique longitudinale du ctDNA** : spaghetti plots individuels (quota et/ou hEG en échelle log) avec médiane de groupe, stratifiés par événement PFS (oui/non)
- **[V3] Représentation parallèle des deux métriques** : spaghetti plots en ΔctDNA_ratio et ΔctDNA_quantité côte à côte, pour visualiser les éventuelles discordances (en particulier aux timepoints précoces J14–M1, période de CRS)
- **Corrélation ctDNA baseline (leucaphérèse) vs. TMTV** : diagramme de dispersion, coefficient de Spearman
- **[V3] Corrélation cfDNA total vs. CRS** : si les données de cfDNA total (ng/mL ou hEG/mL) sont disponibles indépendamment du ctDNA tumoral, décrire la cinétique du cfDNA total et sa corrélation avec la sévérité du CRS (pour contextualiser les variations du ΔctDNA_ratio vs. ΔctDNA_quantité)

### 4.1 ctDNA brut quantitatif et survie

**Objectif** : évaluer la valeur pronostique du niveau absolu de ctDNA mesuré en quota (%) et en hEG aux timepoints pré-CAR-T (leucaphérèse, J–5, J0) sur la PFS et l'OS.

**Méthode :**

- Courbes de Kaplan-Meier : stratifiées par ctDNA haut vs. bas (seuil déterminé par méthode de maximisation du log-rank, cf. 4.5)
- Test du log-rank pour comparaison entre groupes
- Modèles de Cox univariés : ctDNA en continu (quota et hEG, transformation log si nécessaire) → HR, IC95%, p-value
- Modèles de Cox univariés : ctDNA dichotomisé (haut vs. bas) → HR, IC95%, p-value
- Timepoints analysés : leucaphérèse, J–5, J0 (chacun séparément)

**Corrélation avec le TMTV :**

- Corrélation de Spearman entre ctDNA baseline (quota et hEG) et TMTV
- Modèle de Cox bivarié ctDNA + TMTV pour évaluer l'indépendance pronostique

### 4.2 ctDNA MRD qualitative et survie

**Objectif** : évaluer la valeur pronostique du statut MRD qualitatif (POSITIF vs. NEGATIF) à chaque timepoint de suivi sur la PFS et l'OS.

**Méthode :**

- Courbes de Kaplan-Meier par statut MRD+ vs. MRD−, à chaque timepoint (J14, M1, M3, M6, M9, M12)
- Test du log-rank
- Modèles de Cox univariés : MRD quali (positif = 1) → HR, IC95%, p-value, à chaque timepoint
- **Landmark analysis** : les analyses de survie à chaque timepoint utiliseront l'approche landmark (t0 = date du timepoint) pour éviter le biais de garantie de temps (immortal time bias)

**Corrélation avec la réponse TEP :**

- Tableau croisé MRD quali × réponse TEP (Deauville ≤ 3 vs. > 3) aux timepoints M3 et M6
- Concordance (kappa de Cohen), sensibilité, spécificité de la MRD pour prédire la réponse TEP et inversement
- Analyse de discordance : profil des patients MRD+/TEP− et MRD−/TEP+ (description clinique)

### 4.3 ctDNA MRD quantitative (décroissance) et survie

**Objectif** : évaluer la valeur pronostique de la décroissance du ctDNA (ΔctDNA) entre une baseline et les timepoints de suivi, sur la PFS et l'OS.

**[V3] Définition des deux ΔctDNA :**

Le ratio de décroissance sera calculé de deux façons indépendantes :

1. **ΔctDNA_ratio** = log10[quota(Tx) / quota(baseline)]
   - Reflète la variation de la fraction tumorale relative
   - Avantage : peu sensible aux variations de cfDNA total (sauf si très importantes)
   - Limite : peut sous-estimer la réponse si le cfDNA total diminue proportionnellement

2. **ΔctDNA_quantité** = log10[hEG(Tx) / hEG(baseline)]
   - Reflète la variation de la charge tumorale absolue
   - Avantage : meilleur reflet de la masse tumorale réelle
   - Limite : sensible aux variations de cfDNA total (CRS, inflammation, pré-analytique)

Trois baselines seront testées pour chaque métrique : leucaphérèse, J–5, J0.

**Méthode :**

- Courbes de Kaplan-Meier stratifiées par ΔctDNA haut vs. bas (seuil optimisé, cf. 4.5) aux timepoints J14, M1, M3, M6, M9, M12
- Test du log-rank
- Modèles de Cox univariés : ΔctDNA en continu (log10) et dichotomisé → HR, IC95%, p-value
- **[V3] Analyse systématique des deux métriques en parallèle** : tableau comparatif des HR et C-index pour ΔctDNA_ratio vs. ΔctDNA_quantité à chaque timepoint
- Landmark analysis à chaque timepoint
- Analyse séparée pour chaque baseline (leucaphérèse, J–5, J0) puis comparaison des performances pronostiques (C-index de Harrell)

**Corrélation avec la réponse TEP :**

- Comparaison des niveaux de ΔctDNA entre répondeurs TEP (Deauville ≤ 3) et non-répondeurs : test de Mann-Whitney
- Courbes ROC du ΔctDNA pour la prédiction de la réponse TEP à M3 et M6 : AUC, seuil optimal (Youden)
- **[V3] Corrélation ΔctDNA vs. ΔSUVmax** :
  - Diagramme de dispersion ΔctDNA_ratio vs. ΔSUVmax et ΔctDNA_quantité vs. ΔSUVmax aux timepoints M3 et M6
  - Coefficient de corrélation de Spearman
  - Analyse de concordance : identification des patients discordants (forte décroissance ctDNA mais ΔSUVmax faible, ou inversement) et description de leur profil clinique/évolutif
  - Courbes ROC comparatives : ΔctDNA_ratio, ΔctDNA_quantité et ΔSUVmax pour la prédiction de la PFS (DeLong test pour comparer les AUC)

### 4.3bis [V3] Analyse combinée ctDNA + TEP (modèle intégré)

**Objectif** : évaluer si la combinaison du ctDNA et de la TEP (Deauville et/ou ΔSUVmax) améliore la prédiction pronostique par rapport à chaque biomarqueur seul.

**Méthode :**

- **Classification combinée à M3 et M6** : création d'un score composite en 4 catégories :
  - MRD− / TEP− (Deauville ≤ 3) : double négatif → pronostic attendu favorable
  - MRD− / TEP+ : discordant moléculaire négatif
  - MRD+ / TEP− : discordant moléculaire positif
  - MRD+ / TEP+ : double positif → pronostic attendu défavorable
- Courbes de Kaplan-Meier par catégorie combinée (PFS, OS)
- Test du log-rank global et comparaisons 2 à 2
- Modèles de Cox :
  - Modèle 1 : MRD quali seul
  - Modèle 2 : TEP seule (Deauville binarisé)
  - Modèle 3 : MRD + TEP (additif)
  - Modèle 4 : MRD + TEP + interaction
  - Comparaison par LRT (Likelihood Ratio Test) et C-index
- **Modèle quantitatif combiné** : ΔctDNA (ratio et/ou quantité) + ΔSUVmax en variables continues dans un modèle de Cox bivarié → évaluer l'indépendance pronostique (HR ajustés)
- **Net Reclassification Improvement (NRI)** et **Integrated Discrimination Improvement (IDI)** : quantifier l'apport de l'ajout du ctDNA à la TEP seule (et inversement)

### 4.4 Informativité des échantillons

**Objectif** : évaluer l'impact du nombre de régions couvertes de la watchlist sur la fiabilité du résultat de MRD, et proposer un seuil d'informativité minimum par timepoint.

**Méthode :**

- Distribution du nombre de régions couvertes par timepoint (boxplots) chez les patients MRD+, MRD−, et NI
- Taux de résultats NI en fonction du nombre de régions couvertes : courbe et identification d'un seuil naturel (méthode graphique + analyse de sensibilité)
- Analyses de sensibilité : répéter les analyses 4.1–4.3 en excluant les échantillons en dessous du seuil d'informativité
- Hypothèse spécifique : les faux négatifs (MRD− qui rechutent) ont-ils un nombre de régions couvertes inférieur aux vrais négatifs ? (test de Mann-Whitney)

Note : l'informativité est une caractéristique de l'échantillon (pas du patient). Un patient peut avoir un échantillon informatif à un timepoint et non-informatif à un autre.

### 4.5 Méthodologie de détermination des seuils

La détermination des seuils optimaux de ctDNA (brut et en décroissance) pour la dichotomisation utilisera :

- **Méthode primaire** : maximisation de la statistique du log-rank (maxstat, Hothorn & Lausen). Le seuil maximisant la séparation des courbes de survie sera retenu.
- **Ajustement pour tests multiples** : correction de Lausen & Schumacher (p-value ajustée) pour la recherche de seuil
- **Validation par bootstrap** : estimation de la stabilité du seuil optimal (1000 rééchantillonnages, intervalle du seuil et du HR)
- **Seuils cliniquement pertinents pré-spécifiés** à tester en complément : 1-log, 2-log, 3-log de décroissance
- **Analyse exploratoire en grille bivariée** (heatmap) : tester des combinaisons de seuils ctDNA × TEP ou ctDNA(T1) × ctDNA(T2) si pertinent
- **[V3] Seuils à tester pour les deux métriques séparément** : le seuil optimal en ΔctDNA_ratio peut différer de celui en ΔctDNA_quantité. Les deux seront recherchés indépendamment et comparés.

### 4.6 Analyses multivariées

Les variables significatives en univarié (p < 0.10) seront intégrées dans des modèles de Cox multivariés.

- Sélection descendante (backward stepAIC) avec contrainte de conservation d'au moins un biomarqueur ctDNA dans le modèle
- Variables candidates pour l'ajustement : âge, IPI/aaIPI, nombre de lignes antérieures, sous-type (GCB vs. non-GCB), réfractaire vs. rechute, TMTV, réponse TEP, **[V3] ΔSUVmax**
- Forest plot des HR ajustés pour le modèle final
- C-index de Harrell et Likelihood Ratio Test (LRT) pour évaluer l'apport pronostique incrémental du ctDNA par rapport à un modèle clinique de référence
- **[V3] Comparaison des modèles intégrant ΔctDNA_ratio vs. ΔctDNA_quantité** : sélectionner la métrique la plus performante en multivarié (ou démontrer leur complémentarité)

Note : avec 62 patients et un nombre d'événements probablement limité (PFS à estimer), la puissance multivariée sera restreinte. Le nombre de covariables dans le modèle final ne devra pas dépasser ~1 variable pour 10 événements (règle de Peduzzi).

### 4.7 Analyses exploratoires complémentaires

#### 4.7.1 Cinétique à la rechute

- Comparaison du ctDNA au timepoint précédant la rechute vs. au timepoint de rechute chez les 16 patients en progression (test de Wilcoxon apparié), délai entre dernière MRD et rechute clinique/TEP

#### 4.7.2 Lead-time analysis

- Chez les patients en rechute, déterminer si la réascension du ctDNA précède la rechute clinique/TEP et de combien de temps
- **[V3]** Représentation graphique : waterfall plot du lead-time (jours entre réascension ctDNA et rechute clinique) pour chaque patient en rechute

#### 4.7.3 Analyse par conversion MRD

- Impact du changement de statut MRD (MRD+ → MRD− = conversion ; MRD− → MRD+ = résurgence) sur la survie (modèle de Cox avec covariable temps-dépendante)

#### 4.7.4 CRS/ICANS et ctDNA

- Corrélation entre pic de ctDNA à J14 (relargage tumoral ?) et sévérité du CRS/ICANS
- **[V3]** Distinguer le signal tumoral (quota) du signal inflammatoire (cfDNA total) : le pic de cfDNA total à J14 est-il corrélé au CRS, indépendamment du ctDNA tumoral ?

#### 4.7.5 [V3] Profils de réponse moléculaire (clearance patterns)

**Objectif** : caractériser les patterns de cinétique ctDNA et évaluer leur impact pronostique.

**Classification proposée :**

- **Early molecular responders (EMR)** : MRD négative atteinte à J14 ou M1
- **Late molecular responders (LMR)** : MRD négative atteinte à M3 ou M6
- **Never cleared (NC)** : MRD positive persistante à tous les timepoints disponibles
- **Molecular relapsers (MR)** : MRD négative transitoire suivie de résurgence

**Méthode :**

- Description des effectifs par catégorie
- Courbes de Kaplan-Meier par profil de réponse moléculaire (PFS, OS)
- Test du log-rank et HR par rapport au groupe EMR (référence)
- Description clinique des patients « never cleared » et « molecular relapsers » (facteurs associés : IPI, sous-type, TMTV, produit CAR-T)

#### 4.7.6 [V3] Courbes ROC temps-dépendantes

**Objectif** : évaluer la capacité discriminante du ctDNA à différents timepoints pour prédire la PFS à des horizons temporels définis.

**Méthode :**

- Courbes ROC temps-dépendantes (méthode de Heagerty & Zheng) pour la PFS à 6 mois, 12 mois et 24 mois
- Variables testées : MRD quali, ΔctDNA_ratio, ΔctDNA_quantité, à chaque timepoint de mesure
- AUC(t) en fonction du temps : représentation graphique permettant d'identifier le(s) timepoint(s) et la/les métrique(s) ctDNA les plus performantes
- Comparaison formelle des AUC(t) entre les différentes métriques ctDNA et vs. la TEP (ΔSUVmax)

---

## 5. Aspects méthodologiques transversaux

### 5.1 Gestion des données manquantes

- Analyses en cas complet (complete case) en analyse principale
- Analyse de sensibilité : imputation multiple (MICE) si > 10% de données manquantes sur une variable clé
- Documentation du pattern de données manquantes (MCAR / MAR / MNAR) par timepoint

### 5.2 Corrections pour tests multiples

- Les analyses par timepoint génèrent un grand nombre de tests. Correction de Benjamini-Hochberg (FDR) appliquée pour les comparaisons systématiques à travers les timepoints.
- Les analyses de seuil utilisent la correction de Lausen-Schumacher intégrée dans maxstat.
- Distinction claire entre analyses confirmatoires (objectif principal) et exploratoires (objectifs secondaires).
- **[V3]** L'analyse parallèle des deux métriques (ΔctDNA_ratio et ΔctDNA_quantité) double le nombre de tests. La correction FDR sera appliquée conjointement sur les deux métriques. Toutefois, si l'une des deux métriques est clairement supérieure lors des analyses préliminaires, il sera possible de pré-spécifier une métrique principale et une métrique exploratoire, réduisant la charge de correction.

### 5.3 [V3] Analyse en risques compétitifs

Pour l'OS, la mortalité non liée à la rechute (toxicité, NRM) constitue un risque compétitif. Si le nombre d'événements le permet :

- Estimation des incidences cumulées de rechute/progression et de NRM par la méthode de Aalen-Johansen
- Modèle de Fine & Gray (subdistribution hazard) pour les facteurs associés à la rechute/progression en tenant compte du risque compétitif de NRM
- Comparaison des résultats avec les modèles de Cox cause-spécifiques

### 5.4 Seuil de significativité

Seuil bilatéral α = 0.05 pour les analyses principales. Pour les analyses exploratoires, les p-values seront rapportées sans dichotomisation stricte significatif/non significatif.

### 5.5 Logiciel

R (version ≥ 4.3), avec les packages `survival`, `survminer`, `maxstat`, `rms`, `mice`, `ggplot2`, `data.table`, `forestplot`, **[V3]** `timeROC`, `cmprsk`, `pROC`, `nricens`. Le code sera versionné.

---

## 6. Livrables attendus

1. Tableau 1 : caractéristiques patients
2. Flowchart de disponibilité des échantillons ctDNA par timepoint
3. Courbes de cinétique du ctDNA (spaghetti plots) — **[V3] en parallèle pour les deux métriques delta**
4. Courbes de Kaplan-Meier (PFS et OS) par MRD quali et ΔctDNA, à chaque timepoint pertinent
5. Tableaux récapitulatifs des Cox univariés et multivariés (HR, IC95%, p) — **[V3] pour ΔctDNA_ratio ET ΔctDNA_quantité**
6. Forest plot du modèle multivarié
7. Heatmap de la recherche de seuil bivariée (si applicable)
8. Tableaux de concordance MRD × TEP
9. Courbes ROC du ΔctDNA pour la prédiction TEP
10. Analyse lead-time et cinétique à la rechute
11. **[V3] Courbes de Kaplan-Meier par catégorie combinée ctDNA + TEP (4 groupes)**
12. **[V3] Diagrammes de dispersion ΔctDNA vs. ΔSUVmax**
13. **[V3] Courbes ROC temps-dépendantes AUC(t)**
14. **[V3] Description des profils de réponse moléculaire (clearance patterns)**
15. **[V3] Tableau comparatif des performances pronostiques ΔctDNA_ratio vs. ΔctDNA_quantité**

---

## 7. [V3] Points à résoudre avant analyse

| # | Point | Responsable | Statut |
|---|---|---|---|
| 1 | Clarifier le paradoxe M9 (n=38) < M12 (n=43) : fenêtres de visite ? prélèvements manqués ? | Data management LYSARC | À faire |
| 2 | Fournir les données TEP : Deauville par timepoint, ΔSUVmax, TMTV baseline | Imagerie / LYSARC | À faire |
| 3 | Fournir les données cliniques : PFS, OS, caractéristiques baseline, CRS/ICANS | Data management LYSARC | À faire |
| 4 | Valider la définition et la formule exacte du ΔSUVmax utilisée (vs. baseline ? vs. pool ?) | Investigateur imagerie | À faire |
| 5 | Confirmer la limite de détection du test phased-variants (pour imputation des zéros dans les deltas) | Laboratoire ctDNA | À faire |
| 6 | Différencier les NA (prélèvement non réalisé) des NI (non interprétable) dans la base de données | Laboratoire ctDNA | À faire |
