// Revue de literature ALYCANTE v4 - rédaction analytique fluide
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, LevelFormat, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageBreak, PageNumber, Header, Footer, ImageRun,
  PageOrientation, VerticalAlign
} = require('docx');

const refsData = JSON.parse(fs.readFileSync(path.join(__dirname, 'references.json'), 'utf8')).refs;
const additionalRefs = JSON.parse(fs.readFileSync(path.join(__dirname, 'references_v2.json'), 'utf8')).additional_refs;
const v3Refs = JSON.parse(fs.readFileSync(path.join(__dirname, 'references_v3.json'), 'utf8')).additional_refs_v3;
const allRefs = [...refsData, ...additionalRefs, ...v3Refs].sort((a, b) => a.id - b.id);

const FIG_DIR_V3 = path.join(path.dirname(__dirname), 'figures_v3');

// ============ HELPERS ============
function P(text, opts = {}) {
  const runs = Array.isArray(text) ? text : [new TextRun(text)];
  return new Paragraph({
    children: runs,
    spacing: { before: 80, after: 140, line: 320 },
    alignment: opts.align || AlignmentType.JUSTIFIED,
    indent: { firstLine: 240 },
    ...opts
  });
}
function P0(text, opts = {}) {
  // Paragraphe sans indentation de première ligne (après titre)
  const runs = Array.isArray(text) ? text : [new TextRun(text)];
  return new Paragraph({
    children: runs,
    spacing: { before: 80, after: 140, line: 320 },
    alignment: opts.align || AlignmentType.JUSTIFIED,
    ...opts
  });
}
function H1(text) { return new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 480, after: 200 }, children: [new TextRun({ text, bold: true })] }); }
function H2(text) { return new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 280, after: 140 }, children: [new TextRun({ text, bold: true })] }); }
function H3(text) { return new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 200, after: 120 }, children: [new TextRun({ text, bold: true, italics: true })] }); }
function B(text) { return new TextRun({ text, bold: true }); }
function I(text) { return new TextRun({ text, italics: true }); }
function T(text) { return new TextRun(text); }
function cite(...ids) {
  return new TextRun({ text: '[' + ids.join(',') + ']', superScript: true });
}

// Construit un paragraphe à partir d'un tableau de parts (string | {b} | {i} | {cite})
function para(parts, opts = {}) {
  const runs = parts.map(p => {
    if (typeof p === 'string') return new TextRun(p);
    if (p.cite) return cite(...p.cite);
    if (p.b) return B(p.b);
    if (p.i) return I(p.i);
    return new TextRun(String(p));
  });
  if (opts.first) return P0(runs);
  return P(runs);
}

function bullet(textOrRuns, opts = {}) {
  return new Paragraph({
    numbering: { reference: 'bullets', level: 0 },
    spacing: { before: 40, after: 60, line: 280 },
    children: Array.isArray(textOrRuns) ? textOrRuns : [new TextRun(textOrRuns)]
  });
}

function figureBlock(filename, caption, widthPx = 560) {
  const filePath = path.join(FIG_DIR_V3, filename);
  if (!fs.existsSync(filePath)) return [P([T(`[FIGURE MANQUANTE: ${filename}]`)])];
  const imgData = fs.readFileSync(filePath);
  const w = imgData.readUInt32BE(16);
  const h = imgData.readUInt32BE(20);
  const ratio = h / w;
  const docHeight = Math.round(widthPx * ratio);
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 240, after: 80 },
      children: [new ImageRun({
        type: 'png', data: imgData,
        transformation: { width: widthPx, height: docHeight },
        altText: { title: filename, description: caption, name: filename }
      })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 200 },
      children: [new TextRun({ text: caption, italics: true, size: 19, color: '404040' })]
    })
  ];
}

// ============ TABLES (portrait compact - 10080 DXA total) ============
function buildCARTcomparisonTable() {
  const cellBorder = { style: BorderStyle.SINGLE, size: 1, color: 'BFBFBF' };
  const cellBorders = { top: cellBorder, bottom: cellBorder, left: cellBorder, right: cellBorder };
  const headers = ['Caractéristique', 'Axi-cel (Yescarta)', 'Tisa-cel (Kymriah)', 'Liso-cel (Breyanzi)'];
  const colW = [2400, 2560, 2560, 2560];

  const rows = [
    ['Fabricant', 'Kite / Gilead', 'Novartis', 'BMS / Celgene'],
    ['Costimulation', 'CD28', '4-1BB', '4-1BB'],
    ['Manufacture', 'CD4+CD8 combines', 'CD4+CD8 combines', 'CD4 et CD8 separes (1:1)'],
    ['AMM 3L+ (DLBCL)', 'FDA 2017, EMA 2018', 'FDA 2018, EMA 2018', 'FDA 2021, EMA 2022'],
    ['AMM 2L (DLBCL)', 'FDA 2022 (ZUMA-7)', 'Non en 2L', 'FDA 2022 (TRANSFORM)'],
    ['Essai pivot 3L+', 'ZUMA-1', 'JULIET [113]', 'TRANSCEND NHL 001 [31]'],
    ['Essai pivot 2L', 'ZUMA-7 (n=359) [18,43]', '-', 'TRANSFORM (n=184) [90]'],
    ['ORR (3L+, pivot)', '83% (axi-cel 2L)', '~52%', '73%'],
    ['CR rate (3L+, pivot)', '65% (axi-cel 2L)', '~40%', '53%'],
    ['EFS median 2L', '8.3 mois vs 2.0 (HR 0.40) [18]', '-', 'Superieur a ASCT [90]'],
    ['OS 4 ans 2L', '54.6% vs 46% SOC (HR 0.73) [43]', '-', 'Superieur a ASCT'],
    ['CRS toute grade', '92-93%', '58%', '42%'],
    ['CRS grade >=3', '11-13%', '22%', '2% (le plus bas)'],
    ['ICANS toute grade', '64-74%', '21%', '30%'],
    ['ICANS grade >=3', '21-32%', '12%', '10%'],
    ['Profil de tolerance', 'Le plus toxique', 'Intermediaire', 'Le plus favorable'],
    ['Patient frail/age', 'Hospitalisation usuelle', 'Tolerance moyenne', 'Ambulatoire possible'],
    ['Cohorte Lea (n=158)', '104 (65.8%)', '23 (14.6%)', '28 (17.7%)'],
    ['Etude ALYCANTE (n=62)', '62 (100%) en 2L non-ASCT [45]', '-', '-'],
    ['Etudes post-CAR-T glofitamab', '52/154 [94]', 'LYSA [97]', 'LYSA [97]']
  ];

  const headerRow = new TableRow({
    tableHeader: true,
    children: headers.map((h, i) => new TableCell({
      borders: cellBorders, width: { size: colW[i], type: WidthType.DXA },
      shading: { fill: '2F5496', type: ShadingType.CLEAR },
      margins: { top: 80, bottom: 80, left: 100, right: 100 },
      verticalAlign: VerticalAlign.CENTER,
      children: [new Paragraph({
        alignment: AlignmentType.CENTER, spacing: { before: 0, after: 0 },
        children: [new TextRun({ text: h, bold: true, color: 'FFFFFF', size: 17 })]
      })]
    }))
  });
  const dataRows = rows.map(row => new TableRow({
    children: row.map((cell, i) => new TableCell({
      borders: cellBorders, width: { size: colW[i], type: WidthType.DXA },
      margins: { top: 60, bottom: 60, left: 100, right: 100 },
      verticalAlign: VerticalAlign.TOP,
      children: [new Paragraph({
        spacing: { before: 0, after: 0, line: 220 },
        children: [new TextRun({ text: cell, size: 15, bold: i === 0 })]
      })]
    }))
  }));
  return new Table({
    width: { size: 10080, type: WidthType.DXA },
    columnWidths: colW, rows: [headerRow, ...dataRows]
  });
}

function buildMethodsTable() {
  const cellBorder = { style: BorderStyle.SINGLE, size: 1, color: 'BFBFBF' };
  const cellBorders = { top: cellBorder, bottom: cellBorder, left: cellBorder, right: cellBorder };
  // Compact portrait : 5 colonnes au lieu de 7 (fusion LoD+Biopsie et Avantages+Limites)
  const headers = ['Méthode', 'Approche', 'LoD / Biopsie', 'Forces & limites', 'Études clés'];
  const colW = [1600, 2400, 1400, 2580, 2100];
  const rows = [
    ['IgH-NGS / clonotype VDJ', 'Clonotype Ig dominant tissu puis quantification plasma', '~1 ppm — Biopsie : oui', '+ Spécifique tumeur, sensible, tout B-NHL\n– Nécessite biopsie informative', 'Roschewski 2015 [2], Frank 2021 [25], Wang 2025 [69]'],
    ['CAPP-Seq', 'Panel cible récurrent + UMI deep sequencing', '~1-10 ppm — Tumor-naive', '+ Génotypage simultané, LymphGen sur plasma\n– Coût, expertise bioinfo', 'Scherer 2016 [3], Kurtz 2018 [5], Alig 2021 [21], Moia 2025 [68]'],
    ['PhasED-Seq', 'Variants phasés co-localisés (réduction bruit de fond)', '~0.7 ppm — Recommandée', '+ Sensibilité ultra-élevée, idéal MRD\n– Coût élevé', 'Kurtz 2021 [26], Klimova 2025 [71], Roschewski 2025 [75], Stepan 2026 [90]'],
    ['Signatera (mPCR)', 'Panel multiplex 16 SNV tumor-informed', '~1-10 ppm — Oui', '+ Workflow commercial automatisé\n– Limité à 16 SNV', 'Narkhede 2024 [65]'],
    ['EuroClonality-NDC', 'Panel NGS standardisé européen', '~10⁻⁵ — Plasma seul', '+ Standardisation européenne\n– Sensibilité < PhasED-Seq', 'Alcoceba 2024 [62]'],
    ['CLEARS (521 gènes)', 'Panel étendu mutations lymphome', '~10⁻⁴-10⁻⁵ — Non requise', '+ Couverture génique étendue\n– Recouvrement variable', 'Vodicka 2025 [76], Hamova 2025 [81]'],
    ['ULP-WGS cfDNA', 'WGS faible profondeur (CNV/burden)', 'TF > 3 % — Non', '+ Faible coût, détecte CNV/del17p\n– Sensibilité limitée MRD', 'Zhao 2025 [74]'],
    ['ddPCR (single mut)', 'PCR digitale, mutation spécifique', '~10⁻³-10⁻⁴ — Oui', '+ Coût faible, rapide\n– Une seule cible', 'Cas reports [72]'],
    ['Flow cytometry MRD', 'Phénotype B clonal résiduel', '~10⁻⁴ — Moelle', '+ Bien établi en LA\n– Peu applicable DLBCL', 'Liu 2023 [54]'],
    ['cfDNA 5hmC-Seal', 'Profilage épigénétique', '~10⁻⁴ — Non', '+ Approche épigénétique novatrice\n– Méthodologie de recherche', 'Chiu 2019 [13]'],
    ['Exosomes / EV', 'Isolation vésicules tumor-derived', 'Variable — Non', '+ Info RNA + protéique\n– Standardisation manquante', 'Ofori 2020 [14]']
  ];
  const headerRow = new TableRow({
    tableHeader: true,
    children: headers.map((h, i) => new TableCell({
      borders: cellBorders, width: { size: colW[i], type: WidthType.DXA },
      shading: { fill: '2F5496', type: ShadingType.CLEAR },
      margins: { top: 80, bottom: 80, left: 100, right: 100 },
      verticalAlign: VerticalAlign.CENTER,
      children: [new Paragraph({
        alignment: AlignmentType.CENTER, spacing: { before: 0, after: 0 },
        children: [new TextRun({ text: h, bold: true, color: 'FFFFFF', size: 16 })]
      })]
    }))
  });
  const dataRows = rows.map(row => new TableRow({
    children: row.map((cell, i) => new TableCell({
      borders: cellBorders, width: { size: colW[i], type: WidthType.DXA },
      margins: { top: 60, bottom: 60, left: 100, right: 100 },
      verticalAlign: VerticalAlign.TOP,
      children: [new Paragraph({
        spacing: { before: 0, after: 0, line: 220 },
        children: [new TextRun({ text: cell, size: 14 })]
      })]
    }))
  }));
  return new Table({ width: { size: 10080, type: WidthType.DXA }, columnWidths: colW, rows: [headerRow, ...dataRows] });
}

// ============ COVER + PREAMBLE ============
function buildCover() {
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 2400, after: 240 }, children: [new TextRun({ text: 'Revue de littérature exhaustive', bold: true, size: 36 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 360 }, children: [new TextRun({ text: 'Etude ALYCANTE - ctDNA dans le lymphome diffus a grandes cellules B (DLBCL)', bold: true, size: 28 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 }, children: [new TextRun({ text: 'Suivi longitudinal post-CAR-T, modèles a classes latentes joints et positionnement dans le paysage thérapeutique 2026', italics: true, size: 22 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 720, after: 180 }, children: [new TextRun({ text: 'Reunion LYSARC 2026', size: 24 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 180 }, children: [new TextRun({ text: 'Service d Immunologie Biologique - Secteur Maladies Lymphoproliferatives, AP-HP', size: 22 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 480 }, children: [new TextRun({ text: 'Version 4 (rédaction analytique) - 11 mai 2026', size: 22 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 720 }, children: [new TextRun({ text: '120 references PubMed vérifiées - 5 figures de synthese - 2 tableaux comparatifs', italics: true, size: 20 })] }),
    new Paragraph({ children: [new PageBreak()] })
  ];
}

function buildPreambule() {
  return [
    H1('Preambule'),
    para([
      'Le lymphome diffus a grandes cellules B reste, malgré les progres thérapeutiques accumules depuis l’avenement du R-CHOP, une maladie ou la rechute précoce demeure fréquente et le pronostic incertain pour 20 à 50 % des patients. Dans ce contexte, deux innovations bouleversent simultanement la prise en charge du DLBCL R/R : d’une part les CAR-T cells anti-CD19, dont l’indication s est etendue de la troisième ligne (',
      { i: 'ZUMA-1, JULIET, TRANSCEND' },
      ') à la deuxième ligne (',
      { i: 'ZUMA-7, TRANSFORM' },
      ') et, récemment, à la deuxième ligne chez les patients non éligibles à l’autogreffe avec l’étude ',
      { b: 'ALYCANTE' },
      ' ; et d’autre part, l’essor du suivi par ADN tumoral circulant (ctDNA), qui permet une évaluation moléculaire non invasive plus précoce et plus sensible que l’imagerie métabolique.'
    ], { first: true }),
    para([
      'La présente revue accompagne le travail biostatistique de l’étude ALYCANTE-biomarqueurs (n = 57 patients, 421 mesures ctDNA longitudinales) présentée à la reunion LYSARC 2026. Elle vise a situer l’originalité méthodologique du projet - l’application des modèles a classes latentes joints (JLCM) au suivi du ctDNA - dans le paysage international des biomarqueurs du DLBCL post-CAR-T. Elle intègre egalement les développements thérapeutiques qui modifient le pronostic et la trajectoire de soins de cette population : anticorps bispécifiques CD20xCD3, complications immunologiques iatrogenes (CRS, ICANS, ICAHT) et perspectives dans le lymphome primaire du système nerveux central.'
    ]),
    H2('Methodologie de la recherche bibliographique'),
    para([
      'Les references ont été identifiées par interrogations systématiques de PubMed (via l’API officielle NCBI E-utilities) sur la période 2014-2026, en croisant les termes MeSH appropries pour onze thematiques : ctDNA pronostic dans le DLBCL, ctDNA post-CAR-T, méthodes analytiques (CAPP-Seq, PhasED-Seq, IgH-NGS), essais cliniques CAR-T pivots, imagerie métabolique PET et réponse selon les critères de Lugano, modèles statistiques longitudinaux a classes latentes, anticorps bispécifiques CD20xCD3, complications immunologiques post-CAR-T, méta-analysés quantitatives des hazard ratios ctDNA, lymphome primaire du SNC, et methodologies comparees de détection. Chaque reference a fait l’objet d’un appel API ',
      { i: 'get_article_metadata' },
      ' garantissant l’exactitude des informations bibliographiques (PMID, DOI, auteurs, journal, date) ; aucune reference n’a été generee de novo. Le corpus final compte 120 publications uniques après deduplication.'
    ]),
    para([
      'Trois precautions méthodologiques meritent d être soulignees. Premierement, les resultats chiffres rapportés (médianes, hazard ratios, intervalles de confiance, taux de réponse) proviennent exclusivement des abstracts ou textes complets des publications referencees ; tout chiffre cite peut être retrace via le PMID indique. Deuxiemement, plusieurs travaux de 2026 sont actuellement ',
      { i: 'in press' },
      ' et leurs volumes/pages restent provisoires. Troisiemement, l’hétérogénéité des méthodes de quantification du ctDNA limite la comparabilite directe des seuils entre études : un seuil de 2.5 log hGE/mL en CAPP-Seq ne saurait être transpose tel quel en PhasED-Seq, dont la sensibilité analytique est supérieure de plus de deux ordres de grandeur.'
    ]),
    H2('Plan du document'),
    para([
      'L’exposition suit un cheminement allant du contexte clinique général (sections 1 à 2) aux methodologies analytiques (section 3), puis à la valeur pronostique du ctDNA dans ses dimensions baseline (section 4), dynamique (section 5) et post-CAR-T (section 6). La section 7 confronte le ctDNA à l’imagerie métabolique de reference, tandis que la section 8 detaille la méthodologie statistique des modèles a classes latentes joints qui constitue l’originalité analytique d ALYCANTE. Les sections 11 à 13 abordent les développements thérapeutiques récents (bispécifiques CD20xCD3, complications immunologiques) et la synthese quantitative méta-analytique. Les sections 14 et 15 traitent respectivement du comparatif entre les trois produits CAR-T et de la spécificité du lymphome primaire du SNC. La section 16, conclusive, synthese les implications du projet ALYCANTE et discute les perspectives ouvertes par ses resultats.'
    ]),
    new Paragraph({ children: [new PageBreak()] })
  ];
}

// ============ SECTION 1 ============
function buildSection1() {
  return [
    H1('1. Contexte clinique : DLBCL et positionnement de l’étude ALYCANTE'),
    H2('1.1. Une maladie heterogene encore imparfaitement stratifiee'),
    para([
      'Premier lymphome non hodgkinien en fréquence, le DLBCL est curable dans environ 60 % des cas par R-CHOP, mais reste responsable d’une rechute précoce ou d’une réfractarité chez 20 à 50 % des patients ',
      { cite: [14, 47, 77] },
      '. Cette dispersion des trajectoires cliniques traduit une heterogeneite biologique profonde, que les indices pronostiques cliniques classiques (IPI, R-IPI, NCCN-IPI) ne capturent que partiellement. L’émergence des classifications moléculaires - cellule d’origine (GCB versus non-GCB) puis sous-groupes génomiques LymphGen (EZB, BN2, MCD, N1, ST2) - a affine la compréhension de la biologie tumorale, sans pour autant guider de manière reproductible l’individualisation des strategies thérapeutiques en routine ',
      { cite: [68] },
      '.'
    ], { first: true }),
    para([
      'Cette limite de la stratification clinico-biologique baseline a conduit au développement de marqueurs dynamiques. Les paramètres tumoraux volumetriques mesures par 18F-FDG-PET (TMTV, TLG, IMPI) ont apporte une dimension quantitative au-dela des critères de Lugano ',
      { cite: [1, 32, 35, 50] },
      ', tandis que le ctDNA - objet central de cette revue - intègre simultanement information sur la masse tumorale, génotype, et dynamique de réponse. C est dans ce paysage en mutation rapide que se positionne l’étude ALYCANTE.'
    ]),
    H2('1.2. Place des CAR-T cells dans le DLBCL R/R'),
    para([
      'L’approbation réglementaire des trois CAR-T anti-CD19 - axicabtagène ciloleucel (axi-cel), tisagenlecleucel (tisa-cel) et lisocabtagène maraleucel (liso-cel) - a profondément modifié l’histoire naturelle du DLBCL R/R ',
      { cite: [19, 31, 113, 118] },
      '. La section 14 et le Tableau 2 detaillent leurs caractéristiques comparees ; on retiendra ici que les trois produits différent non seulement par leur domaine de costimulation (CD28 pour axi-cel, 4-1BB pour les deux autres), mais aussi par leur profil de tolerance, leur procede de fabrication et leur cible d AMM.'
    ], { first: true }),
    para([
      'Au-dela de la troisième ligne, deux essais randomises ont valide en 2021-2022 l’utilisation des CAR-T en deuxième ligne. ZUMA-7 a démontré la supériorité de l’axi-cel sur le standard de soins (chimiothérapie de rattrapage suivie d ASCT) avec une médiane d EFS portee de 2.0 à 8.3 mois (HR 0.40 ; IC95 0.31-0.51 ; p < 0.001) et une survie globale a quatre ans de 54.6 % contre 46 % (HR 0.73 ; p = 0.03) ',
      { cite: [18, 43] },
      '. TRANSFORM a confirme un bénéfice analogue pour le liso-cel, avec un argument biologique supplementaire : la profondeur et la duree de la réponse moléculaire mesurees par ctDNA-MRD étaient significativement supérieures dans le bras CAR-T par rapport au bras ASCT ',
      { cite: [90] },
      ', ce qui constitue un argument fort en faveur de l’interet du ctDNA comme critère de substitution.'
    ]),
    H2('1.3. L’originalite de l’étude ALYCANTE'),
    para([
      'L’étude ALYCANTE (NCT04531046) repond à une question laissee ouverte par ZUMA-7 et TRANSFORM, qui n incluaient que des patients éligibles à l’autogreffe. Or, dans la pratique reelle, près de la moitie des patients DLBCL R/R en seconde ligne ne le sont pas, soit en raison de comorbidites, soit en raison de l’age. ALYCANTE, étude de phase 2 multicentrique francaise, évalué spécifiquement l’axi-cel dans cette population fragile : sur 62 patients inclus, le taux de réponse métabolique complète (CMR) a trois mois - critère principal - atteint 71 % (IC95 58-82 %), avec une PFS médiane de 11.8 mois et un profil de toxicite comparable a celui des essais pivots (CRS de grade supérieur ou egal à 3 chez 8.1 %, neurotoxicite de grade supérieur ou egal à 3 chez 14.5 %) ',
      { cite: [45] },
      '. Les données de qualité de vie publiees ulterieurement ',
      { cite: [86] },
      ' montrent même une recuperation a trois mois supérieure a celle observee dans ZUMA-7, suggerant que la population éligible à ALYCANTE n’est pas plus penalisee que les patients plus fits dans le contexte d’un CAR-T 2L.'
    ], { first: true }),
    H2('1.4. La question biomarqueur que pose ALYCANTE'),
    para([
      'La reussite clinique d ALYCANTE pose immediatement la question de l’identification précoce des patients qui beneficieront durablement du traitement, et de ceux qui rechuteront. La CMR par PET a trois mois, bien que critère principal d évaluation, présente plusieurs limites : elle est tardive, son interprétation peut être perturbee par l’inflammation post-CAR-T résiduelle, et sa spécificité pour la maladie active reste imparfaite. Le suivi longitudinal du ctDNA (',
      { b: '421 mesures sur 57 patients' },
      ', des prélèvements de leucaphérèse jusqu’à vingt-quatre mois post-infusion) offre une alternative et un complément attractifs.'
    ], { first: true }),
    para([
      'Le projet biomarqueur ALYCANTE se distingue par plusieurs choix originaux. Premierement, il évalué la valeur pronostique du ctDNA en termes de delta ratio (log10[quota(Tx)/quota(BL)]) plutot que de quantité absolue, ce qui standardise les comparaisons entre patients aux burdens initiaux différents. Deuxiemement, il applique un ',
      { b: 'modèle a classes latentes joint (JLCM)' },
      ' - approche emergente decrite en detail en section 8 - pour identifier des sous-classes de trajectoires ctDNA correlees au risque d’événement. Troisiemement, il confronte directement la classification JLCM tronquee a J14 avec la CMR PET M3, dans le but de démontrer une supériorité prédictive du marqueur moléculaire précoce sur l’imagerie tardive.'
    ]),
    H2('1.5. Schema synoptique du protocole'),
    para([
      'La Figure 5 schematise le deroulement temporel du protocole et la position des biomarqueurs : leucaphérèse pre-traitement (J-30 a J-5), lymphodepletion par fludarabine-cyclophosphamide, reinfusion d axi-cel a J0, mesures ctDNA aux temps J14, M1, M3, M6, M9 et M12, et évaluations PET aux mêmes timepoints. Le critère principal CMR M3 est mis en exergue. Cette représentation permet de visualiser le decalage temporel entre les mesures moléculaires précoces (J14 a M1) et l’évaluation clinique du critère principal (M3), justifiant l’interet pronostique potentiel des marqueurs précoces.'
    ], { first: true }),
    ...figureBlock('fig5_protocole_ALYCANTE.png',
      'Figure 5. Schema synoptique du protocole ALYCANTE. Timeline des visites clés et insertion des mesures longitudinales ctDNA (n = 421 observations / 57 patients) intégrées au modèle JLCM. La CMR M3, critère principal de l’essai, est mise en évidence.', 560)
  ];
}

// ============ SECTION 2 ============
function buildSection2() {
  return [
    H1('2. Le ctDNA dans les lymphomes B agressifs : principes généraux'),
    H2('2.1. Definition et biologie de la cellule à la circulation'),
    para([
      'L’ADN tumoral circulant (',
      { i: 'circulating tumor DNA' },
      ', ctDNA) designe la fraction d ADN extracellulaire derivant des cellules tumorales et liberee dans le plasma sanguin, principalement par apoptose. Les fragments mesurent typiquement entre 140 et 170 paires de bases, taille caractéristique des nucleosomes, et constituent un sous-ensemble d’un pool plus large d ADN libre circulant (cfDNA) dont la majorite provient des leucocytes normaux. Cette dilution du signal tumoral dans un bruit de fond important pose le defi analytique central : la détection du ctDNA exige des méthodes capables d’identifier de très faibles fractions tumorales, jusqu’à une partie par million dans les approches les plus sensibles ',
      { cite: [4, 7, 27, 67, 111] },
      '. La revue méthodologique de Fu et coll. (2025) ',
      { cite: [111] },
      ' propose une synthese actualisee des plateformes disponibles.'
    ], { first: true }),
    para([
      'Dans le DLBCL spécifiquement, deux approches dominent. La première repose sur la détection et la quantification des rearrangements V(D)J du recepteur d immunoglobuline (IgH, IgK, IgL), uniques pour chaque clone tumoral et stables au cours de l’évolution ; elle necessite l’identification prealable du clonotype dominant sur un échantillon tissulaire au diagnostic. La seconde repose sur le suivi simultane de multiples mutations somatiques par sequencage cible profond, et à l’avantage majeur de ne pas requerir de biopsie informative prealable. La quantité de ctDNA est habituellement exprimee en ',
      { b: 'hGE/mL' },
      ' (',
      { i: 'haploid génome equivalents per milliliter' },
      ') ou, plus fréquemment en pratique, en log10 de cette grandeur, transformation qui linearise les distributions très asymetriques observees dans les populations de patients. Avec les méthodes contemporaines, le ctDNA est détectable chez 90 à 98 % des patients DLBCL au diagnostic ',
      { cite: [5, 21, 50, 62, 65] },
      '.'
    ]),
    H2('2.2. Une panoplie d utilites cliniques, encore inégalement validees'),
    para([
      'L’interet clinique du ctDNA dans le DLBCL se décline en cinq utilites complémentaires, dont la maturité varie considérablement. Le ',
      { b: 'génotypage non invasif' },
      ' permet d’identifier des mutations somatiques récurrentes (TP53, KMT2D, CARD11, MYD88, B2M, EZH2) et de classer les tumeurs selon la cellule d’origine ou les sous-groupes LymphGen directement sur plasma, avec une concordance supérieure à 95 % par rapport aux biopsies tissulaires ',
      { cite: [3, 29, 36, 68] },
      '. Cette dimension diagnostique transforme la prise en charge des situations ou la biopsie est inaccessible ou non informative.'
    ], { first: true }),
    para([
      'L ',
      { b: 'estimation de la masse tumorale' },
      ' constitue la deuxième application validee : les niveaux baseline de ctDNA sont fortement correles aux marqueurs traditionnels (LDH, stade Ann Arbor, IPI) et plus particulièrement au TMTV mesure par PET, avec des coefficients de Spearman compris entre 0.37 et 0.7 selon les études ',
      { cite: [21, 50, 52, 74] },
      '. Cette correlation offre une alternative non invasive et quantitative au TMTV, particulièrement utile lorsque l’acces à une plateforme de quantification métabolique automatisee fait defaut.'
    ]),
    para([
      'Les trois utilites suivantes relevent du suivi temporel et constituent le cœur de la présente revue. La ',
      { b: 'réponse moléculaire précoce' },
      ', formalisee par les seuils EMR/MMR de Kurtz et coll. ',
      { cite: [5] },
      ', identifié des le premier ou deuxième cycle de chimiothérapie les patients dont la trajectoire pronostique est favorable. La ',
      { b: 'maladie résiduelle measurable' },
      ' (MRD) en fin de traitement, dont la valeur pronostique surpasse celle de la réponse PET selon les données récentes ',
      { cite: [26, 71, 75, 90] },
      ', ouvre la voie à une redefinition de la remission. Enfin, la ',
      { b: 'surveillance post-remission' },
      ' permet de détecter une rechute moléculaire trois a six mois avant l’apparition de la rechute clinique radiologique ',
      { cite: [2, 25, 67] },
      ', avec des implications majeures pour la mise en place précoce d’une thérapie de sauvetage.'
    ])
  ];
}

// ============ SECTION 3 ============
function buildSection3() {
  return [
    H1('3. Methodes de détection du ctDNA dans le DLBCL'),
    para([
      'Le choix de la méthode de détection conditionne directement la sensibilité, la spécificité et l’utilite clinique du ctDNA. Le Tableau 1 (section 13) et la Figure 3 synthetisent les onze plateformes principales selon leur limite de détection, leur necessite ou non de biopsie tissulaire prealable, et leur degre de validation clinique. Trois familles meritent une description detaillee.'
    ], { first: true }),
    H2('3.1. IgH-NGS et sequencage clonotypique V(D)J'),
    para([
      'L’approche pionnière développée par Roschewski, Wilson et coll. au NIH ',
      { cite: [2, 4, 12] },
      ' repose sur l’identification, sur tissu tumoral, du clonotype V(D)J dominant du recepteur d immunoglobuline. Ce clonotype, unique pour chaque tumeur, est ensuite quantifie série après série dans le plasma par sequencage profond. La sensibilité analytique atteint environ une cellule tumorale par million de cellules normales (1 ppm) et la spécificité tumorale est très élevée, les rearrangements V(D)J etant intrinsequement absents des cellules non lymphoides B circulantes. La plateforme commerciale clonoSEQ (Adaptive Biotechnologies) est largement utilisee dans cette approche.'
    ], { first: true }),
    para([
      'La principale limite de cette méthode reside dans son exigence d’une biopsie tissulaire informative au diagnostic, ce qui peut être problématique dans le contexte de tumeurs profondes, transformees ou de lymphomes a faible cellularité. L’ajout du sequencage IgK aux IgH augmente sensiblement le taux de détection clonotypique, de 43 % à 58 % dans la cohorte de 33 patients de Wang et coll. (2025) ',
      { cite: [69] },
      ', ce qui suggere une optimisation possible de la sensibilité par multiplexage des rearrangements cibles.'
    ]),
    H2('3.2. CAPP-Seq, le standard tumor-naive'),
    para([
      'Developpee par les equipes de Diehn et Alizadeh a Stanford, la technologie ',
      { i: 'Cancer Personalized Profiling by Deep Sequencing' },
      ' (CAPP-Seq) ',
      { cite: [3, 5, 11, 21, 80] },
      ' utilise un panel cible de regions génomiques fréquemment alterees dans le DLBCL (typiquement 250 à 500 kilobases), sequencees a haute profondeur avec utilisation de codes-barres moléculaires uniques (',
      { i: 'unique molecular identifiers' },
      ', UMI) qui permettent la correction des erreurs de sequencage. La limite de détection se situe entre 10 et 1 ppm selon l’input d ADN et la profondeur atteinte.'
    ], { first: true }),
    para([
      'L’avantage decisif du CAPP-Seq sur l’IgH-NGS est son caractère ',
      { b: 'tumor-naive' },
      ' : aucune biopsie tissulaire prealable n’est requise puisque le panel cible des mutations fréquentes dans la population DLBCL. Cette propriete simplifie l’implementation clinique et autorisé l’analyse retrospective de cohortes ou les biopsies tissulaires ne sont pas disponibles. CAPP-Seq permet en outre une caractérisation genotypique simultanee, ouvrant la voie à la classification LymphGen sur plasma, comme l’ont démontré Moia et coll. (2025) qui rapportent une concordance de 96 % entre les classes assignees sur ctDNA et sur tissu (n = 77) ',
      { cite: [68] },
      '. Le panel CLEARS (Clinical Lymphoma Exploration And Research Sequencing, 521 genes) développé par l’equipe tcheque ',
      { cite: [81] },
      ' représenté une déclinaison europeenne contemporaine de cette approche.'
    ]),
    H2('3.3. PhasED-Seq, l’ultra-sensibilité par les variants phases'),
    para([
      'Introduit en 2021 par Kurtz, Alizadeh et coll. ',
      { cite: [26] },
      ', le sequencage des variants phases (PhasED-Seq) exploite un principe biophysique elegant : lorsque deux mutations somatiques sont localisees sur le même fragment d ADN (typiquement moins de 170 paires de bases), leur co-détection augmente exponentiellement la spécificité du signal et réduit drastiquement le bruit de fond. La limite de détection rapportée atteint 0.7 ppm avec 95 % de détection à partir de 120 nanogrammes d ADN d’entrée, soit une amélioration de plus d’un ordre de grandeur sur CAPP-Seq classique. Le taux de faux positifs analytique est de 0.24 % et le taux d’erreur de fond de 1.95 × 10⁻⁸, valeurs validees prospectivement par Klimova et coll. (2025-2026) ',
      { cite: [71, 89] },
      '.'
    ], { first: true }),
    para([
      'L’impact clinique de cette gain de sensibilité est démontré par les données originelles de Kurtz et coll. : parmi les patients considérés comme MRD-negatifs après deux cycles de chimiothérapie selon CAPP-Seq, 25 % présentent encore du ctDNA détectable par PhasED-Seq, et leur pronostic est significativement plus defavorable ',
      { cite: [26] },
      '. Cette observation suggere que la sensibilité analytique limite directement la valeur pronostique du marqueur, et que les seuils de remission moléculaire définis avec des méthodes moins sensibles sous-estiment systématiquement la maladie résiduelle. PhasED-Seq a depuis été utilise dans plusieurs études pivotales, incluant TRANSFORM ',
      { cite: [90] },
      ' et l’analyse poolée LBCL de Roschewski et coll. (2025) ',
      { cite: [75] },
      ' qui sera detaillee en section 7.'
    ]),
    H2('3.4. Methodes complémentaires et emergentes'),
    para([
      'Plusieurs autres approches occupent des niches spécifiques. ',
      { b: 'Signatera' },
      ' (Natera) repose sur un panel multiplex PCR de seize mutations somatiques personnalisees, identifiées sur biopsie initiale ; commercialise pour plusieurs tumeurs solides, son application au DLBCL a été validee par Narkhede et coll. (2024, n = 50) avec une clairance ctDNA après un cycle predisant une amélioration spectaculaire de l’EFS (HR 6.5) et un avancement de la détection de réponse complète de 97 jours par rapport à l’imagerie ',
      { cite: [65] },
      '. La plateforme ',
      { b: 'EuroClonality-NDC' },
      ' constitue l’effort de standardisation europeen, intégrée dans plusieurs études multicentriques ',
      { cite: [62] },
      '.'
    ], { first: true }),
    para([
      'A l’autre extrême du spectre cout-sensibilité, le sequencage du génome entier a faible profondeur (',
      { b: 'ULP-WGS' },
      ', environ 0.1×) propose par Zhao et coll. (2025) ',
      { cite: [74] },
      ' permet l’estimation de la fraction tumorale et la détection de pertes chromosomiques majeures (notamment del(17p)) a cout réduit, au prix d’une sensibilité limitée à des fractions tumorales supérieures à 3 %. La ',
      { b: 'PCR digitale (ddPCR) ' },
      ' sur une mutation unique offre une approche bon marche et rapide adaptee à la surveillance ciblee, mais ne permet pas de génotypage tumoral exhaustif. Enfin, des approches plus exploratoires - profilage epigenetique 5-hydroxymethylcytosines ',
      { cite: [13] },
      ', exosomes et vesicules extracellulaires ',
      { cite: [14] },
      ' - elargissent le champ des biomarqueurs accessibles depuis le compartiment plasmatique, mais leur validation clinique reste préliminaire.'
    ]),
    para([
      'Cette panoplie méthodologique pose la question récurrente, dans la littérature comme dans les essais cliniques, de la ',
      { b: 'standardisation' },
      ' : un seuil de positivite défini par CAPP-Seq n’est pas directement applicable a PhasED-Seq, et les comparaisons entre études sont compromises par cette heterogeneite. Le roadmap propose par Goldstein, Alizadeh et coll. (2026) ',
      { cite: [91] },
      ' pour la validation de la MRD comme critère de substitution dans les essais de phase précoce souligne explicitement ce defi.'
    ])
  ];
}

// ============ SECTION 4 ============
function buildSection4() {
  return [
    H1('4. Valeur pronostique du ctDNA baseline au diagnostic'),
    H2('4.1. Le ctDNA comme reflet quantitatif de la masse tumorale'),
    para([
      'Le premier rôle pronostique du ctDNA est celui d’un indicateur quantitatif de la charge tumorale globale, complémentaire des marqueurs cliniques traditionnels. Les niveaux de ctDNA pre-traitement sont fortement correles aux LDH seriques, au stade Ann Arbor, à l’IPI et surtout au TMTV mesure par 18F-FDG-PET. Dans la cohorte multicentrique de 267 patients d Alig, Kurtz et coll. (2021) ',
      { cite: [21] },
      ', les niveaux de ctDNA correlent significativement avec ces trois marqueurs (p < 0.001 pour chacun), et le coefficient de Spearman avec le TMTV atteint 0.37. Surtout, le ctDNA baseline reste un prédicteur independant de l’EFS après ajustement multivarié sur l’IPI et l’intervalle diagnostic-traitement (DTI), avec un hazard ratio de 1.5 par log d augmentation (IC95 1.2-2.0).'
    ], { first: true }),
    para([
      'Cette association ctDNA-burden à une implication conceptuelle importante : le ctDNA capture non seulement la masse tumorale visible (TMTV) mais aussi probablement la dynamique de renouvellement cellulaire tumoral, ce qui pourrait expliquer pourquoi il apporte une information independante de l’imagerie. Cette dimension ',
      { b: 'biologique active' },
      ' du ctDNA, par opposition à la mesure statique du volume métabolique, motive son interet pour la prédiction d évolution.'
    ]),
    H2('4.2. Seuils pronostiques en immunochimiotherapie frontline'),
    para([
      'La définition d’un seuil ctDNA permettant de stratifier les patients en groupes de risque distincts est un objectif méthodologique majeur, mais les valeurs proposees varient selon les méthodes et les cohortes. Kurtz et coll. (2018), dans leur étude princeps de 217 patients ',
      { cite: [5] },
      ', proposent un seuil de 2.5 log10 hGE/mL en CAPP-Seq, au-dela duquel l’EFS et l’OS sont significativement réduits. Le Goff, Blanc-Durand et coll. (2023) dans une cohorte real-world de 112 patients évalués par un panel de 40 genes ',
      { cite: [50] },
      ' identifient un seuil legerement différent (3.57 log hGE/mL) au-dela duquel la PFS à un an chute de 83 % à 44 %. Plus récemment, Moia et coll. (2025) ',
      { cite: [68] },
      ' ont propose une approche integrant le seuil ctDNA (2.5 log) avec la classification moléculaire LymphGen : les patients du sous-groupe ST2/BN2 avec ctDNA faible ont un pronostic excellent (PFS 4 ans 87.5 %, OS 100 %), tandis que les autres clusters avec ctDNA élevé ont une PFS 4 ans de 38 %. Cette intégration ctDNA + sous-type moléculaire amélioré le C-index pronostique de 0.59 à 0.63 pour la PFS et de 0.63 à 0.68 pour l’OS.'
    ], { first: true }),
    para([
      'La disparite des seuils entre études (2.5 vs 3.57 log) refleterait moins une divergence biologique fondamentale qu’une différence de sensibilité et de normalisation entre méthodes analytiques. Cette observation renforce la necessite d’une harmonisation des protocoles pre-analytiques (volume plasma, méthode d extraction, contrôles internes) et de la calibration des plateformes, comme le souligne le travail de Klimova et coll. (2026) ',
      { cite: [89] },
      ' sur la robustesse analytique du PhasED-Seq face aux principales sources de variabilite.'
    ]),
    H2('4.3. Du génotype au pronostic : LymphGen sur plasma'),
    para([
      'Au-dela de la simple quantification, le ctDNA permet la determination du génotype tumoral. La concordance entre classification LymphGen réalisée sur ctDNA et sur biopsie tissulaire depasse 95 % dans les études récentes ',
      { cite: [3, 36, 68] },
      ', ce qui valide l’utilisation du plasma comme source primaire d’information moléculaire. Les mutations récurrentes détectées au baseline (TP53, B2M, KMT2D, MYD88, CARD11) ont chacune leur signification pronostique propre. Zhang et coll. (2021) ',
      { cite: [29] },
      ' rapportent ainsi que la mutation TP53 ou B2M pre-traitement chez 38 patients DLBCL haut risque est associee à un pronostic significativement plus defavorable, observation confirmee dans plusieurs cohortes chinoises de plus grande taille ',
      { cite: [36] },
      '.'
    ], { first: true }),
    para([
      'Cette capacité a intégrer simultanement quantité et qualité moléculaire fait du ctDNA un biomarqueur particulièrement riche, dont la valeur pronostique combinee surpasse celle de chaque dimension prise isolement. L’application directe au contexte CAR-T (section 6) demande toutefois quelques nuances : les patients arrivant en deuxième ou troisième ligne ont des paysages mutationnels remodeles par les chimiothérapies anterieures, et certaines mutations (comme TP53) acquierent une signification pronostique encore plus marquee dans ces situations réfractaires.'
    ])
  ];
}

// ============ SECTION 5 ============
function buildSection5() {
  return [
    H1('5. Dynamique précoce du ctDNA et réponse moléculaire'),
    H2('5.1. Les seuils EMR et MMR : une convention devenue standard'),
    para([
      'L’observation fondatrice de l’interet pronostique de la cinétique ctDNA précoce remonte aux travaux de Kurtz, Scherer et coll. (2018) ',
      { cite: [5] },
      ', qui ont analyse les dynamiques de 217 patients DLBCL traités dans six centres internationaux. Sur la base d’une cohorte de decouverte, deux seuils ont été définis et valides dans deux cohortes independantes : la ',
      { b: 'réponse moléculaire précoce (EMR)' },
      ', définie par une diminution d au moins 2 log10 du ctDNA après un cycle de chimiothérapie ; et la ',
      { b: 'réponse moléculaire majeure (MMR)' },
      ', définie par une diminution d au moins 2.5 log10 après deux cycles. Les patients atteignant l’EMR avaient une EFS à 24 mois de 83 % contre 50 % chez les non-EMR (p = 0.0015) ; le seuil MMR offrait une discrimination encore plus marquee (82 % vs 46 % ; p < 0.001).'
    ], { first: true }),
    para([
      'L’originalite de ce travail tient au fait que ces deux seuils restent prédictifs après ajustement multivarié sur l’IPI ',
      { b: 'et' },
      ' la réponse PET interim, deux marqueurs eux-mêmes solidement etablis. Cette independance suggere que la cinétique moléculaire précoce capture une dimension de la réponse tumorale qui n’est ni le burden initial, ni la réponse métabolique imagee. Les replications dans d’autres cohortes ',
      { cite: [11, 36, 38, 62, 65] },
      ' ont robustement valide ces seuils, faisant aujourd’hui des concepts EMR/MMR un standard implicite dans la littérature DLBCL.'
    ]),
    H2('5.2. Combinaison ctDNA et PET interim : une stratification a trois niveaux'),
    para([
      'L’étude d Alcoceba et coll. (2024, n = 68 patients DLBCL R-CHOP) ',
      { cite: [62] },
      ' a directement compare et combine la MMR ctDNA (mesuree par EuroClonality-NDC) et la réduction du SUVmax au PET interim après deux cycles. Chaque marqueur, pris isolement, discrimine significativement le risque de progression : la MMR seule classifie les patients en deux groupes avec une PFS a deux ans de 76 % contre 0 % (p < 0.001) ; la réduction du SUVmax supérieure à 66 % donné une PFS a deux ans de 83 % contre 38 % (p < 0.001). La combinaison des deux marqueurs identifié trois strates de pronostic très distinct (PFS 2 ans de 84 %, 17 % et 0 % selon le nombre de critères atteints ; p < 0.001).'
    ], { first: true }),
    para([
      'Ces resultats suggerent que ctDNA et PET ne sont pas substituables mais complémentaires : ils capturent des dimensions partiellement orthogonales de la réponse tumorale, et leur intégration amélioré la stratification au-dela de ce que chaque marqueur permet seul. Cette logique de complémentarité ouvre la voie aux approches dites de ',
      { b: 'multimodal monitoring' },
      ' qui constituent l’avenir probable de la stratification post-traitement.'
    ]),
    H2('5.3. CIRI : vers une prédiction dynamique individualisée'),
    para([
      'Le concept ultime de la stratification dynamique a été formalise par Kurtz, Esfahani et coll. dans leur publication phare de Cell (2019) ',
      { cite: [11] },
      ' : le ',
      { b: 'Continuous Individualized Risk Index (CIRI)' },
      ' intègre l’ensemble des informations disponibles à chaque temps clinique (IPI baseline, ctDNA initial, EMR/MMR, réponse PET interim) pour produire, pour chaque patient, une probabilite évolutive de PFS recalculee dynamiquement. L’analogie avec les modèles de "win probability" en sport est explicite : la prédiction n’est pas figee au baseline mais s ajuste au cours du suivi.'
    ], { first: true }),
    para([
      'Le CIRI apporte une amélioration de prédiction substantielle par rapport aux modèles statiques bases sur le seul IPI. Son inconvénient principal est sa nature combinatoire discrete : il opere par seuils successifs plutot que par modélisation continue d’une trajectoire moléculaire. C est précisément ce point qui justifie le choix méthodologique d ALYCANTE en faveur d’une approche par modèles a classes latentes joints (JLCM, section 8) : plutot que de combiner des seuils discrets, le JLCM modélise la forme entiere de la trajectoire ctDNA et l’associe directement au risque d’événement, capturant ainsi des configurations cinétiques qui echapperaient à des classifications binaires successives.'
    ])
  ];
}

// ============ SECTION 6 ============
function buildSection6() {
  return [
    H1('6. Le ctDNA dans le contexte CAR-T : un biomarqueur essentiel'),
    H2('6.1. Charge tumorale moléculaire pre-CAR-T : pronostic et toxicite'),
    para([
      'L’un des constats les plus solides émergés de la littérature post-CAR-T est que la charge tumorale pre-infusion - qu’elle soit mesuree par TMTV, par ctDNA ou par des indices combines - conditionne à la fois l’efficacité et la toxicite du traitement. Frank, Hossain et coll. (2021), dans la première étude prospective multicentrique dediee à ce sujet (n = 72) ',
      { cite: [25] },
      ', ont montre que les patients avec un ctDNA baseline élevé avaient un risque accru de progression après axi-cel, mais aussi un risque accru de développer un syndrome de relargage cytokinique (CRS) ou une neurotoxicite immunologique (ICANS) sévères. Cette double association à un sens biologique simple : une plus grande quantité de cellules tumorales présente plus d antigene cible, ce qui amplifie à la fois l’efficacité et la réponse inflammatoire associee.'
    ], { first: true }),
    para([
      'L’analyse exploratoire de ZUMA-7 publiee par Locke et coll. (2024) ',
      { cite: [59] },
      ' confirme ces observations sur une base plus large : un TMTV baseline élevé est associe à un EFS inférieur (notamment dans le bras standard) et à un risque accru de CRS et d ICANS de grade 3 ou plus. L’equipe chinoise de Zhou (2023, n = 48 patients R/R DLBCL) ',
      { cite: [53] },
      ' rapporté un effet dose particulièrement marque pour le nombre de mutations détectables sur ctDNA pre-traitement : au-dela de dix mutations, l’OS à un an chute à 0 % contre 73.8 % chez les patients avec dix mutations ou moins. Ces resultats convergent vers une conclusion clinique importante : la "debulking therapy" ou thérapie de pont avant CAR-T pourrait bénéficier préférentiellement aux patients identifiés comme a haut risque sur des critères moléculaires baseline.'
    ]),
    H2('6.2. La cinétique ctDNA précoce post-infusion : un signal puissant'),
    para([
      'L’étude pivot de Frank et coll. (2021) ',
      { cite: [25] },
      ' a etabli des references pronostiques cruciales pour le suivi post-CAR-T. Les chiffres rapportés sont particulièrement frappants : 70 % des patients en réponse durable à un an avaient un ctDNA indetectable des le septième jour post-infusion (J7), contre seulement 13 % des patients qui ont finalement progresse (p < 0.0001). Au temps J28, soit un mois après l’infusion, la dichotomie devient encore plus saillante : la PFS médiane n’est pas atteinte chez les patients ctDNA-negatifs contre seulement trois mois chez les patients ctDNA-positifs (p < 0.0001), et l’OS a deux ans est respectivement non atteinte contre dix-neuf mois (p = 0.0080).'
    ], { first: true }),
    para([
      'L’observation la plus marquante concerne les patients dont l’imagerie PET a J28 donné un message discordant - réponse partielle ou maladie stable - et chez lesquels le ctDNA permet la decision pronostique. Dans ce sous-groupe, seulement un patient sur dix (10 %) avec un ctDNA simultanement indetectable a finalement rechute, contre quinze patients sur dix-sept (88 %) avec un ctDNA détectable (p = 0.0001). Autrement dit, ',
      { b: 'le ctDNA précoce reclasse correctement les patients dont le PET genere de l’incertitude' },
      ', situation clinique fréquente liee à l’inflammation post-CAR-T résiduelle non spécifique. Pour compléter cette démonstration, le ctDNA détecté la rechute moléculaire avant la rechute radiologique dans 94 % des cas (29 patients sur 30), avec un decalage temporel median de plusieurs semaines a plusieurs mois.'
    ]),
    H2('6.3. Confirmation en deuxième ligne : l’étude TRANSFORM'),
    para([
      'Ces observations issues de la population traitee en troisième ligne ou au-dela ont été confirmees en deuxième ligne par l’analyse correlative ctDNA de TRANSFORM (Stepan, Ansari et coll., 2026, n = 136) ',
      { cite: [90] },
      '. Aux trois temps predefinis (J43, J64 et J126 post-randomisation), la clairance ctDNA-MRD predisait significativement l’EFS dans les deux bras (liso-cel et ASCT). Le bras liso-cel obtenait plus fréquemment un statut MRD-negatif que le bras ASCT, et la MRD-negativite était correlee à une EFS et une PFS prolongees ainsi qu à une plus grande duree de réponse parmi les répondeurs complets. Surtout, l’analyse multivariée montre que la MRD reste associee à l’EFS après ajustement pour la réponse PET, et une interaction significative est détectée entre le statut PET et le bras de traitement, suggerant que la valeur prédictive du PET diffère selon que le patient ait recu un CAR-T ou une ASCT.'
    ], { first: true }),
    para([
      'Cette dernière observation est importante pour la pratique clinique : elle suggere que les seuils et les significations attribues à la réponse PET ne sont pas necessairement transposables d’un contexte thérapeutique à l’autre, et qu’une évaluation moléculaire concomitante pourrait offrir une grille de lecture plus stable. Cette idée est en parfait accord avec la philosophie d ALYCANTE.'
    ]),
    H2('6.4. Implications pour la prise en charge post-CAR-T'),
    para([
      'L’ensemble de ces données converge vers un parcours clinique structure ou le ctDNA serait intègre a plusieurs etapes successives. Au baseline, il permettrait de stratifier conjointement le risque toxicite et efficacité, et d orienter la thérapie de pont chez les patients identifiés comme a haut burden moléculaire. Tres précocement après l’infusion (entre J7 et J28), il permettrait d’identifier les patients dont la réponse moléculaire est sous-optimale et d envisager des escalades thérapeutiques précoces, sans attendre la confirmation imagerie tardive. Enfin, régulièrement après la réponse PET, le ctDNA permettrait la détection précoce des rechutes moléculaires avant leur manifestation clinique ou radiologique. La principale barriere à cette intégration reste, en 2026, l’acces aux plateformes ultra-sensibles - PhasED-Seq notamment - encore confinees a quelques centres specialises en Europe. C est précisément cette question méthodologique que le projet ALYCANTE-biomarqueurs aborde, en démontrant la faisabilite d’un suivi pertinent même avec des plateformes moins ultra-sensibles, grace à une exploitation statistique optimale (modèles a classes latentes) des données longitudinales disponibles.'
    ], { first: true })
  ];
}

// ============ SECTION 7 ============
function buildSection7() {
  return [
    H1('7. ctDNA versus imagerie métabolique PET : complementarites et concurrences'),
    H2('7.1. La classification de Lugano : la reference contemporaine'),
    para([
      'Les critères de Lugano, formalises par Cheson et coll. en 2014 ',
      { cite: [1] },
      ', constituent la reference internationale pour le staging et l’évaluation de la réponse des lymphomes FDG-avides, incluant le DLBCL. Ils intègrent l’échelle visuelle de Deauville en cinq points : DS 1 et 2 correspondent à une absence d hypermetabolisme supérieur au pool sanguin mediastinal, DS 3 à un hypermetabolisme supérieur au pool mediastinal mais inférieur au foie, DS 4 et 5 à un hypermetabolisme supérieur au foie. La réponse métabolique complète (CMR) est définie par un score DS inférieur ou egal à 3. Une étude de comparaison directe avec les critères PERCIST réalisée par Nielsen et coll. (2023) ',
      { cite: [49] },
      ' a montre une concordance de 98.4 % entre les deux approches au temps interim et de 86 % en fin de traitement, suggerant que le choix entre Lugano et PERCIST a peu d impact pratique.'
    ], { first: true }),
    H2('7.2. Les limites du PET interim : un message pronostique discordant'),
    para([
      'Malgre son statut de reference, le PET interim après deux cycles (iPET2) présente des limites pronostiques bien documentees. Wight et coll. (2021), dans une cohorte de 200 patients DLBCL traités par R-CHOP ',
      { cite: [32] },
      ', montrent que seul le DS 5 (chez 19.5 % des patients) prédit fortement l’échec thérapeutique (HR 6.29 ; IC95 3.01-13.17), tandis que le DS 4 - fréquemment rapporté comme positif - est en réalité equivalent en pronostic aux DS 1-3. Cette dichotomie inattendue limite la valeur clinique pratique du seuil de positivite PET interim, et a conduit a explorer des alternatives plus discriminantes comme l’iFLT-PET (imagerie de la proliferation à la 18F-fluorothymidine) qui s’avère supérieur à l’iFDG-PET dans la prédiction de PFS dans la même cohorte (Minamimoto 2021, ',
      { cite: [22] },
      ').'
    ], { first: true }),
    para([
      'Dans le contexte post-CAR-T, les limites du PET sont encore plus marquees. L’inflammation résiduelle post-infusion peut persister plusieurs semaines, generant des hypermetabolismes non spécifiques qui rendent l’interprétation à un mois (M1) particulièrement delicate. Kitajima et coll. (2024) ',
      { cite: [60] },
      ' ont confirme la valeur de la CMR a M1 comme prédicteur de PFS et OS après CAR-T, mais au prix d’une dispersion non negligeable des réponses : sur 53 patients évaluables, 32 étaient en CMR a M1 et 21 en non-CMR, avec des trajectoires ulterieures contrastees.'
    ]),
    H2('7.3. Le ctDNA-MRD en fin de traitement : une supériorité pronostique démontrée'),
    para([
      'L’étude la plus aboutie démontrant la supériorité pronostique du ctDNA sur le PET en fin de traitement est l’analyse poolée de Roschewski, Kurtz, Westin et coll. (J Clin Oncol 2025) ',
      { cite: [75] },
      '. En agregeant les données de cinq études prospectives portant sur 137 patients LBCL traités en frontline par chimiothérapie a base d anthracyclines, suivis par 409 prélèvements plasmatiques par PhasED-Seq, les auteurs comparent directement la valeur prédictive de la MRD ctDNA en fin de traitement (EoT) avec celle du PET aux mêmes timepoints. Les resultats sont saisissants : la PFS a deux ans est de 29 % chez les patients ctDNA-détectable EoT contre 97 % chez les patients ctDNA-indetectable (HR 28.7 ; p < 0.0001), tandis que le PET positif à un HR de seulement 3.6. Quatre-vingt-quatorze pour cent des patients ctDNA-negatifs en fin de traitement restent en remission durable.'
    ], { first: true }),
    para([
      'Cet ecart d’ordre de grandeur entre les HR (28.7 contre 3.6) ne disqualifie pas le PET, qui conserve sa valeur de marqueur anatomique permettant de localiser la maladie résiduelle et de guider d eventuelles biopsies ciblees. Il suggere neanmoins fortement que la définition même de la remission devrait intégrer le ctDNA-MRD pour les patients éligibles : la spécificité tumorale du marqueur moléculaire - variants somatiques présents exclusivement dans les cellules tumorales - elimine le bruit inflammatoire qui parasite l’interprétation du PET. La Figure 4 rassemble ces resultats avec ceux d’autres études récentes confrontant ctDNA et PET dans des contextes thérapeutiques varies, et toutes convergent vers la même conclusion : le ctDNA discrimine systématiquement mieux que le PET, avec un effet particulièrement marque dans le contexte post-CAR-T (HR 14.0 pour le ctDNA J28 dans l’étude de Frank, contre 4.5 pour le PET dans la même cohorte).'
    ]),
    H2('7.4. Vers une redefinition de la remission ?'),
    para([
      'Cette supériorité analytique du ctDNA-MRD à des implications regulatoires majeures. Le ',
      { i: 'roadmap' },
      ' de Goldstein, Wang, Chamuleau et Alizadeh (2026) ',
      { cite: [91] },
      ' propose deux nouveaux critères de jugement pour les essais cliniques dans le lymphome : la ',
      { b: 'PFS modifiée' },
      ' (mPFS), incluant la MRD-positivite à la fin du traitement comme equivalent d’événement, et le ',
      { b: 'taux d uMRD' },
      ' à un timepoint predefini comme mesure de la profondeur de réponse. Ces critères permettraient d accelerer le développement clinique de nouveaux traitements en raccourcissant les durees d’essais et en augmentant leur sensibilité à la détection d efficacité. Leur adoption suppose toutefois une harmonisation méthodologique encore inaboutie.'
    ], { first: true })
  ];
}

// ============ SECTION 8 ============
function buildSection8() {
  return [
    H1('8. Methodes statistiques : modèles a classes latentes joints (JLCM/LCMM)'),
    H2('8.1. Pourquoi sortir des modèles de Cox classiques ?'),
    para([
      'L’analyse de biomarqueurs longitudinaux en oncologie pose plusieurs defis statistiques qui depassent le cadre des modèles de survie de Cox a covariables fixes. L’heterogeneite inter-individuelle des trajectoires est rarement bien capturee par une seule courbe moyenne ; la dépendance entre l’évolution du biomarqueur et la survenue de l’événement clinique - un patient en progression genere mecaniquement une trajectoire ctDNA croissante avant deces ou rechute - viole l’hypothèse d independance des observations longitudinales ; les mesures repetees sont souvent non equilibrees, certains patients ayant plus de timepoints que d’autres ; et l’interet clinique se porte souvent sur l’identification de sous-phénotypes plutot que sur des effets de population moyens.'
    ], { first: true }),
    para([
      'Les modèles a classes latentes mixtes (',
      { i: 'Latent Class Mixed Models' },
      ', LCMM) répondent spécifiquement à ces defis en postulant l’existence de plusieurs sous-populations non observees, chacune caractérisée par sa propre trajectoire moyenne (effets fixes spécifiques de classe) et sa propre variabilite individuelle (effets aleatoires). Combines avec un sous-modèle de survie spécifique de classe et un modèle multinomial d appartenance, ils forment les ',
      { i: 'Joint Latent Class Mixed Models' },
      ' (JLCM), qui permettent une modélisation simultanee et coherente des deux dimensions temporelles ',
      { cite: [55, 57, 78] },
      '.'
    ]),
    H2('8.2. Architecture du JLCM'),
    para([
      'Un JLCM comporte trois composantes interdependantes. Le ',
      { b: 'sous-modèle longitudinal' },
      ' est un modèle lineaire mixte qui decrit l’évolution du biomarqueur conditionnellement à l’appartenance à une classe latente, autorisant des pentes individuelles autour de la pente moyenne de classe (effets aleatoires sur l’intercept et la pente, structure typiquement notee ',
      { i: 'random = ~time' },
      ' dans le package R ',
      { i: 'lcmm' },
      '). Le ',
      { b: 'sous-modèle de survie' },
      ' est un modèle de Cox proportionnel spécifique de chaque classe, qui modélise la fonction de risque d’événement conditionnellement à la classe. Le ',
      { b: 'modèle d appartenance aux classes' },
      ' est une regression multinomiale qui peut intégrer des covariables baseline (age, IPI, stade) pour prédire la probabilite d appartenance à chaque classe.'
    ], { first: true }),
    para([
      'L’estimation des paramètres se fait par maximum de vraisemblance via un algorithme de Newton-Raphson modifié, robuste aux optima locaux. Le choix du nombre de classes (paramètre ng) repose sur des critères bayesiens (BIC) combines avec des considerations de pertinence clinique. Le tutoriel méthodologique récent de Kyheng, Babykina et Duhamel (2025) ',
      { cite: [78] },
      ' fournit un guide pratique d’implémentation pour cliniciens et statisticiens appliques, base sur des jeux de données reels. Le travail de Proust-Lima, Saulnier et coll. (2023) ',
      { cite: [55] },
      ' etend ce cadre aux marqueurs longitudinaux multivariés (',
      { i: 'mpjlcmm' },
      '), permettant la modélisation simultanee de plusieurs biomarqueurs sur un même axe temporel.'
    ]),
    H2('8.3. Applications oncologiques publiees'),
    para([
      'Plusieurs travaux ont démontré la valeur ajoutee des approches a classes latentes en oncologie clinique. En cancer colorectal, Li et coll. (2021) ont analyse les trajectoires peri-operatoires de trois marqueurs (CEA, CA19-9, CA125) chez 3539 patients ',
      { cite: [28] },
      '. Le modèle a classes latentes generalise (LCGMM) identifié trois trajectoires distinctes pour chaque marqueur (low-stable, early-rising, later-rising), et la combinaison des appartenances aux classes donné six groupes pronostiques avec des hazard ratios de mortalite allant de 1.59 à 12.40, captant une heterogeneite pronostique invisible aux seuils baseline statiques. Une approche similaire appliquee à l’alpha-fetoprotein dans le carcinome hepatocellulaire post-chimioembolisation (Lu et coll. 2022, n = 881) ',
      { cite: [82] },
      ' identifié trois classes (high-rising, low-stable, sharp-falling) avec un hazard ratio ajuste de mortalite de 5.13 pour la classe rising par rapport à stable.'
    ], { first: true }),
    para([
      'L’equipe bordelaise de Proust-Lima, qui a développé le package ',
      { i: 'lcmm' },
      ', a applique ces méthodes à des problèmes neuro-oncologiques complexes (atrophie multi-systèmes, n = 598 ',
      { cite: [55] },
      ') identifiant cinq sous-phénotypes distincts par leur trajectoire et leur risque de deces. Sur le versant exposition-maladie, Leveque et coll. (2020) ',
      { cite: [16] },
      ' ont utilise le LCMM pour stratifier les trajectoires d exposition au tabac et à l’amiante chez 4636 sujets de l’étude cas-témoins ICARE, identifiant des classes de risque differenciees pour le cancer du poumon. Cette diversite d’applications - du suivi clinique au screening etiologique - illustre la robustesse et la flexibilite du cadre.'
    ]),
    H2('8.4. Choix entre Joint Model classique et JLCM'),
    para([
      'Le ',
      { b: 'joint model (JM)' },
      ' classique, formalise par Rizopoulos et coll. ',
      { cite: [79, 83, 84] },
      ', modélise la trajectoire individuelle (effets aleatoires) comme covariable temps-dépendante dans le modèle de survie, produisant une prédiction continue individualisée. Le ',
      { b: 'JLCM' },
      ' postule au contraire l’existence de classes latentes discretes et fournit une probabilite d appartenance par patient. Les deux approches sont complémentaires : le JM optimise la prédiction individuelle (logique de "win probability"), tandis que le JLCM optimise l’identification de sous-phénotypes cliniquement utilisables (logique de stratification a deux ou trois bras).'
    ], { first: true }),
    para([
      'L’étude comparative de Brombin, Di Serio et Rancoita (2014) ',
      { cite: [83] },
      ' sur la cohorte HIV-CASCADE (n = 648, lymphocytes CD4 longitudinaux) a directement compare ces deux approches sur le même jeu de données : les deux donnent des inferences valides, mais avec des objectifs différents - le JM excelle pour la prédiction de mortalite individuelle, le JLCM pour la description des sous-phénotypes évolutifs et l’identification des facteurs associes à leur appartenance.'
    ]),
    H2('8.5. Choix méthodologiques dans ALYCANTE'),
    para([
      'Le projet ALYCANTE-biomarqueurs a privilegie le JLCM plutot que le JM classique pour deux raisons. Premierement, l’objectif clinique est l’identification de sous-classes pronostiques actionnables - des groupes "BON" et "MAUVAIS" pronostic stratifiables des le J14 post-infusion - plutot qu’une prédiction individuelle continue dont l’interprétation reste plus complexe en consultation. Deuxiemement, la taille d échantillon limitée (n = 57) favorise des modèles parsimonieux : deux classes latentes avec une structure aleatoire ',
      { i: 'random = ~time' },
      ' (intercept et pente individuels au sein de chaque classe) offrent un compromis raisonnable entre flexibilite et risque de surapprentissage.'
    ], { first: true }),
    para([
      'Le choix du seed 123 dans l’algorithme d optimisation merite une mention spécifique. Sur cette cohorte de 57 patients, certains seeds (456, 2024, 3141, 5000, etc.) conduisent l’estimation à la frontiere de l’espace des paramètres - typiquement une variance d’effet aleatoire convergeant vers zero ou une correlation atteignant ±1 - ce qui fait echouer la fonction ',
      { i: 'predictClass()' },
      ' avec une erreur de matrice non définie positive. Le seed 123 (et plusieurs autres : 42, 789, 1000) donné le même BIC et la même classification que les seeds problematiques, mais avec une matrice de variance-covariance correctement estimee à l’interieur de l’espace des paramètres. Cette observation, documentee dans la memoire méthodologique du projet, illustre les limites pratiques d’application des modèles complexes sur des effectifs modestes, et plaide pour une validation externe sur cohorte plus large.'
    ]),
    para([
      'Le modèle final identifié deux classes : une classe BON (cl1, n = 32, taux de R/R à 12 mois de 6 %) et une classe MAUVAIS (cl2, n = 25, taux de R/R à 12 mois de 96 %). Tronque a J14 - c’est-a-dire en utilisant uniquement les mesures de leucaphérèse, J-5, J0 et J14 pour prédire la classe d appartenance - le modèle atteint Se = Sp = PPV = NPV = 100 % pour la prédiction de R/R à 12 mois chez les 40 patients avec un followup adequat. Cette performance, qu’il faudra confirmer par validation externe (notamment sur la cohorte CART de Lea, n = 158, présentée en annexe), constitue le resultat saillant du projet ALYCANTE-biomarqueurs.'
    ])
  ];
}

// ============ SECTION 11 ============
function buildSection11() {
  return [
    H1('11. Anticorps bispécifiques CD20xCD3 dans le DLBCL réfractaire'),
    H2('11.1. Une alternative thérapeutique en plein essor'),
    para([
      'Apres l’essor des CAR-T, les anticorps bispécifiques CD20xCD3 (BsAbs) représentent la deuxième grande revolution immunotherapeutique du DLBCL R/R, avec plusieurs avantages logistiques majeurs sur les thérapies cellulaires : disponibilite immediate, absence de necessite de leucaphérèse et de lymphodepletion, administration ambulatoire possible, cout moindre. Trois molecules ont obtenu une AMM après au moins deux lignes de traitement : glofitamab (Roche/Columvi, IV), epcoritamab (AbbVie/Genmab, sous-cutané) et mosunetuzumab (Roche/Lunsumio, indication limitée au lymphome folliculaire). Odronextamab a recu une approbation europeenne plus récente ',
      { cite: [95] },
      ', et plusieurs autres BsAbs sont en développement. La revue systématique de Bayly-McCredie et coll. (2024, 19 études, 1332 patients) ',
      { cite: [98] },
      ' synthetise l’ensemble des données disponibles a fin 2024.'
    ], { first: true }),
    H2('11.2. Glofitamab : un format 2:1 ameliorant l’engagement T'),
    para([
      'Le glofitamab présente une particularite structurelle : son format 2:1 (deux Fab anti-CD20 pour un Fab anti-CD3) augmente l’affinite pour la cellule cible et favorise la formation du "synapse immunologique" entre lymphocyte T et cellule tumorale. L’étude pivotale phase 2 de Dickinson, Carlo-Stella et coll. publiee dans le NEJM (2022, n = 154 patients DLBCL R/R après au moins deux lignes) ',
      { cite: [94] },
      ' a rapporté un taux de réponse complète de 39 % (IC95 32-48 %) avec un schema d administration de duree fixe (12 cycles), après prétraitement par obinutuzumab destine a moderer la liberation cytokinique. Le delai median d obtention de la réponse complète était de 42 jours, et 78 % des réponses complètes étaient maintenues a douze mois. La PFS a douze mois était de 37 % pour l’ensemble de la cohorte. Le syndrome de relargage cytokinique survenait chez 63 % des patients mais restait majoritairement de bas grade (CRS de grade supérieur ou egal à 3 chez seulement 4 %), confirmant la securite acceptable du regime.'
    ], { first: true }),
    H3('Glofitamab après échec de CAR-T : l’étude LYSA'),
    para([
      'L’application la plus pertinente pour la trajectoire des patients ALYCANTE est l’étude phase 2 monobras de la LYSA conduite par Cartron, Houot, Al Tabaa et coll. (2025, Nat Cancer) ',
      { cite: [97] },
      '. Cette étude a enrôlé 46 patients DLBCL R/R après échec de CAR-T, une population au pronostic historiquement dramatique avec une survie globale médiane inférieure a six mois. Grace à un schema d escalade rapide atteignant la dose pleine en une semaine, la survie globale médiane atteint 14.7 mois (IC95 8.8 - non atteinte), validant le critère principal. Le taux de réponse métabolique objectivée est de 76.1 % et le taux de réponse métabolique complète de 45.7 %. La PFS médiane plus courte (3.8 mois) suggere que les réponses ne sont pas toujours durables dans cette population fortement prétraitée, mais l’absence de CRS et d ICANS de grade supérieur ou egal à 3 valide la securite du protocole accelere et ouvre la voie à son utilisation en pratique courante.'
    ], { first: true }),
    H2('11.3. Epcoritamab et mosunetuzumab : profils et indications'),
    para([
      'L’epcoritamab, administre par voie sous-cutanée, présente un profil pharmacocinetique stable et permet une utilisation ambulatoire. Les données du programme EPCORE NHL ',
      { cite: [102] },
      ' ont valide la dose recommandee de 48 mg, et l’étude EPCORE NHL-3 conduite chez 36 patients japonais (Izutsu et coll. 2023) ',
      { cite: [100] },
      ' a confirme un taux de réponse globale de 56 % et de réponse complète de 44 %, avec un profil de tolerance comparable aux essais internationaux (CRS chez 83 %, principalement de grade 1-2). Le mosunetuzumab, qui dispose d’une AMM principalement pour le lymphome folliculaire R/R (Budde et coll. 2022 ',
      { cite: [101] },
      '), reste en développement dans le DLBCL, principalement en combinaison. Son profil de tolerance dans une série de 218 patients NHL (Matasar et coll. 2023) ',
      { cite: [103] },
      ' est favorable, avec un CRS chez 39 % seulement et un ICANS chez 1 %.'
    ], { first: true }),
    H2('11.4. Donnees real-world : tolerance et limites'),
    para([
      'L’analyse multicentrique americaine de Brooks, Zabor et coll. (2025) ',
      { cite: [96] },
      ', portant sur 245 patients DLBCL R/R traités par epcoritamab (n = 156) ou glofitamab (n = 89) en pratique reelle, apporte un éclairage essentiel sur la translation clinique. Pres de 60 % des patients auraient été inéligibles aux essais pivots en raison de comorbidites ou de traitements anterieurs ; 60 % avaient déjà recu un CAR-T. Le taux de réponse global était comparable a celui des essais (51 % pour epcoritamab, 53 % pour glofitamab), mais la PFS médiane était beaucoup plus courte en pratique reelle : seulement 2.6 mois (IC95 2.0-3.8) et l’OS médiane de 7.8 mois. Cette discordance suggere que la population reelle est plus fragile que celle des essais et que les réponses obtenues ne sont pas systématiquement durables.'
    ], { first: true }),
    para([
      'Une observation biologique particulièrement preoccupante émerge de cette étude real-world : sur les dix-sept patients ayant bénéficie d’une biopsie pairee avant et après traitement par BsAb, quinze (88 %) avaient perdu l’expression de CD20 à la rechute, avec un delai median de progression de 3.7 mois. Cette perte d antigene cible constitue un mecanisme de resistance majeur, analogue à la perte de CD19 observee après CAR-T, et à des conséquences directes sur la sequence thérapeutique : si un patient recoit un BsAb avant un CAR-T anti-CD19, la perte de CD20 ne compromet pas le CAR-T ulterieur ; mais à l’inverse, un patient traite d’abord par CAR-T anti-CD19 puis perdant CD20 après BsAb sera depourvu de cibles antigeniques validees.'
    ]),
    H2('11.5. Sequencement thérapeutique : CAR-T puis bispécifique'),
    para([
      'L’ensemble des données disponibles plaide pour la sequence CAR-T puis BsAb en cas d échec, plutot que l’inverse. Trois arguments convergent en faveur de cette strategie. D abord, le bénéfice de survie démontré par le glofitamab après échec de CAR-T (LYSA, OS médiane 14.7 mois) ',
      { cite: [97] },
      ' n’a pas son equivalent dans la situation reciproque. Ensuite, la perte d antigene CD19 post-CAR-T n affecte pas la cible CD20 utilisee par les BsAbs, ce qui préservé l’efficacité de la sequence. Enfin, la perte de CD20 post-BsAb compromettrait l’efficacité ulterieure d’un CAR-T anti-CD19, fermant cette option de sauvetage si le BsAb a été utilise en premier. Cette logique de préservation des cibles antigeniques s’applique directement aux patients d ALYCANTE : ceux qui rechuteront seront prioritairement orientes vers un BsAb, vraisemblablement le glofitamab compte tenu des données LYSA. Le suivi par ctDNA prend ici toute sa place : il pourrait permettre la détection précoce de la rechute moléculaire post-CAR-T, autorisant l’initiation du bispécifique avant la reprise clinique de la maladie.'
    ], { first: true })
  ];
}

// ============ SECTION 12 ============
function buildSection12() {
  return [
    H1('12. Complications immunologiques post-CAR-T : CRS, ICANS et ICAHT'),
    H2('12.1. Le syndrome de relargage cytokinique (CRS) : un standard cliniquement maîtrise'),
    para([
      'Le syndrome de relargage cytokinique reste la complication la plus fréquente après CAR-T anti-CD19, mais son management a considérablement progresse au cours de la dernière decennie. L’analyse de registre CIBMTR de Shouval et coll. (2025), portant sur 1916 patients LBCL traités en pratique reelle aux Etats-Unis entre 2018 et 2020 ',
      { cite: [107] },
      ', donné les chiffres de reference contemporains : 75.2 % des patients développent un CRS de tout grade, mais seulement 11.3 % présentent un CRS de grade 3 ou plus. La proportion de CRS sévères a diminue significativement au fil des annees - de 14.0 % en 2018 à 9.2 % en 2020 (p < 0.01) - traduisant l’amélioration de la prise en charge (utilisation précoce du tocilizumab, identification des facteurs prédicteurs, anticipation thermique).'
    ], { first: true }),
    para([
      'Le risque de CRS de grade 3 ou plus diffère significativement selon le produit CAR-T : l’axi-cel y est associe à un odds ratio de 4.6 par rapport au tisa-cel (p < 0.01), ce qui doit être pris en compte dans la decision thérapeutique chez les patients fragiles. La physiopathologie - liberation massive d IL-6, IFN-gamma, TNF-alpha par les cellules T activees - et la prise en charge - tocilizumab (anti-IL6R), corticosteroides, support symptomatique selon les critères ASTCT/Lee - sont aujourd’hui bien codifiees ',
      { cite: [106] },
      '. Les recommandations conjointes EBMT/JACIE/EHA (Hayden et coll. 2022) constituent la reference pratique en Europe.'
    ]),
    H2('12.2. La neurotoxicite ICANS : un signal moins resolu'),
    para([
      'Le syndrome de neurotoxicite associe aux cellules effectrices immunologiques (ICANS) regroupe des manifestations diverses : encephalopathie, aphasie, convulsions, myoclonies, dans les cas les plus sévères œdeme cérébral. Les données du registre CIBMTR rapportent un ICANS de tout grade chez 43.5 % des patients, et de grade 3 ou plus chez 21 % de la population totale (soit 47.7 % des cas d ICANS) ',
      { cite: [107] },
      '. Contrairement au CRS, la proportion d ICANS sévères n’a pas significativement diminue entre 2018 et 2020 (41.5 % à 53.7 % parmi les ICANS, p = 0.10), suggerant que les outils thérapeutiques disponibles - principalement les corticosteroides - restent limites.'
    ], { first: true }),
    para([
      'Une observation cliniquement importante émerge de cette analyse : 57.1 % des CRS s’accompagnent d’un ICANS, et 97.5 % des ICANS surviennent chez des patients qui ont aussi présente un CRS. Cette colocalisation suggere un continuum physiopathologique entre les deux syndromes, possiblement relie à la production cytokinique systémique. Les valeurs d ALYCANTE - CRS de grade supérieur ou egal à 3 chez 8.1 %, neurotoxicite de grade supérieur ou egal à 3 chez 14.5 % ',
      { cite: [45] },
      ' - se situent dans la fourchette des essais pivots malgré une population non éligible à l’ASCT, ce qui valide la securite du traitement dans cette population fragile.'
    ]),
    H2('12.3. ICAHT : la cytopenie prolongee, complication récemment formalisee'),
    para([
      'L’ICAHT (',
      { i: 'Immune effector Cell-Associated HematoToxicity' },
      ') a été formellement reconnu comme entite distincte en 2023 par les societes EHA-EBMT ',
      { cite: [104, 105] },
      '. Il se definit par une cytopenie prolongee post-CAR-T - typiquement une neutropenie de grade 3 ou plus persistant plus de quatorze jours après l’infusion ou suivant un profil bi/triphasique. Sa physiopathologie est multifactorielle : toxicite directe de la lymphodepletion, suppression medullaire par cytokines inflammatoires, infiltration tumorale résiduelle, infections secondaires.'
    ], { first: true }),
    para([
      'L’outil prédictif le plus utilise est le score ',
      { b: 'CAR-HEMATOTOX (CAR-HT)' },
      ' développé par Rejeski et coll., reposant sur cinq paramètres pre-CAR-T : numeration des polynucleaires neutrophiles, des plaquettes, de l’hemoglobine, et taux de CRP et de ferritine. Le score a été prospectivement valide dans le LBCL et le MCL. La validation comparative chinoise de Zhang et coll. (2025, n = 119) ',
      { cite: [105] },
      ' confirme sa performance : 67 % des patients classes a haut risque présentent une neutropenie prolongee médiane de 17.7 jours contre seulement 5.3 jours dans le groupe a bas risque (p < 0.001). Pour les leucemies aigues B (B-ALL), Nair et coll. (2025) ',
      { cite: [104] },
      ' ont développé une variante ALL-Hematotox dans laquelle la ferritine est remplacee par la charge medullaire au diagnostic, atteignant une AUC de 0.84 pour la prédiction de neutropenie sévère prolongee.'
    ]),
    H2('12.4. Mortalite non liee à la maladie et toxicites d’organes'),
    para([
      'L’étude de registre EBMT de Penack, Peczynski et coll. (2023) ',
      { cite: [108] },
      ', portant sur 492 patients LBCL post-axi-cel ou tisa-cel, fournit une évaluation globale de la securite a moyen terme. La mortalite non liee à la maladie (NRM) est de 3.1 % a trois mois et 5.2 % à un an, principalement liee aux toxicites des thérapies cellulaires (6.4 % des deces) et aux infections (4.4 %). Les toxicites d’organes sévères (grade 3 ou plus) sont relativement rares : renale dans 3 % des cas, cardiaque dans 2.3 %, gastro-intestinale dans 2.3 %, hepatique dans 1.8 %. Toutes surviennent majoritairement dans les trois premières semaines post-infusion. La cause de deces la plus fréquente reste de loin la progression tumorale (85.1 % des deces), ce qui rappelle que l’enjeu principal demeure l’efficacité antitumorale plus que la maîtrise de la toxicite chez les patients atteints d’un DLBCL R/R.'
    ], { first: true }),
    H2('12.5. ctDNA et prédiction des toxicites : une piste prometteuse'),
    para([
      'L’association entre charge moléculaire baseline et risque de toxicite, déjà evoquee en section 6, ouvre une piste de stratification preventive. Les patients identifiés comme a haut risque sur la base du ctDNA pre-CAR-T pourraient bénéficier d’une surveillance renforcee (monitoring biologique rapproche, accessibilite au tocilizumab) et d’une optimisation de la thérapie de pont visant a réduire la masse tumorale. Le développement de scores intégratifs combinant ctDNA, CAR-HT, IMPI et caractéristiques cliniques reste un objectif de recherche prioritaire, qu’aucune étude prospective n’a encore valide à notre connaissance. La cohorte ALYCANTE-biomarqueurs, par son design et son suivi précoce, pourrait y contribuer.'
    ], { first: true })
  ];
}

// ============ SECTION 13 ============
function buildSection13() {
  return [
    H1('13. Synthese quantitative : méta-analysés des hazard ratios ctDNA'),
    H2('13.1. La méta-analyse pionnière de Yao (2021)'),
    para([
      'La première synthese quantitative de la valeur pronostique du ctDNA dans les lymphomes a été proposee par Yao, Xu et coll. en 2021 (Clin Exp Med) ',
      { cite: [23] },
      ', sur la base de huit études publiees totalisant 767 patients. Les resultats sont coherents avec la littérature individuelle : un ctDNA élevé est associe à un hazard ratio pondere de 2.24 (IC95 1.63-3.08, p < 0.00001) pour la PFS dans les lymphomes pris globalement. Restreint aux DLBCL (sous-groupe de 379 patients sur trois études), le HR est de 2.01 (IC95 1.42-2.85, p < 0.0001), avec une heterogeneite modeste. Pour l’EFS, le HR pondere est de 4.53 (1.79-11.47) dans deux études totalisant 192 patients ; pour l’OS dans le DLBCL, il s élevé à 3.09 (1.50-6.35). Cette méta-analyse, bien que limitée par l’hétérogénéité des méthodes ctDNA et des seuils utilises dans les études individuelles, etablit la robustesse globale de l’effet.'
    ], { first: true }),
    H2('13.2. La méta-analyse bayesienne IPD de 2026 (lymphome de Hodgkin)'),
    para([
      'Une approche méthodologique plus aboutie a été développée par Shahsavand, Forghani et coll. (Crit Rev Oncol Hematol 2026, in press) ',
      { cite: [110] },
      ' pour le lymphome de Hodgkin, sur la base de dix études totalisant 1158 patients. Cette méta-analyse bayesienne avec données individuelles patients (IPD) reconstruites à partir des courbes de Kaplan-Meier digitalisees apporte plusieurs raffinements importants : analyse temporelle de l’effet pronostique, calcul des temps de survie restreints (RMST) avec leurs intervalles de credibilite, et stratification par timepoint de mesure.'
    ], { first: true }),
    para([
      'Les resultats objectivent un effet pronostique dose-dépendant croissant au fil du traitement. Un ctDNA baseline élevé est associe à un HR PFS de 2.74 (IC95 1.30-5.75) et à une perte de RMST a cinq ans de 7.7 mois. La positivite ctDNA au temps interim multiplie l’effet par presque trois (HR 5.99 ; perte RMST 22.7 mois). En fin de traitement, l’association atteint une amplitude rarement rencontree : HR PFS de 13.4 (IC95 3.97-41.87), perte RMST de 39.2 mois - autrement dit, la quasi-totalite du bénéfice de survie predictible. Pour l’OS, les HR sont respectivement de 2.49 et 4.74 pour baseline et fin de traitement. Cette gradation temporelle - la valeur pronostique du marqueur augmente avec le temps de mesure - est une observation profondément convergente avec les données DLBCL detaillees en section 7.'
    ]),
    H2('13.3. Le forest plot de synthese (Figure 1)'),
    para([
      'La Figure 1 propose une synthese visuelle des hazard ratios ctDNA dans les lymphomes B agressifs, sur la base de 18 estimations issues de 13 études représentatives publiees entre 2015 et 2026. Cinq categories sont distinguees par code couleur : ctDNA baseline (bleu), réponse moléculaire C1-C2 (orange), fin de traitement (vert pour ctDNA, rouge pour la reference PET), post-CAR-T (violet) et méta-analysés (gris). Plusieurs observations se degagent de cette représentation.'
    ], { first: true }),
    para([
      'Premierement, on observe un gradient temporel net : les HR baseline (1.5 à 3.8) sont moderes, ceux mesures après un ou deux cycles atteignent 3 à 8, ceux mesures en fin de traitement explosent jusqu’à 28.7. Cette observation confirme la convergence avec la méta-analyse Hodgkin et suggere un principe biologique général : plus la mesure ctDNA est proche de la fin du traitement, plus elle intègre les determinants pronostiques de l’ensemble du parcours thérapeutique. Deuxiemement, la comparaison directe entre ctDNA et PET en fin de traitement - rendue possible par l’étude de Roschewski (2025) qui rapporté les deux mesures chez les mêmes patients - montre une supériorité ecrasante du ctDNA (HR 28.7 contre 3.6) ',
      { cite: [75] },
      '. Troisiemement, dans le contexte post-CAR-T, l’effet pronostique est conserve et même amplifie : le HR du ctDNA J28 atteint 14.0 dans l’étude pivotale de Frank (2021) ',
      { cite: [25] },
      '.'
    ]),
    H2('13.4. Limites et perspectives'),
    para([
      'Plusieurs limites tempèrent l’interprétation de ces resultats. L’heterogeneite méthodologique entre études - méthodes ctDNA, définitions de positivite, seuils, timing précis - est considérable et fait que la comparabilite directe des HR n’est pas toujours pertinente. Le biais de publication est probable, les études negatives etant moins susceptibles de paraître. Les données individuelles patient (IPD) ne sont disponibles que pour une minorite d’études, limitant la possibilite de méta-analysés statistiquement plus puissantes. Enfin, la PhasED-Seq, plateforme la plus sensible, reste limitée a quelques études (Roschewski 2025, Stepan 2026, Klimova 2025) et son adoption europeenne est encore très restreinte.'
    ], { first: true }),
    para([
      'Malgre ces réservés, le constat global est clair et coherent : le ctDNA constitue un marqueur pronostique extrêmement robuste dans les lymphomes B agressifs, dont l’ordre d’effet depasse largement celui de la plupart des marqueurs cliniques et d imagerie traditionnels. Sa transition de l’outil de recherche vers la pratique clinique routiniere - question exploree dans le ',
      { i: 'roadmap' },
      ' de Goldstein et coll. ',
      { cite: [91] },
      ' - est un objectif désormais a court terme.'
    ])
  ];
}

// ============ FIGURES + TABLES (regrouped) ============
function buildFiguresAndTables() {
  return [
    H1('Figures de synthese et tableau comparatif des méthodes'),
    para([
      'Les figures ci-après synthetisent visuellement les principaux enseignements des sections précédentes. La Figure 1 propose une vue d ensemble du paysage pronostique du ctDNA dans les lymphomes B agressifs. La Figure 2 retrace la chronologie des avancées pivotales depuis 2015. La Figure 3 compare la sensibilité analytique des différentes méthodes de détection. La Figure 4 confronte directement le ctDNA-MRD à la réponse PET en fin de traitement ou après CAR-T. Le Tableau 1, en fin de section, detaille les onze méthodes principales de détection.'
    ], { first: true }),
    H2('Figure 1 - Forest plot des HR ctDNA'),
    ...figureBlock('fig1_forest_plot_HR_ctDNA.png',
      'Figure 1. Forest plot des hazard ratios ctDNA dans les lymphomes B agressifs (18 estimations issues de 13 études publiees entre 2015 et 2026). Cinq categories distingues par code couleur : ctDNA baseline (bleu), réponse moléculaire C1-C2 (orange), fin de traitement (vert ctDNA, rouge PET pour reference), post-CAR-T (violet), méta-analysés (gris). La taille du marqueur est proportionnelle au logarithme de l’effectif. La reference HR = 1 (absence d’effet) est materialisee par la ligne rouge pointillee.', 560),
    H2('Figure 2 - Timeline des études pivot'),
    ...figureBlock('fig2_timeline_etudes.png',
      'Figure 2. Timeline 2014-2026 des études pivots dans le DLBCL post-CAR-T et le suivi par ctDNA. Code couleur : méthodes ctDNA (orange), pronostic clinique (bleu), essais CAR-T (violet), bispécifiques (rouge). Les études francaises (ALYCANTE, LYSA glofitamab) sont indiquees.', 620),
    H2('Figure 3 - Sensibilite analytique des méthodes'),
    ...figureBlock('fig3_methodes_sensibilite.png',
      'Figure 3. Comparaison de la limite de détection des méthodes ctDNA et de l’imagerie. Echelle logarithmique inversee de la fraction tumorale détectable. La PhasED-Seq atteint 7 x 10⁻⁷ (sub-ppm) contre environ 10⁻¹ pour le PET. Les paliers MRD classique (10⁻⁴) et ultra-sensible (10⁻⁶) sont materialises.', 620),
    H2('Figure 4 - ctDNA-MRD versus PET-CMR'),
    ...figureBlock('fig4_ctDNA_vs_PET.png',
      'Figure 4. Comparaison directe des hazard ratios ctDNA-MRD et PET-CMR mesures aux mêmes timepoints (fin de traitement ou post-CAR-T) dans six études représentatives. Echelle logarithmique. Dans toutes les études, le ctDNA discrimine plus fortement que le PET, l’effet etant particulièrement marque dans le contexte post-CAR-T (Roschewski 2025, Frank 2021).', 560),
    new Paragraph({ children: [new PageBreak()] }),
    H2('Tableau 1 - Comparatif des méthodes de détection ctDNA'),
    para([T('Synthese des onze méthodes principales selon leur sensibilité analytique, leur necessite de biopsie tissulaire, leurs avantages et leurs limites cliniques, avec les études représentatives correspondantes.')], { first: true }),
    buildMethodsTable()
  ];
}

// ============ SECTION 14 (landscape) ============
function buildSection14() {
  return [
    new Paragraph({ children: [new PageBreak()] }),
    H1('14. Comparatif des trois produits CAR-T anti-CD19 dans le DLBCL'),
    para([
      'Le paysage thérapeutique du DLBCL R/R repose désormais sur trois produits CAR-T anti-CD19 cliniquement disponibles : axicabtagène ciloleucel (axi-cel, Yescarta), tisagenlecleucel (tisa-cel, Kymriah) et lisocabtagène maraleucel (liso-cel, Breyanzi). Bien que tous trois ciblent le même antigene CD19 et reposent sur un même principe immunotherapeutique, ils differencient sur des aspects structurels et cliniques qui conditionnent les indications, l’efficacité et le profil de tolerance.'
    ], { first: true }),
    H2('14.1. Differences structurelles et pharmacologiques'),
    para([
      'La première différence fondamentale porte sur le domaine de costimulation intracellulaire. L’axi-cel utilise un domaine CD28, associe à une activation plus rapide et plus puissante des lymphocytes T mais aussi à une demi-vie plus courte ; tisa-cel et liso-cel emploient un domaine 4-1BB, associe à une persistance plus longue des cellules effectrices mais une cinétique d activation plus progressive. Cette différence structurelle explique en partie le profil de toxicite distinct : l’axi-cel induit plus fréquemment des CRS et ICANS sévères, comme le confirment les données CIBMTR (OR 4.6 pour CRS de grade ≥ 3 par rapport au tisa-cel) ',
      { cite: [107] },
      '. La deuxième différence notable concerne la manufacture : le liso-cel est seul a separer les fractions CD4 et CD8 et à les reinfuser dans un ratio 1:1 contrôle, ce qui contribuerait à son profil de tolerance favorable (Filosto et coll. 2024, ZUMA-7) ',
      { cite: [56] },
      '.'
    ], { first: true }),
    H2('14.2. Essais pivots et indications AMM'),
    para([
      'L’axi-cel et le tisa-cel ont d’abord obtenu leur AMM en troisième ligne et au-dela sur la base des études ZUMA-1 (axi-cel) et JULIET (tisa-cel, Schuster et coll. NEJM 2019) ',
      { cite: [113] },
      ', et le liso-cel sur l’étude TRANSCEND NHL 001 (Salles et coll. 2021) ',
      { cite: [19, 31] },
      '. Cette etape a marque une transformation majeure du pronostic dans une population historiquement considérée comme palliative (SCHOLAR-1).'
    ], { first: true }),
    para([
      'L’extension à la deuxième ligne s est faite differemment pour les trois produits. L’axi-cel a obtenu son AMM en 2L après ZUMA-7 (FDA 2022) ',
      { cite: [44] },
      ', étude randomisee 1:1 dans laquelle l’axi-cel a montre une supériorité sur la chimiothérapie standard suivie d ASCT (EFS median 8.3 vs 2.0 mois, HR 0.40 ; OS 4 ans 54.6 % vs 46 %, HR 0.73) ',
      { cite: [18, 43] },
      '. Le liso-cel a egalement obtenu son AMM en 2L grace à l’essai TRANSFORM, dont l’analyse correlative ctDNA (Stepan 2026) ',
      { cite: [90] },
      ' montre une supériorité supplementaire sur le critère moléculaire (MRD plus profonde et plus durable). Le tisa-cel n’a pas d AMM en 2L, faute d’essai randomise concluant. L’étude ALYCANTE (Houot et coll. 2023) ',
      { cite: [45] },
      ' s’inscrit dans le sillage de ZUMA-7 mais cible une population non couverte par cet essai : les patients non éligibles à l’ASCT en raison de l’age ou de comorbidites.'
    ]),
    H2('14.3. Profils de tolerance compares'),
    para([
      'Sur le plan de la tolerance, le liso-cel se distingue par le profil le plus favorable. Les taux de CRS de grade ≥ 3 sont de 2 % pour liso-cel, 11-13 % pour axi-cel, et 22 % pour tisa-cel ; les taux d ICANS de grade ≥ 3 sont de 10 %, 21-32 % et 12 % respectivement. Cette différence de tolerance à des conséquences pratiques importantes : le liso-cel peut être administre en ambulatoire dans certains centres, ce qui n’est pas envisageable pour l’axi-cel. Pour les patients ages ou fragiles, ces considerations peuvent peser autant que l’efficacité pure dans le choix du produit, comme le suggere la discussion accompagnant l’étude ALYCANTE.'
    ], { first: true }),
    H2('14.4. Tableau de synthese (Tableau 2)'),
    para([
      'Le Tableau 2 ci-après rassemble les caractéristiques principales des trois produits, des aspects structurels aux données d efficacité et de tolerance. Les chiffres reportes pour ALYCANTE (axi-cel uniquement) et pour la cohorte multicentrique de Lea (N = 158, distribution Yescarta 66 %, Breyanzi 18 %, Kymriah 15 %) permettent de situer les populations etudiees dans le contexte général.'
    ], { first: true }),
    buildCARTcomparisonTable(),
    para([T('Sources : ZUMA-1 (refs en bibliographie), ZUMA-7 [18,43,44], JULIET [113], TRANSCEND [31,19], TRANSFORM [90], ALYCANTE [45,86], Brooks 2025 [96], Cartron 2025 [97].')], { first: true }),
    new Paragraph({ children: [new PageBreak()] }),
    H2('14.5. Implications pour ALYCANTE et son interprétation'),
    para([
      'L’étude ALYCANTE etant restreinte à l’axi-cel, les resultats biomarqueurs s’appliquent directement à la population ZUMA-7 (axi-cel 2L) et plus généralement aux patients traités par axi-cel toutes lignes confondues. Leur généralisation aux autres produits CAR-T (tisa-cel, liso-cel) suppose une validation spécifique, dans la mesure ou les dynamiques cinétiques cellulaires et les profils de toxicite différent. La cohorte multicentrique de Lea (N = 158), discutee en annexe, offre un materiau de validation precieux : elle inclut les trois produits dans des proportions reflechissant la pratique reelle francaise. La comparaison de survie entre ALYCANTE et Lea, qui montre des courbes PFS et OS quasi superposables (log-rank p = 0.95 et 0.62 respectivement), valide la représentativité externe de la cohorte ALYCANTE et autorisé une extrapolation prudente des conclusions ctDNA à la population CAR-T plus large.'
    ], { first: true }),
    para([
      'Une perspective interessante consisterait a stratifier l’analyse ctDNA par produit CAR-T dans la cohorte de Lea, ce qui permettrait de tester si les seuils et trajectoires identifiés dans ALYCANTE (entierement axi-cel) restent pertinents pour les patients traités par tisa-cel ou liso-cel. Cette analyse, en cours, completera l’interprétation des resultats principaux.'
    ])
  ];
}

// ============ SECTION 15 (PCNSL) ============
function buildSection15() {
  return [
    H1('15. Le lymphome primaire du SNC : un terrain particulier'),
    H2('15.1. Une variante du DLBCL au pronostic intermediaire'),
    para([
      'Le lymphome primaire du système nerveux central (PCNSL) constitue une variante rare mais distincte du DLBCL, caractérisée par une localisation strictement encéphalique (parenchyme cérébral, leptomeninges, vitreoretine) sans atteinte systémique au diagnostic. Sa biologie partage de nombreux traits avec le DLBCL extra-cérébral mais s en distingue par une fréquence plus élevée de mutations MYD88 L265P, CD79B et CARD11 - configurations rappelant le sous-groupe MCD de la classification LymphGen. Le pronostic est intermediaire entre celui du DLBCL classique et celui des lymphomes systémiques avec atteinte SNC secondaire. Le traitement repose sur des regimes de chimiothérapie a haute dose de methotrexate, eventuellement suivis d ASCT pour les patients jeunes en bon etat général.'
    ], { first: true }),
    H2('15.2. Les limites de la biopsie tissulaire dans le PCNSL'),
    para([
      'La spécificité anatomique du PCNSL rend la biopsie tissulaire particulièrement problématique. Les lésions sont souvent profondes, multiples, voire déjà diffuses au diagnostic, ce qui complique l’acces chirurgical. Les biopsies stereotaxiques portent des risques neurologiques non negligeables et ne fournissent souvent qu’un materiel limite, peu adapte aux analysés moléculaires exhaustives. Dans ce contexte, la liquid biopsy - qu’il s agisse de plasma ou de liquide cephalorachidien - constitue une alternative particulièrement attractive ',
      { cite: [114, 115, 116, 120] },
      '. La revue spécifique de Šúri et Mocikova (2025) ',
      { cite: [116] },
      ' synthetise les approches CSF disponibles pour le diagnostic de l’atteinte leptomeningee du DLBCL.'
    ], { first: true }),
    H2('15.3. Le ctDNA plasmatique : sensibilité réduite par la barriere hemato-encéphalique'),
    para([
      'Contrairement au DLBCL systémique ou le ctDNA plasmatique est détectable chez plus de 95 % des patients au diagnostic, sa sensibilité dans le PCNSL est limitée par la barriere hemato-encéphalique qui restreint le passage des fragments d ADN tumoral vers la circulation périphérique. L’étude prospective de Yoon, Kim et coll. (2021, n = 42) ',
      { cite: [115] },
      ' a évalué le ctDNA plasmatique chez des patients PCNSL diagnostiques entre 2017 et 2018. La détection de mutations somatiques representant le ctDNA n’a été possible que chez 27 % des patients (11 sur 41 évaluables), une proportion considérablement inférieure a celle observee dans le DLBCL systémique. Les mutations principalement détectées concernent PIM1 (36 % des cas positifs), KMT2D, PIK3CA et MYD88 (27 % chacun). La concordance entre les profils mutationnels plasmatiques et tissulaires est de 45 %, ce qui indique que certaines mutations importantes présentés dans le tissu n atteignent pas la circulation périphérique. Pour le suivi longitudinal, sur sept patients en réponse complète tracables, quatre ont vu leurs mutations ctDNA disparaitre et trois ont conserve des mutations détectables en fin de traitement ; cette observation suggere une valeur potentielle pour la MRD, mais reste limitée par le faible taux de détection initial.'
    ], { first: true }),
    H2('15.4. Le ctDNA dans le LCS : sensibilité optimale pour le PCNSL'),
    para([
      'Le passage des fragments tumoraux vers le LCS etant facilite par la proximite anatomique, le ctDNA du LCS est plus concentre et permet une meilleure détection. Plusieurs strategies se sont développées autour de ce compartiment ',
      { cite: [114, 116] },
      '. La détection de la mutation MYD88 L265P par ddPCR sur LCS constitue aujourd’hui l’approche la plus etablie pour le diagnostic du PCNSL : la mutation est présente chez environ 75 % des PCNSL avec composante ABC et offre une sensibilité/spécificité très élevée dans le LCS. Sa combinaison avec le dosage d interleukine 10 (IL-10) sur le même prélèvement amélioré encore les performances diagnostiques (Šúri 2025). Pour le suivi MRD post-traitement, des panels NGS plus etendus sur LCS sont en développement.'
    ], { first: true }),
    H2('15.5. Lymphomes vitreoretiniens : le cas particulier des fluides oculaires'),
    para([
      'Une variante particulièrement complexe est le lymphome vitreoretinien (VRL), sous-type du PCNSL touchant principalement le vitre et la retine. L’étude pilote de Wang, Su et coll. (Haematologica 2022, n = 15) ',
      { cite: [117] },
      ' a évalué l’analyse de ctDNA dans l’humeur aqueuse (HA) et le fluide vitreen (FV) chez ces patients. Les profils moléculaires des prélèvements HA et FV pries au baseline sont hautement concordants (>90 %), tandis que la concordance avec le LCS est plus faible avec des fréquences alleliques nettement inférieures. Cette observation suggere que le compartiment oculaire est anatomiquement separable du compartiment cérébral, et que chaque type de prélèvement reflète préférentiellement le siege primaire de la maladie. Pour le suivi du traitement, les changements de fréquences alleliques en HA correlent avec les niveaux d IL-10, marqueur de réponse oculaire bien etabli.'
    ], { first: true }),
    para([
      'L’étude apporte egalement une comparaison genetique interessante entre PCNSL et VRL : les mutations MYD88 sont plus fréquentes dans le PCNSL, tandis que les pertes en CDKN2A/B sont plus fréquentes dans le VRL. Cette différence biologique se traduit par une différence de réponse thérapeutique à l’ibrutinib : taux de réponse objectivée de 65 % pour le PCNSL contre seulement 14 % pour le VRL, ce qui appelle à une individualisation des strategies selon le compartiment anatomique.'
    ]),
    H2('15.6. CAR-T dans le PCNSL : prudence initiale, données rassurantes'),
    para([
      'Les essais pivots des CAR-T (ZUMA-1, JULIET, TRANSCEND) excluaient explicitement les patients avec atteinte SNC active, par crainte de neurotoxicite immunologique sévère. Cette prudence réglementaire a longtemps prive les patients atteints de PCNSL ou de SCNSL d acces à une thérapie potentiellement curative. La méta-analyse de Cook, Dorris et coll. (Blood Adv 2023) ',
      { cite: [119] },
      ' constitue la synthese la plus aboutie des données disponibles : 128 patients (30 PCNSL, 98 SCNSL) traités par CAR-T anti-CD19 en dehors des essais formels, dans des séries single-center ou des registres. Les resultats sont rassurants : le CRS de grade 3 ou plus survient chez 13 % des PCNSL et 11 % des SCNSL, soit des taux comparables a ceux des patients DLBCL extra-cérébraux ; l’ICANS de grade 3 ou plus survient chez 18 % des PCNSL et 26 % des SCNSL, taux egalement comparables. Les taux de réponse complète sont de 56 % pour le PCNSL et 47 % pour le SCNSL, avec 37 % de remission a six mois dans les deux groupes.'
    ], { first: true }),
    para([
      'Cette démonstration empirique a conduit à une évolution progressive des critères d eligibilite dans les essais cliniques récents et à une plus large inclusion des patients atteints de PCNSL/SCNSL dans les programmes CAR-T. La revue de Miyao, Yokota et Sakemura (2023) ',
      { cite: [120] },
      ' discute les pistes d optimisation : administration intrathecale de CAR-T, ingenierie de cellules lymphotropes, combinaison avec des inhibiteurs de la BHE. Aucune de ces strategies n’est encore validee en pratique courante mais elles ouvrent un champ de recherche actif.'
    ]),
    H2('15.7. Implications pour ALYCANTE et perspectives'),
    para([
      'L’étude ALYCANTE excluait initialement les patients avec atteinte SNC active, conformement aux pratiques en vigueur pour les essais CAR-T DLBCL. Les enseignements méthodologiques d ALYCANTE - en particulier l’interet du suivi longitudinal ctDNA et l’application des modèles a classes latentes joints - pourraient cependant être transferables au PCNSL, sous réserve de plusieurs adaptations méthodologiques. Premierement, le suivi devrait porter sur le LCS plutot que sur le plasma, compte tenu de la sensibilité limitée du plasma dans cette pathologie. Deuxiemement, le panel moléculaire devrait privilegier les mutations spécifiques du PCNSL (MYD88 L265P, CD79B). Troisiemement, le calendrier des prélèvements devrait intégrer la réalité clinique du suivi neurologique, généralement moins fréquente que celle des prélèvements plasmatiques. Une étude prospective dediee, en collaboration avec les equipes de neuro-oncologie, pourrait constituer une extension naturelle des resultats ALYCANTE.'
    ], { first: true })
  ];
}

// ============ SECTION 16 IMPLICATIONS ============
function buildSection16() {
  return [
    H1('16. Implications pour ALYCANTE et perspectives'),
    H2('16.1. Le positionnement scientifique de l’étude'),
    para([
      'A la lumière de la littérature internationale développée dans les sections précédentes, l’étude ALYCANTE-biomarqueurs s’inscrit dans une triple lignée. Premierement, elle prolonge et etend les travaux pionniers de Frank et coll. (2021) sur le suivi ctDNA post-CAR-T ',
      { cite: [25] },
      ', en l’appliquant à une population non couverte par les essais americains et europeens précédents : les patients non éligibles à l’autogreffe traités en deuxième ligne. Deuxiemement, elle constitue, à notre connaissance, la première application publiee des modèles a classes latentes joints au suivi du ctDNA dans le DLBCL post-CAR-T, transposant ainsi une approche statistique développée initialement dans d’autres contextes (cancer colorectal, hepatocarcinome, neurodegenerescences) ',
      { cite: [28, 55, 78, 82] },
      '. Troisiemement, elle apporte une comparaison directe entre marqueur moléculaire précoce (delta ctDNA J14) et marqueur d imagerie tardif (CMR PET M3, critère principal de l’essai clinique), avec une démonstration de supériorité pronostique du premier sur le second.'
    ], { first: true }),
    H2('16.2. Les resultats principaux replaces dans la littérature'),
    para([
      'Le resultat le plus marquant du projet biomarqueur est la performance prédictive du modèle JLCM tronque au temps J14 : sensibilité, spécificité, valeurs prédictives positive et negative atteignent toutes 100 % pour la prédiction de la rechute/réfractarité à 12 mois (n = 40 patients avec followup adequat). Cette performance, sans equivalent direct dans la littérature, doit être interprétée avec prudence : elle pourrait refléter en partie un surapprentissage lie à la taille d échantillon limitée, et necessite imperativement une validation externe sur cohorte independante. Elle est neanmoins coherente avec les données post-CAR-T disponibles, notamment l’étude de Frank (2021) ou la valeur prédictive positive du ctDNA J28 atteint déjà environ 80 % chez les patients dont le PET genere de l’incertitude ',
      { cite: [25] },
      '.'
    ], { first: true }),
    para([
      'L’indice de reclassement net (NRI) du JLCM J14 par rapport à la CMR M3 est de + 59 % pour la prédiction de R/R 12, une amélioration substantielle qui, si elle est confirmee, justifie pleinement l’interet d’une intégration précoce du marqueur moléculaire dans la stratification post-CAR-T. Le couple prédictif explore en analysés secondaires - delta_ctDNA_ratio x lymphocytes leucapheresis x duree de mesure M6 - atteint un C-index de 0.752 pour l’EFS, valeur très respectable dans le contexte des modèles pronostiques en oncologie. L’ensemble de ces resultats est en accord conceptuel avec les données TRANSFORM (Stepan et coll. 2026) ',
      { cite: [90] },
      ' qui montrent une supériorité de la MRD ctDNA sur le PET dans le bras CAR-T, et avec la méta-analyse Hodgkin (Shahsavand 2026) ',
      { cite: [110] },
      ' qui objectivée un gradient temporel d’effet pronostique du ctDNA.'
    ]),
    H2('16.3. La validation externe par comparaison avec la cohorte Lea'),
    para([
      'La comparaison de survie entre ALYCANTE (N = 57) et la cohorte CART de Lea (N = 158, multicentrique LYSARC) réalisée en complément apporte un premier argument de généralisabilité. Les médianes de PFS sont quasi identiques (17.6 mois pour ALYCANTE contre 19.1 mois pour Lea, log-rank p = 0.95) ; la survie globale n’est atteinte au point de médiane dans aucune des deux cohortes (log-rank p = 0.62) ; les estimations Kaplan-Meier de PFS à 24 mois sont de 45 % et 47 % respectivement, et de 70 % et 58 % pour l’OS à 24 mois. La superposition est encore plus marquee lorsqu on restreint la cohorte Lea à la sous-population "ALYCANTE-like" - Yescarta administre en deuxième ligne, n = 40 - avec p = 0.88 pour la PFS et p = 0.97 pour l’OS, soit des courbes quasiment confondues.'
    ], { first: true }),
    para([
      'Cette absence de différence significative entre les deux cohortes - issues de centres et de selections différentes - constitue un argument fort en faveur de la représentativité d ALYCANTE pour la pratique CAR-T francaise contemporaine, et autorisé une extrapolation prudente des conclusions ctDNA. Une validation prospective de la performance du JLCM sur les données ctDNA de la cohorte Lea, lorsqu elles seront disponibles, constituera l’etape de validation externe définitive.'
    ]),
    H2('16.4. Limites a discuter de manière transparente'),
    para([
      'Plusieurs limites doivent être clairement identifiées pour permettre une interprétation lucide des resultats. La taille d échantillon limitée (n = 57 patients) accroit le risque de surapprentissage du modèle JLCM, en particulier compte tenu de la complexite paramétrique du modèle (effets aleatoires sur l’intercept et la pente, plus paramètres de classe spécifique). La validation externe sur cohorte independante est donc une etape critique et imperative.'
    ], { first: true }),
    para([
      'La dépendance au seed dans l’algorithme d optimisation du JLCM, déjà discutee en section 8, est un autre signe de fragilité numérique sur petit échantillon. Bien que les seeds qui donnent une estimation valide convergent vers le même BIC et la même classification, ce phénomène plaide pour une approche prudente et systématique : vérification de la stabilite du modèle sur plusieurs seeds, analysés de sensibilité, et idealement validation par bootstrap. La cohorte de validation devrait permettre de tester si les mêmes seeds restent utilisables sur un effectif plus grand, ou si une re-estimation complète est préférable.'
    ]),
    para([
      'L’heterogeneite méthodologique du ctDNA dans la littérature limite la transposabilite directe des seuils ALYCANTE à d’autres centres. La plateforme PhasED-Seq, plus sensible que le CAPP-Seq employe dans ALYCANTE, pourrait redefinir comme positives certaines mesures actuellement classees comme negatives. Cette dimension méthodologique merite d être discutee dans la présentation des resultats : le modèle JLCM s adresse à une plateforme donnée et son utilisation avec une plateforme différente necessiterait une recalibration des seuils.'
    ]),
    para([
      'Enfin, la définition stricte du R/R (Progression ou Relapse uniquement, exclusion des censures avant 12 ou 24 mois) constitue un choix méthodologique conservateur mais critique. Il garantit que les performances rapportées sont valides pour les patients ayant un suivi suffisant, mais peut sous-estimer le taux d’événement reel dans la cohorte globale. La transparence sur cette définition est essentielle pour l’interprétation comparative avec d’autres études utilisant des définitions plus larges (EFS toute cause).'
    ]),
    H2('16.5. Perspectives ouvertes par les resultats'),
    para([
      'Plusieurs lignes de recherche se degagent naturellement des resultats ALYCANTE. La validation externe sur la cohorte Lea, pour laquelle les données ctDNA pourraient être extraites à partir de GLIMS aux temps J0 et J14, est la priorité méthodologique immediate. L’intégration des classifications LymphGen réalisables sur ctDNA (Moia et coll. 2025) ',
      { cite: [68] },
      ' permettrait une stratification combinee moléculaire et dynamique, potentiellement encore plus discriminante que chaque approche prise isolement. L’adoption des critères uMRD ou mPFS comme critères de jugement selon le ',
      { i: 'roadmap' },
      ' de Goldstein et coll. ',
      { cite: [91] },
      ' constituerait une translation pratique des resultats academiques vers les essais cliniques regulatoires.'
    ], { first: true }),
    para([
      'Une perspective particulièrement riche concerne l’articulation avec les anticorps bispécifiques. Pour les patients ALYCANTE en progression après CAR-T - une proportion non negligeable au vu des courbes de survie - le glofitamab représenté désormais la principale option thérapeutique (étude LYSA de Cartron 2025) ',
      { cite: [97] },
      '. Le suivi ctDNA pourrait jouer un rôle majeur a deux niveaux : la détection précoce de la rechute moléculaire post-CAR-T, permettant d initier le bispécifique avant l’explosion clinique de la maladie ; et le suivi de la perte d antigene CD20 post-bispécifique, mecanisme de resistance documente par Brooks et coll. (2025) ',
      { cite: [96] },
      ' dans 88 % des biopsies pairees, qui necessitera l’elaboration de panels multi-antigeniques (CD19, CD20, CD22).'
    ]),
    para([
      'D autres extensions méthodologiques sont envisageables : développement de scores intégratifs combinant ctDNA baseline, CAR-HEMATOTOX, IMPI et caractéristiques cliniques pour la prédiction conjointe de l’efficacité et de la toxicite ; application des approches JLCM aux données TMTV longitudinales en parallele du ctDNA, dans une logique d analyse multivariée de trajectoires ',
      { cite: [55] },
      ' ; et extension au PCNSL par adaptation du suivi au compartiment LCS, comme suggere en section 15.'
    ]),
    H2('16.6. Le message essentiel pour la reunion LYSARC 2026'),
    para([
      'L’étude ALYCANTE-biomarqueurs apporte trois contributions originales au paysage scientifique du DLBCL post-CAR-T. Premierement, elle constitue la première étude prospective dediee à la population des patients non éligibles à l’autogreffe en deuxième ligne, comblant une lacune importante des essais ZUMA-7 et TRANSFORM ',
      { cite: [45] },
      '. Deuxiemement, elle introduit dans ce contexte une méthodologie statistique novatrice - les modèles a classes latentes joints - dont l’application au suivi ctDNA dans le DLBCL est, à notre connaissance, inedite. Troisiemement, elle apporte un element empirique fort en faveur de la supériorité prédictive de la dynamique moléculaire précoce (delta ctDNA J14) sur l’imagerie métabolique tardive (CMR PET M3), justifiant le développement d outils de stratification ctDNA-bases en pratique clinique routiniere.'
    ], { first: true }),
    para([
      'La validation externe sur la cohorte CART de Lea (N = 158, log-rank PFS p = 0.95 et OS p = 0.62 contre ALYCANTE) renforce la représentativité externe des resultats et autorisé leur généralisation prudente. La transition entre l’outil de recherche et l’outil clinique routinier reste à accomplir, mais ALYCANTE fournit à la fois la preuve de concept méthodologique et le materiel pratique - protocole, scripts d analyse reproductibles, comparaison directe avec la reference imagerie - necessaires à cette transition. Le projet illustre ainsi une voie possible pour l’intégration des biomarqueurs moléculaires dans la prise en charge du DLBCL post-CAR-T, dans une perspective de medecine de précision adaptee à la population fragile.'
    ])
  ];
}

function buildBibliography() {
  const out = [H1('Bibliographie (120 references PubMed vérifiées)')];
  out.push(para([
    'L’ensemble des references suivantes a été identifié et vérifié par interrogations API PubMed (NCBI E-utilities). Chaque entree comporte le PMID et le DOI permettant l’acces direct aux articles. La numerotation est continue : les references 1 à 93 correspondent à la première phase de recherche thematique, 94 à 112 aux thematiques complémentaires (anticorps bispécifiques, complications immunologiques post-CAR-T, méta-analysés), et 113 à 120 aux sections specialisees (essai JULIET, comparaison detaillee des trois produits CAR-T, PCNSL et liquid biopsy du LCS).'
  ], { first: true }));
  allRefs.forEach(r => {
    out.push(new Paragraph({
      spacing: { before: 80, after: 80, line: 280 },
      indent: { left: 720, hanging: 720 },
      children: [
        new TextRun({ text: `[${r.id}] `, bold: true }),
        new TextRun({ text: r.authors + ' ' }),
        new TextRun({ text: r.title + ' ' }),
        new TextRun({ text: `${r.journal}. ${r.year}`, italics: true }),
        new TextRun({ text: r.vol ? ';' + r.vol + '.' : '.' }),
        new TextRun({ text: ` PMID: ${r.pmid}; DOI: ${r.doi}`, size: 18, color: '595959' })
      ]
    }));
  });
  return out;
}

// ============ ASSEMBLE ============
const portraitContent = [
  ...buildCover(),
  ...buildPreambule(),
  ...buildSection1(),
  ...buildSection2(),
  ...buildSection3(),
  ...buildSection4(),
  ...buildSection5(),
  ...buildSection6(),
  ...buildSection7(),
  ...buildSection8(),
  ...buildSection11(),
  ...buildSection12(),
  ...buildSection13(),
  ...buildFiguresAndTables()
];

const landscapeContent14 = buildSection14();
const portraitContent15plus = [
  ...buildSection15(),
  ...buildSection16(),
  new Paragraph({ children: [new PageBreak()] }),
  ...buildBibliography()
];

const commonHeader = new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: 'Revue ALYCANTE v6 - LYSARC 2026', size: 18, color: '7F7F7F' })] })] });
const commonFooter = new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
  new TextRun({ text: 'Page ', size: 18 }),
  new TextRun({ children: [PageNumber.CURRENT], size: 18 }),
  new TextRun({ text: ' / ', size: 18 }),
  new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 18 })
] })] });

// V6 : tout en portrait, une seule section continue
const portraitSectionAll = {
  properties: {
    page: {
      size: { width: 12240, height: 15840 },
      margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 }
    }
  },
  headers: { default: commonHeader },
  footers: { default: commonFooter },
  children: [...portraitContent, ...landscapeContent14, ...portraitContent15plus]
};

const doc = new Document({
  creator: 'Service Immunologie Biologique AP-HP - assistance Claude',
  title: 'Revue ALYCANTE v4 - LYSARC 2026',
  description: 'Revue analytique ctDNA DLBCL CAR-T bispécifiques PCNSL JLCM',
  styles: {
    default: { document: { run: { font: 'Calibri', size: 22 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 30, bold: true, font: 'Calibri', color: '2F5496' },
        paragraph: { spacing: { before: 480, after: 200 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 26, bold: true, font: 'Calibri', color: '2F5496' },
        paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 1 } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 23, bold: true, italics: true, font: 'Calibri', color: '404040' },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 2 } }
    ]
  },
  numbering: {
    config: [
      { reference: 'bullets', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }
    ]
  },
  sections: [portraitSectionAll]
});

Packer.toBuffer(doc).then(buf => {
  const outPath = process.argv[2] || 'revue_alycante_v4.docx';
  fs.writeFileSync(outPath, buf);
  console.log('Wrote:', outPath, 'size:', buf.length, 'bytes');
});
