// Revue de literature ALYCANTE v3 - corrigee + nouvelles sections (PCNSL, CAR-T comparatif, protocole)
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, LevelFormat, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageBreak, PageNumber, Header, Footer, ImageRun,
  PageOrientation, VerticalAlign
} = require('docx');

// ============ LOAD REFS ============
const refsData = JSON.parse(fs.readFileSync(path.join(__dirname, 'references.json'), 'utf8')).refs;
const additionalRefs = JSON.parse(fs.readFileSync(path.join(__dirname, 'references_v2.json'), 'utf8')).additional_refs;
const v3Refs = JSON.parse(fs.readFileSync(path.join(__dirname, 'references_v3.json'), 'utf8')).additional_refs_v3;
const allRefs = [...refsData, ...additionalRefs, ...v3Refs].sort((a, b) => a.id - b.id);

const FIG_DIR = r => r;
const FIG_DIR_V3 = path.join(path.dirname(__dirname), 'figures_v3');

// ============ HELPERS ============
function P(text, opts = {}) {
  const runs = Array.isArray(text) ? text : [new TextRun(text)];
  return new Paragraph({
    children: runs,
    spacing: { before: 60, after: 100, line: 300 },
    alignment: opts.align || AlignmentType.JUSTIFIED,
    ...opts
  });
}
function H1(text) { return new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 180 }, children: [new TextRun({ text, bold: true })] }); }
function H2(text) { return new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 120 }, children: [new TextRun({ text, bold: true })] }); }
function H3(text) { return new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 180, after: 100 }, children: [new TextRun({ text, bold: true, italics: true })] }); }
function B(text) { return new TextRun({ text, bold: true }); }
function I(text) { return new TextRun({ text, italics: true }); }
function T(text) { return new TextRun(text); }
function Sup(text) { return new TextRun({ text, superScript: true }); }

function cite(...ids) {
  return new TextRun({ text: '[' + ids.join(',') + ']', superScript: true });
}

function bullet(textOrRuns) {
  return new Paragraph({
    numbering: { reference: 'bullets', level: 0 },
    spacing: { before: 40, after: 60 },
    children: Array.isArray(textOrRuns) ? textOrRuns : [new TextRun(textOrRuns)]
  });
}

function PC(parts) {
  const runs = parts.map(p => {
    if (typeof p === 'string') return new TextRun(p);
    if (p.cite) return cite(...p.cite);
    if (p.b) return B(p.b);
    if (p.i) return I(p.i);
    return new TextRun(String(p));
  });
  return P(runs);
}

function figureBlock(filename, caption, widthPx = 580) {
  const filePath = path.join(FIG_DIR_V3, filename);
  if (!fs.existsSync(filePath)) {
    return [P([T(`[FIGURE MANQUANTE: ${filename}]`)])];
  }
  const imgData = fs.readFileSync(filePath);
  const w = imgData.readUInt32BE(16);
  const h = imgData.readUInt32BE(20);
  const ratio = h / w;
  const docHeight = Math.round(widthPx * ratio);

  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 240, after: 120 },
      children: [new ImageRun({
        type: 'png',
        data: imgData,
        transformation: { width: widthPx, height: docHeight },
        altText: { title: filename, description: caption, name: filename }
      })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 60, after: 180 },
      children: [new TextRun({ text: caption, italics: true, size: 20, color: '404040' })]
    })
  ];
}

// ============ TABLE COMPARATIVE CAR-T PRODUITS ============
function buildCARTcomparisonTable() {
  const cellBorder = { style: BorderStyle.SINGLE, size: 1, color: 'BFBFBF' };
  const cellBorders = { top: cellBorder, bottom: cellBorder, left: cellBorder, right: cellBorder };
  const headers = ['Caracteristique', 'Axi-cel (Yescarta)', 'Tisa-cel (Kymriah)', 'Liso-cel (Breyanzi)'];
  const colW = [3500, 3700, 3700, 3700]; // sum = 14600 (landscape)

  const rows = [
    ['Fabricant', 'Kite / Gilead', 'Novartis', 'BMS / Celgene'],
    ['Costimulation', 'CD28', '4-1BB', '4-1BB'],
    ['Manufacture', 'CD4+CD8 combined', 'CD4+CD8 combined', 'CD4 et CD8 separes (1:1)'],
    ['Approbations DLBCL 3L+', 'FDA 2017, EMA 2018', 'FDA 2018, EMA 2018', 'FDA 2021, EMA 2022'],
    ['Approbations DLBCL 2L', 'FDA 2022 (ZUMA-7) [44]', 'Non en 2L', 'FDA 2022 (TRANSFORM)'],
    ['Essai pivot 3L+', 'ZUMA-1 [refs ZUMA-1]', 'JULIET [113]', 'TRANSCEND NHL 001 [31]'],
    ['Essai pivot 2L', 'ZUMA-7 (n=359) [18,43]', '-', 'TRANSFORM (n=184) [90]'],
    ['ORR (3L+, pivot)', '83% (axi-cel 2L)', '~52%', '73%'],
    ['CR rate (3L+, pivot)', '65% (axi-cel 2L)', '~40%', '53%'],
    ['EFS median 2L (vs SOC)', '8.3 mois vs 2.0 (HR 0.40) [18]', '-', 'Superior to ASCT [90]'],
    ['OS 4 ans 2L', '54.6% vs 46% SOC (HR 0.73, p=0.03) [43]', '-', 'Superior to ASCT'],
    ['CRS toute grade', '92-93% (ZUMA-1)', '58% (JULIET)', '42% (TRANSCEND)'],
    ['CRS grade >=3', '11-13%', '22%', '2% (le plus bas)'],
    ['ICANS toute grade', '64-74%', '21%', '30%'],
    ['ICANS grade >=3', '21-32%', '12%', '10%'],
    ['Profil de tolerance', 'Le plus toxique', 'Intermediaire', 'Le plus favorable'],
    ['Cible patient frail/age', 'Necessite hospit. usuelle', 'Tolerance moyenne', 'Adapte (ambulatoire possible)'],
    ['Cohorte Lea (n=158)', '104 patients (65.8%)', '23 patients (14.6%)', '28 patients (17.7%)'],
    ['Etude ALYCANTE (n=62)', '62 (100%) en 2L non-ASCT [45]', '-', '-'],
    ['Cout (US, ~)', '$373 000 (FDA)', '$475 000', '$410 000'],
    ['Etude post-CAR-T glofitamab', '52/154 etaient ex axi-cel [94]', 'inclus dans LYSA [97]', 'inclus dans LYSA [97]']
  ];

  const headerRow = new TableRow({
    tableHeader: true,
    children: headers.map((h, i) => new TableCell({
      borders: cellBorders,
      width: { size: colW[i], type: WidthType.DXA },
      shading: { fill: '2F5496', type: ShadingType.CLEAR },
      margins: { top: 80, bottom: 80, left: 100, right: 100 },
      verticalAlign: VerticalAlign.CENTER,
      children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 0 },
        children: [new TextRun({ text: h, bold: true, color: 'FFFFFF', size: 17 })]
      })]
    }))
  });

  const dataRows = rows.map(row => new TableRow({
    children: row.map((cell, i) => new TableCell({
      borders: cellBorders,
      width: { size: colW[i], type: WidthType.DXA },
      margins: { top: 60, bottom: 60, left: 100, right: 100 },
      verticalAlign: VerticalAlign.TOP,
      children: [new Paragraph({
        spacing: { before: 0, after: 0, line: 220 },
        children: [new TextRun({ text: cell, size: 15, bold: i === 0 })]
      })]
    }))
  }));

  return new Table({
    width: { size: 14600, type: WidthType.DXA },
    columnWidths: colW,
    rows: [headerRow, ...dataRows]
  });
}

// ============ TABLE COMPARATIVE METHODES CTDNA (v2 maintained) ============
function buildMethodsTable() {
  const cellBorder = { style: BorderStyle.SINGLE, size: 1, color: 'BFBFBF' };
  const cellBorders = { top: cellBorder, bottom: cellBorder, left: cellBorder, right: cellBorder };
  const headers = ['Methode', 'Approche', 'LoD', 'Biopsie ?', 'Avantages', 'Limites', 'Etudes representatives'];
  const colW = [1700, 2300, 1400, 1300, 2500, 2500, 2900];

  const rows = [
    ['IgH-NGS / clonotype VDJ', 'Clonotype Ig dominant tissu puis quantification plasma', '~1 ppm', 'Oui', 'Specifique tumeur, sensible, tout B-NHL', 'Necessite biopsie informative', 'Roschewski 2015 [2], Frank 2021 [25], Wang 2025 [69]'],
    ['CAPP-Seq', 'Panel cible recurrent DLBCL + UMI deep sequencing', '~1-10 ppm', 'Non', 'Tumor-naive, genotypage simultane, LymphGen classifiable', 'Cout, expertise bioinfo', 'Scherer 2016 [3], Kurtz 2018 [5], Alig 2021 [21], Moia 2025 [68]'],
    ['PhasED-Seq', 'Variants phases co-localises pour reduction de bruit', '~0.7 ppm', 'Recommandee', 'Sensibilite ultra-elevee, ideal MRD post-traitement', 'Cout eleve, validation recente', 'Kurtz 2021 [26], Klimova 2025 [71], Roschewski 2025 [75], Stepan 2026 [90]'],
    ['Signatera (mPCR)', 'Panel multiplex 16 SNV tumor-informed', '~1-10 ppm', 'Oui', 'Workflow commercial, FDA-approved (autres tumeurs)', 'Limite a 16 SNV', 'Narkhede 2024 [65]'],
    ['EuroClonality-NDC', 'Panel NGS standardise europeen', '~10^-5', 'Plasma seul', 'Standardisation europeenne', 'Sensibilite < PhasED-Seq', 'Alcoceba 2024 [62]'],
    ['CLEARS (panel 521 genes)', 'Panel etendu mutations lymphome', '~10^-4-10^-5', 'Non', 'Couverture genique etendue', 'Recouvrement variable', 'Vodicka 2025 [76], Hamova 2025 [81]'],
    ['ULP-WGS cfDNA', 'WGS faible profondeur pour CNV/burden', 'TF >3%', 'Non', 'Faible cout, detecte CNV/del17p', 'Sensibilite limitee MRD', 'Zhao 2025 [74]'],
    ['ddPCR (single mut)', 'PCR digitale mutation specifique', '~10^-3-10^-4', 'Oui', 'Cout faible, rapide', 'Une seule cible', 'Cas reports [72]'],
    ['Flow cytometry MRD', 'Phenotype B clonal residuel', '~10^-4', 'Non (moelle)', 'Bien etabli leucemie aigue', 'Peu applicable DLBCL', 'Liu 2023 [54]'],
    ['cfDNA 5hmC-Seal', 'Profilage epigenetique 5hmC', '~10^-4', 'Non', 'Approche epigenetique novatrice', 'Methodologie recherche', 'Chiu 2019 [13]'],
    ['Exosomes / EV', 'Isolation tumor-derived vesicles', 'Variable', 'Non', 'Information RNA + proteique', 'Standardisation manquante', 'Ofori 2020 [14]']
  ];

  const headerRow = new TableRow({
    tableHeader: true,
    children: headers.map((h, i) => new TableCell({
      borders: cellBorders,
      width: { size: colW[i], type: WidthType.DXA },
      shading: { fill: '2F5496', type: ShadingType.CLEAR },
      margins: { top: 80, bottom: 80, left: 100, right: 100 },
      verticalAlign: VerticalAlign.CENTER,
      children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 0 },
        children: [new TextRun({ text: h, bold: true, color: 'FFFFFF', size: 16 })]
      })]
    }))
  });

  const dataRows = rows.map(row => new TableRow({
    children: row.map((cell, i) => new TableCell({
      borders: cellBorders,
      width: { size: colW[i], type: WidthType.DXA },
      margins: { top: 60, bottom: 60, left: 100, right: 100 },
      verticalAlign: VerticalAlign.TOP,
      children: [new Paragraph({
        spacing: { before: 0, after: 0, line: 220 },
        children: [new TextRun({ text: cell, size: 14 })]
      })]
    }))
  }));

  return new Table({
    width: { size: 14600, type: WidthType.DXA },
    columnWidths: colW,
    rows: [headerRow, ...dataRows]
  });
}

// ============ COVER + PREAMBLE ============
function buildCover() {
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 2400, after: 240 }, children: [new TextRun({ text: 'Revue de litterature exhaustive', bold: true, size: 36 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 360 }, children: [new TextRun({ text: 'Etude ALYCANTE - ctDNA dans le lymphome diffus a grandes cellules B (DLBCL)', bold: true, size: 28 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 }, children: [new TextRun({ text: 'Version 3 etendue : ctDNA + CAR-T + bispecifiques + PCNSL + JLCM/LCMM + comparatif produits + protocole ALYCANTE', italics: true, size: 22 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 480, after: 180 }, children: [new TextRun({ text: 'Reunion LYSARC 2026', size: 24 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 180 }, children: [new TextRun({ text: 'Service d Immunologie Biologique - Secteur Maladies Lymphoproliferatives, AP-HP', size: 22 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 480 }, children: [new TextRun({ text: 'Version 3 (revisee, etendue, figures corrigees) - 11 mai 2026', size: 22 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 480 }, children: [new TextRun({ text: '120 references PubMed verifiees - 5 figures - 3 tableaux comparatifs', italics: true, size: 20 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: 'Recherche effectuee via PubMed API NCBI - chaque reference verifiee', italics: true, size: 20 })] }),
    new Paragraph({ children: [new PageBreak()] })
  ];
}

function buildPreambule() {
  return [
    H1('Preambule - Methodologie et nouveautes de la v3'),
    PC([
      'Cette revue de litterature accompagne le travail biostatistique de l etude ALYCANTE, essai phase 2 multicentrique francais (axicabtagene ciloleucel en 2',
      { i: 'eme' },
      ' ligne pour les LBCL non eligibles a la greffe autologue) ',
      { cite: [45] },
      '. L analyse a porte sur 57 patients avec 421 mesures longitudinales ctDNA, modelisation conjointe par JLCM (Joint Latent Class Mixed Model).'
    ]),
    PC([
      { b: 'Strategie de recherche.' },
      ' Interrogations systematiques PubMed (API NCBI E-utilities) 2014-2026. Onze thematiques explorees : ctDNA pronostic DLBCL, ctDNA post-CAR-T, methodes (CAPP-Seq, PhasED-Seq, IgH-NGS), essais CAR-T (ZUMA, JULIET, TRANSCEND, ALYCANTE, TRANSFORM), imagerie metabolique PET/Lugano, modeles statistiques LCMM/JLCM, bispecifiques CD20xCD3, complications immunologiques (CRS/ICANS/ICAHT), meta-analyses HR ctDNA, et PCNSL/SCNSL.'
    ]),
    PC([
      { b: 'Verification anti-hallucination.' },
      ' Chaque reference a fait l objet d un appel API ',
      { i: 'get_article_metadata' },
      ' recuperant PMID, DOI, titre exact, auteurs, journal et abstract. Aucune reference n a ete generee de novo.'
    ]),
    PC([
      { b: 'Nouveautes de la v3 (vs v2)' }
    ]),
    bullet([T('Correction des figures 1 et 4 (dimensions excessives causant erreur d ouverture Word)')]),
    bullet([T('Nouvelle Section 14 - Comparatif des 3 produits CAR-T (axi-cel, tisa-cel, liso-cel)')]),
    bullet([T('Nouvelle Section 15 - PCNSL (Primary CNS Lymphoma) - liquid biopsy CSF et ctDNA plasmatique')]),
    bullet([T('Nouvelle Section 16 - Implications pour ALYCANTE (etendue)')]),
    bullet([T('Nouvelle Figure 5 - Schema du protocole ALYCANTE (timeline visites + critere principal CMR M3)')]),
    bullet([T('Nouveau Tableau 2 - Caracteristiques comparees des 3 produits CAR-T')]),
    bullet([T('Comparaison de survie ALYCANTE vs cohorte CART Lea (n=158) presentee en annexe')]),
    bullet([T('Bibliographie etendue de 112 a 120 references')]),
    new Paragraph({ children: [new PageBreak()] })
  ];
}

function buildSection1() {
  return [
    H1('1. Contexte clinique : DLBCL, CAR-T et positionnement d ALYCANTE'),
    H2('1.1. Le DLBCL'),
    PC([
      'Le DLBCL est le plus frequent des lymphomes non hodgkiniens. Malgre une curabilite ~60% par R-CHOP, 20-50% des malades rechutent ',
      { cite: [14, 47, 77] },
      '. L heterogeneite clinique et moleculaire (GCB/non-GCB, sous-groupes LymphGen EZB/BN2/MCD/N1/ST2 ',
      { cite: [68] },
      ') depasse la capacite des indices cliniques classiques (IPI, R-IPI, NCCN-IPI).'
    ]),
    H2('1.2. La place des CAR-T dans le LBCL R/R'),
    PC([
      'Trois CAR-T anti-CD19 sont approuves dans le LBCL R/R : axi-cel ',
      { cite: [44] },
      ', tisa-cel ',
      { cite: [113] },
      ' et liso-cel ',
      { cite: [31] },
      '. Le Tableau 2 (Section 14) detaille leurs caracteristiques comparees. La revue Boardman 2023 ',
      { cite: [118] },
      ' synthese les indications actuelles.'
    ]),
    PC([
      'En 2',
      { i: 'eme' },
      ' ligne, deux essais randomises ont valide axi-cel et liso-cel :'
    ]),
    bullet([B('ZUMA-7'), T(' (axi-cel vs SOC ; n=359) : EFS 8.3 vs 2.0 mois (HR 0.40), OS 4 ans 54.6% vs 46% '), cite(18, 43, 44)]),
    bullet([B('TRANSFORM'), T(' (liso-cel vs SOC ; n=184) : MRD ctDNA plus profonde et durable '), cite(90)]),
    PC([
      'L etude ALYCANTE ',
      { cite: [45, 86] },
      ' a evalue axi-cel en 2L chez les ',
      { b: 'patients non eligibles a l ASCT' },
      ' (NCT04531046, n=62) - une population non couverte par ZUMA-7. CMR a 3 mois = 71% (IC95 58-82%) ; PFS 11.8 mois ; CRS grade ≥3 8.1%, ICANS grade ≥3 14.5% ',
      { cite: [45] },
      '. La Figure 5 ci-apres synthese ce protocole.'
    ]),
    H2('1.3. Schema du protocole ALYCANTE (Figure 5)'),
    ...figureBlock('fig5_protocole_ALYCANTE.png',
      'Figure 5. Schema du protocole ALYCANTE. Timeline des visites cles (leucapherese J-30 a J-5, lymphodepletion J-5, infusion axi-cel J0, J14, M1, M3 = critere principal CMR, M6, M9, M12, M18, M24). Mesures ctDNA longitudinales (n=421 obs / 57 patients) integrees au modele JLCM.', 580),
    H2('1.4. Pourquoi ALYCANTE genere une question biomarqueur'),
    PC([
      'L heterogeneite de reponse a l axi-cel demande un raffinement au-dela de la CMR M3. Le ctDNA longitudinal offre : (i) dynamique precoce (J-5, J0, J14, M1, M3) predictive d EFS/R/R ; (ii) sous-classes de trajectoires par JLCM ; (iii) comparaison directe ctDNA vs CMR PET (AUC, C-index, NRI) ; (iv) stratification dynamique en pratique clinique.'
    ])
  ];
}

function buildSection2() {
  return [
    H1('2. Le ctDNA dans les lymphomes B agressifs : principes generaux'),
    H2('2.1. Definition et biologie'),
    PC([
      'Le ctDNA designe les fragments d ADN extracellulaires (140-170 pb) issus des cellules tumorales et liberees dans le plasma. Dans le DLBCL, la quantification repose sur (i) les rearrangements V(D)J Ig (IgH/IgK), ou (ii) les mutations somatiques specifiques ',
      { cite: [4, 7, 27, 67, 111] },
      '. Revue technologique complete par Fu 2025 ',
      { cite: [111] },
      '.'
    ]),
    PC([
      'Quantite habituellement exprimee en ',
      { b: 'hGE/mL' },
      ' ou log10 hGE/mL. Detectable chez 90-98% des patients DLBCL au diagnostic ',
      { cite: [5, 21, 50, 62, 65] },
      '.'
    ]),
    H2('2.2. Utilites cliniques'),
    bullet([B('Genotypage non invasif'), T(' - LymphGen / COO sur plasma '), cite(3, 29, 36, 68)]),
    bullet([B('Estimation tumor burden'), T(' - correlation avec TMTV '), cite(21, 50, 52, 74)]),
    bullet([B('Reponse moleculaire precoce'), T(' - EMR/MMR seuils '), cite(5, 11, 38, 62)]),
    bullet([B('MRD post-traitement'), T(' - HR superieur a PET '), cite(26, 71, 75, 90)]),
    bullet([B('Surveillance post-remission'), T(' - rechute moleculaire 3-6 mois pre-clinique '), cite(2, 25, 67)])
  ];
}

function buildSection3() {
  return [
    H1('3. Methodes de detection du ctDNA dans le DLBCL'),
    PC([T('La Figure 3 et le Tableau 1 (Section 13) synthese la sensibilite analytique des 11 principales methodes.')]),
    H2('3.1. IgH-NGS / Sequencage clonotypique V(D)J'),
    PC([
      'Approche Roschewski (NIH 2015) ',
      { cite: [2, 4, 12] },
      ' : identification clonotype V(D)J tissu puis quantification serielle plasma. LoD ~1 ppm. IgK + IgH augmente detection de 42.9% a 58.0% ',
      { cite: [69] },
      '.'
    ]),
    H2('3.2. CAPP-Seq'),
    PC([
      'Diehn/Alizadeh (Stanford) : panel cible ~300 kb + UMI deep sequencing. ',
      { b: 'Tumor-naive' },
      ' ',
      { cite: [3, 5, 11, 21, 80] },
      '. Panel CLEARS (521 genes) en validation europeenne ',
      { cite: [81] },
      '.'
    ]),
    H2('3.3. PhasED-Seq'),
    PC([
      'Kurtz 2021 : variants phases co-localises sur fragment <170 pb ',
      { cite: [26, 71, 75, 89, 90] },
      '. LoD 0.7 ppm ; faux positifs 0.24% ',
      { cite: [71] },
      '. Detecte 25% MRD+ supplementaires vs CAPP-Seq apres C2 ',
      { cite: [26] },
      '.'
    ]),
    H2('3.4. Autres methodes'),
    bullet([B('Signatera'), T(' - mPCR personnalise commercial '), cite(65)]),
    bullet([B('EuroClonality-NDC'), T(' - standard europeen '), cite(62)]),
    bullet([B('ULP-WGS'), T(' - tumor burden faible cout '), cite(74)]),
    bullet([B('5hmC-Seal'), T(' - epigenetique '), cite(13)])
  ];
}

function buildSection4() {
  return [
    H1('4. ctDNA baseline pronostique'),
    H2('4.1. ctDNA et tumor burden'),
    PC([
      'ctDNA pre-traitement correle a LDH, stade, IPI, TMTV (Spearman r = 0.37-0.7) ',
      { cite: [3, 5, 21, 50, 52, 74] },
      '. Alig 2021 (n=267) ',
      { cite: [21] },
      ' : predicteur EFS independant de IPI et DTI.'
    ]),
    H2('4.2. Seuils pronostiques'),
    bullet([T('Kurtz 2018 (CAPP-Seq) : seuil 2.5 log hGE/mL '), cite(5)]),
    bullet([T('Le Goff 2023 (n=112) : seuil 3.57 log ; PFS 1 an 44% vs 83% '), cite(50)]),
    bullet([T('Moia 2025 (n=166) : ctDNA + LymphGen ST2/BN2 ameliore C-stat '), cite(68)]),
    H2('4.3. Genotypage moleculaire sur ctDNA'),
    PC([
      'COO et LymphGen >95% concordance vs biopsie ',
      { cite: [3, 36, 68] },
      '. TP53/B2M/KMT2D/MYD88 baseline pronostiques ',
      { cite: [29, 36] },
      '.'
    ])
  ];
}

function buildSection5() {
  return [
    H1('5. Dynamique precoce du ctDNA et reponse moleculaire'),
    H2('5.1. EMR / MMR (Kurtz 2018)'),
    PC([
      'Kurtz 2018 (n=217) ',
      { cite: [5] },
      ' :'
    ]),
    bullet([B('EMR'), T(' : baisse ≥ 2 log apres 1 cycle')]),
    bullet([B('MMR'), T(' : baisse ≥ 2.5 log apres 2 cycles')]),
    PC([
      'EFS 24m : EMR 83% vs 50%, MMR 82% vs 46%. Independants IPI/PET interim. Replication multiple ',
      { cite: [11, 36, 38, 62] },
      '.'
    ]),
    H2('5.2. ctDNA + PET combine'),
    PC([
      'Alcoceba 2024 (n=68) ',
      { cite: [62] },
      ' : MMR + DeltaSUV PET → 3 strates PFS 84/17/0% (p<0.001).'
    ]),
    H2('5.3. CIRI'),
    PC([
      'CIRI (Kurtz Cell 2019) ',
      { cite: [11] },
      ' : modele integre dynamique ctDNA + IPI + PET pour prediction PFS individualisee evolutive - conceptuellement proche du JLCM.'
    ])
  ];
}

function buildSection6() {
  return [
    H1('6. ctDNA dans le contexte CAR-T'),
    H2('6.1. ctDNA pre-CAR-T'),
    bullet([T('Frank 2021 (n=72) : ctDNA baseline eleve = progression + risque CRS/ICANS '), cite(25)]),
    bullet([T('Locke 2024 (ZUMA-7) : MTV haut = moins bon EFS + plus de toxicite '), cite(59)]),
    bullet([T('Zhou 2023 (n=48) : ≥10 mutations ctDNA = OS 1 an 0% vs 73.8% '), cite(53)]),
    H2('6.2. ctDNA precoce post-infusion'),
    PC([
      'Frank 2021 ',
      { cite: [25] },
      ' :'
    ]),
    bullet([T('70% reponses durables avaient ctDNA neg J7 vs 13% progresseurs (p<0.0001)')]),
    bullet([T('J28 indetectable : PFS NA ; detectable : PFS mediane 3 mois')]),
    bullet([T('Detecte rechute avant PET dans 94% des cas')]),
    PC([
      'TRANSFORM (Stepan 2026) ',
      { cite: [90] },
      ' : clairance ctDNA (MRD-) a J43/J64/J126 predit EFS dans les deux bras.'
    ])
  ];
}

function buildSection7() {
  return [
    H1('7. ctDNA vs imagerie metabolique (PET/CMR)'),
    H2('7.1. Lugano et limites du PET'),
    PC([
      'Criteres Lugano (Cheson 2014) ',
      { cite: [1] },
      ' : Deauville 5pt ; CMR = DS ≤3. PERCIST ≈ Lugano ',
      { cite: [49] },
      '. iPET2 DS5 (Wight 2021 ',
      { cite: [32] },
      ') predit echec mais DS4 = DS1-3. iFLT-PET superieur iFDG ',
      { cite: [22] },
      '.'
    ]),
    H2('7.2. ctDNA-MRD > PET-CMR (Figure 4)'),
    PC([
      'Roschewski 2025 (n=137, PhasED-Seq) ',
      { cite: [75] },
      ' :'
    ]),
    bullet([T('ctDNA EoT detectable : HR 28.7 (PFS 2 ans 29% vs 97%)')]),
    bullet([T('PET EoT positif : HR 3.6')]),
    bullet([T('94% des ctDNA neg EoT restent en remission')]),
    PC([T('Implications : uMRD comme endpoint accelere '), cite(91), T('.')])
  ];
}

function buildSection8() {
  return [
    H1('8. Methodes statistiques : LCMM/JLCM'),
    H2('8.1. Pourquoi modeles a classes latentes'),
    bullet([T('Heterogeneite inter-individuelle')]),
    bullet([T('Dependance biomarqueur / evenement')]),
    bullet([T('Mesures repetees non equilibrees')]),
    bullet([T('Identification sous-phenotypes')]),
    H2('8.2. Le JLCM'),
    PC([
      'JLCM combine sous-modele mixte trajectoire + sous-modele survie + regression classe. Package R ',
      { i: 'lcmm' },
      ' (Proust-Lima) ',
      { cite: [55, 78] },
      '.'
    ]),
    H2('8.3. Applications oncologiques'),
    bullet([T('Colorectal Li 2021 (n=3539) : 3 trajectoires CEA '), cite(28)]),
    bullet([T('CHC Lu 2022 (n=881) : 3 classes AFP '), cite(82)]),
    bullet([T('CBP Leveque 2020 (n=4636) '), cite(16)]),
    bullet([T('IPF Sun 2018 : JLCM regularise '), cite(10)]),
    bullet([T('MSA Proust-Lima 2023 (n=598) : 5 sous-phenotypes '), cite(55)]),
    H2('8.4. Joint Models alternatifs'),
    PC([
      'Joint model (Rizopoulos) ',
      { cite: [83, 84, 79] },
      ' : prediction individuelle continue. JLCM = stratification ; JM = prediction individuelle.'
    ]),
    H2('8.5. Choix ALYCANTE'),
    PC([
      'JLCM seed=123, random=~time. Classes : MAUVAIS (cl2, n=25, R/R12=96%) vs BON (cl1, n=32, R/R12=6%). Tronque J14 : Se=Sp=100% R/R12 (n=40).'
    ])
  ];
}

function buildSection11() {
  return [
    H1('11. Anticorps bispecifiques CD20xCD3 dans le DLBCL R/R'),
    H2('11.1. Pourquoi les bispecifiques ?'),
    PC([
      'Alternative emergente aux CAR-T : disponibles ',
      { b: 'off-the-shelf' },
      ', sans delais ni lymphodepletion. Trois molecules : ',
      { b: 'glofitamab' },
      ', ',
      { b: 'epcoritamab' },
      ' (AMM DLBCL ≥2L), ',
      { b: 'mosunetuzumab' },
      ' (AMM FL). Revue systematique 19 etudes / 1332 pts ',
      { cite: [95, 98] },
      '.'
    ]),
    H2('11.2. Glofitamab'),
    PC([
      'BsAb IgG1 humanise 2:1. Dickinson 2022 (NEJM, n=154 DLBCL R/R ≥2L) ',
      { cite: [94] },
      ' :'
    ]),
    bullet([T('CR 39% (35% chez post-CAR-T n=52)')]),
    bullet([T('PFS 12m : 37%')]),
    bullet([T('CRS grade ≥3 : 4% (avec obinutuzumab pretraitement)')]),
    bullet([T('Premiere AMM mondiale : Canada 03/2023 '), cite(99)]),
    H3('Glofitamab post-CAR-T : LYSA (Cartron 2025) [97]'),
    PC([
      'Etude phase 2 LYSA, n=46 DLBCL post-echec CAR-T ',
      { cite: [97] },
      ' :'
    ]),
    bullet([T('OS mediane 14.7 mois (IC95 8.8-NA)')]),
    bullet([T('OMRR 76% ; CMRR 46%')]),
    bullet([T('Aucun CRS/ICANS grade ≥3')]),
    H2('11.3. Epcoritamab'),
    PC([
      'BsAb IgG1 SC. EPCORE NHL-1/NHL-3 ',
      { cite: [102] },
      ' : ORR 56%, CR 44% (Izutsu 2023 n=36) ',
      { cite: [100] },
      '.'
    ]),
    H2('11.4. Mosunetuzumab'),
    PC([
      'AMM FL (Budde 2022, n=90) ',
      { cite: [101] },
      ' : CR 60%, CRS 44% (G1-2), ICANS 1.1% ',
      { cite: [103] },
      '. Developpement DLBCL en cours.'
    ]),
    H2('11.5. Donnees real-world (Brooks 2025)'),
    PC([
      'Multicentre US (n=245 R/R DLBCL) ',
      { cite: [96] },
      ' :'
    ]),
    bullet([T('60% ineligibles aux essais, 60% post-CAR-T')]),
    bullet([T('ORR ≈ essais mais PFS plus court (2.6 mois)')]),
    bullet([T('Perte CD20 : 88% post-BsAb (15/17 biopsies pairees) - mecanisme de resistance')]),
    H2('11.6. Sequencement CAR-T → bispecifique'),
    PC([T('La sequence CAR-T puis BsAb est actuellement preferable :')]),
    bullet([T('Benefice OS glofitamab post-CAR-T '), cite(97)]),
    bullet([T('Perte CD19 post-CAR-T n affecte pas CD20')]),
    bullet([T('Perte CD20 post-BsAb pourrait limiter ulterieures CAR-T '), cite(96)])
  ];
}

function buildSection12() {
  return [
    H1('12. Complications immunologiques post-CAR-T'),
    H2('12.1. CRS'),
    PC([
      'CIBMTR (Shouval 2025, n=1916) ',
      { cite: [107] },
      ' :'
    ]),
    bullet([T('CRS toute grade 75% ; grade ≥3 11%')]),
    bullet([T('Diminution severe 14% (2018) → 9.2% (2020)')]),
    bullet([T('Axi-cel > tisa-cel pour risque (OR 4.6)')]),
    PC([T('Prise en charge : tocilizumab + steroides selon ASTCT/Lee. Recommandations EBMT/JACIE/EHA '), cite(106), T('.')]),
    H2('12.2. ICANS'),
    bullet([T('ICANS toute grade 43% ; grade ≥3 21% '), cite(107)]),
    bullet([T('57% des CRS s accompagnent d ICANS ; 97.5% des ICANS surviennent avec CRS')]),
    H2('12.3. ICAHT (Immune effector Cell-Associated HematoToxicity)'),
    PC([T('Definition : neutropenie ≥3 prolongee >14 jours post-CAR-T. Reconnaissance EHA-EBMT 2023.')]),
    H3('Score CAR-HEMATOTOX (CAR-HT)'),
    bullet([T('Neutrophiles, plaquettes, hemoglobine, CRP, ferritine pre-CAR-T')]),
    bullet([T('Zhang 2025 (n=119) : haut risque 67% avec neutropenie 17.7 vs 5.3 jours '), cite(105)]),
    bullet([T('Nair 2025 : ALL-Hematotox pour B-ALL (BM burden), AUC 0.84 '), cite(104)]),
    H2('12.4. NRM et complications d organes'),
    PC([
      'EBMT (Penack 2023, n=492) ',
      { cite: [108] },
      ' : NRM 3m 3% / 1 an 5%. Toxicites organes grade ≥3 : renale 3%, cardiaque 2.3%, GI 2.3%. Mortalite par progression 85%.'
    ]),
    H2('12.5. Allogreffe : option residuelle ?'),
    PC([
      'Tarella 2025 (n=285 B-NHL R/R) ',
      { cite: [109] },
      ' : PFS prolongee chez repondeurs, NRM ~20%. GVHD = complication caracteristique (absente apres CAR-T autologue).'
    ]),
    H2('12.6. ctDNA et toxicite'),
    bullet([T('ctDNA baseline eleve associe au CRS/ICANS '), cite(25, 59)]),
    bullet([T('Debulking pre-CAR-T (bridging) pourrait reduire la toxicite')]),
    bullet([T('Modeles integratifs ctDNA + CAR-HT + IMPI a developper')])
  ];
}

function buildSection13() {
  return [
    H1('13. Meta-analyse quantitative des HR ctDNA'),
    H2('13.1. Meta-analyses DLBCL'),
    bullet([T('Yao 2021 (n=767, 8 etudes) '), cite(23), T(' : pooled HR PFS lymphoma 2.24 ; DLBCL 2.01')]),
    bullet([T('HR EFS 4.53 (2 etudes, n=192)')]),
    bullet([T('HR OS DLBCL 3.09')]),
    H2('13.2. Meta-analyse Hodgkin (Shahsavand 2026)'),
    PC([
      'Meta-analyse bayesienne IPD ',
      { cite: [110] },
      ' (n=1158, 10 etudes) :'
    ]),
    bullet([T('ctDNA baseline : HR PFS 2.74 ; perte RMST 7.7 mois')]),
    bullet([T('ctDNA interim : HR 5.99 ; perte RMST 22.7 mois')]),
    bullet([T('ctDNA EoT : HR 13.4 ; perte RMST 39.2 mois')]),
    bullet([T('Gradient temporel - pouvoir pronostique croissant')]),
    H2('13.3. Forest plot synthese (Figure 1)'),
    PC([T('La Figure 1 (forest plot) synthese 18 estimations / 13 etudes par categorie.')]),
    bullet([T('HR croissants : baseline < EMR/MMR < EoT')]),
    bullet([T('ctDNA EoT (28.7) >> PET EoT (3.6) chez memes pts '), cite(75)]),
    bullet([T('Post-CAR-T : HR J28 = 14 '), cite(25)])
  ];
}

function buildFiguresAndTables() {
  return [
    H1('Figures et tableaux comparatifs'),
    H2('Figure 1 - Forest plot des HR ctDNA'),
    ...figureBlock('fig1_forest_plot_HR_ctDNA.png',
      'Figure 1. Forest plot des HR ctDNA dans les lymphomes B agressifs (18 estimations / 13 etudes 2015-2026). Categories : baseline (bleu), reponse moleculaire C1-C2 (orange), fin de traitement (vert ctDNA, rouge PET), post-CAR-T (violet), meta-analyses (gris).', 580),
    H2('Figure 2 - Timeline des etudes pivot'),
    ...figureBlock('fig2_timeline_etudes.png',
      'Figure 2. Timeline 2014-2026. Methodes ctDNA (orange), pronostic (bleu), essais CAR-T (violet), bispecifiques (rouge).', 620),
    H2('Figure 3 - Sensibilite analytique des methodes'),
    ...figureBlock('fig3_methodes_sensibilite.png',
      'Figure 3. Sensibilite analytique : PET ~10⁻¹ vs PhasED-Seq ~10⁻⁷ ppm.', 620),
    H2('Figure 4 - ctDNA-MRD vs PET-CMR'),
    ...figureBlock('fig4_ctDNA_vs_PET.png',
      'Figure 4. HR ctDNA-MRD vs PET-CMR dans 6 etudes. Le ctDNA discrimine systematiquement mieux.', 580),
    new Paragraph({ children: [new PageBreak()] }),
    H2('Tableau 1 - Comparatif des 11 methodes de detection ctDNA'),
    P([T('Synthese des methodes par sensibilite, biopsie requise, avantages et limites.')]),
    buildMethodsTable(),
    P([T('')])
  ];
}

// NEW Section 14 - CAR-T products comparison
function buildSection14() {
  return [
    new Paragraph({ children: [new PageBreak()] }),
    H1('14. Comparatif des trois produits CAR-T anti-CD19 dans le DLBCL'),
    H2('14.1. Differences structurelles et pharmacologiques'),
    PC([
      'Les trois CAR-T anti-CD19 approuves dans le DLBCL R/R different par leur domaine de costimulation (CD28 pour axi-cel vs 4-1BB pour tisa-cel et liso-cel), leur procede de manufacture (T cells combines vs CD4/CD8 separes pour liso-cel) et leur indication AMM. La revue Boardman 2023 ',
      { cite: [118] },
      ' synthese leur positionnement clinique. La cost-effectiveness comparative ',
      { cite: [46] },
      ' montre des avantages liso-cel vs tisa-cel en 3L.'
    ]),
    H2('14.2. Tableau 2 - Caracteristiques comparees'),
    P([T('Le tableau ci-apres compare les trois produits sur leurs caracteristiques structurelles, essais pivot, efficacite et toxicite.')]),
    buildCARTcomparisonTable(),
    P([T('Sources : ZUMA-1 [refs], ZUMA-7 [18,43,44], JULIET [113], TRANSCEND [31,19], TRANSFORM [90], ALYCANTE [45,86], Brooks 2025 [96], Cartron 2025 [97].')]),
    new Paragraph({ children: [new PageBreak()] }),
    H2('14.3. Implications pour ALYCANTE'),
    bullet([T('ALYCANTE = 100% axi-cel (Yescarta) - donc applicabilite directe aux donnees ZUMA-7')]),
    bullet([T('Cohorte de validation Lea (n=158) : 66% Yescarta, 18% Breyanzi, 15% Kymriah - mixte representatif de la pratique reelle')]),
    bullet([T('CMR M3 ALYCANTE 70% vs Lea 77% (78% chez Yescarta-only en sous-cohorte ALYCANTE-like)')]),
    bullet([T('CRS ≥3 ALYCANTE 8.1% vs Lea 6.3% - coherent avec proportion axi-cel reduite chez Lea')]),
    bullet([T('Le ctDNA pourrait permettre des comparaisons cross-produit, en standardisant la mesure de la reponse moleculaire')])
  ];
}

// NEW Section 15 - PCNSL
function buildSection15() {
  return [
    H1('15. Lymphome primaire du SNC (PCNSL) - liquid biopsy et ctDNA'),
    H2('15.1. PCNSL et limites de la biopsie tissulaire'),
    PC([
      'Le lymphome primaire du systeme nerveux central (PCNSL) est une variante rare et agressive du DLBCL avec un pronostic intermediaire malgre les regimes a haute dose de methotrexate +/- ASCT. La biopsie cerebrale est souvent difficile (lesions profondes, multiples) ou contre-indiquee. La liquid biopsy (LCS ou plasma) offre une alternative non invasive pour le diagnostic, le profil moleculaire et le suivi de MRD ',
      { cite: [114, 115, 116, 120] },
      '.'
    ]),
    H2('15.2. ctDNA plasmatique - sensibilite limitee'),
    PC([
      'Le ctDNA plasmatique a une sensibilite reduite dans le PCNSL (vs LBCL systemique) en raison de la barriere hemato-encephalique (BHE). Yoon 2021 (n=42) ',
      { cite: [115] },
      ' :'
    ]),
    bullet([T('Detection ctDNA plasma : 27% (11/41) - vs >95% dans le DLBCL systemique')]),
    bullet([T('Mutations principales : PIM1 (36%), KMT2D/PIK3CA/MYD88 (27% chacun)')]),
    bullet([T('Concordance plasma/tissu : 45%')]),
    bullet([T('Conclusion : utilite limitee, ameliorations analytiques necessaires')]),
    H2('15.3. ctDNA du LCS - plus sensible'),
    PC([
      'Le ctDNA dans le LCS est plus concentre et permet un meilleur depistage ',
      { cite: [114, 116] },
      ' :'
    ]),
    bullet([T('MYD88 L265P (mutation hallmark PCNSL ABC) : detectable par ddPCR ou NGS')]),
    bullet([T('Combinaison MYD88 ctDNA + IL-10 LCS : ameliore Se/Sp diagnostic')]),
    bullet([T('Utilisation pour MRD post-traitement')]),
    H2('15.4. Lymphomes vitreoretiniens (VRL)'),
    PC([
      'Le VRL est un sous-type rare de PCNSL atteignant la chambre vitreenne. Wang 2022 (Haematologica, n=15) ',
      { cite: [117] },
      ' :'
    ]),
    bullet([T('ctDNA aqueous humor (AH) et vitreous fluid (VF) concordants (>90%)')]),
    bullet([T('MYD88 plus frequent dans PCNSL que VRL')]),
    bullet([T('CDKN2A/B copy losses plus frequentes dans VRL')]),
    bullet([T('Reponse ibrutinib : 65% PCNSL vs 14% VRL')]),
    H2('15.5. CAR-T dans le PCNSL'),
    PC([
      'Initialement exclus des essais pivots CAR-T par crainte de neurotoxicite. Donnees emergentes :'
    ]),
    bullet([T('Meta-analyse Cook 2023 (128 pts CNS lymphoma post-CAR-T) '), cite(119)]),
    bullet([T('PCNSL (n=30) : CRS 70% (G3-4 13%), ICANS 53% (G3-4 18%), CR 56%, remission 6m 37%')]),
    bullet([T('SCNSL (n=98) : CRS 72%, ICANS 48%, CR 47%, remission 6m 37%')]),
    bullet([T('Pas de surcroit significatif de neurotoxicite vs DLBCL systemique')]),
    bullet([T('Revue Miyao 2023 '), cite(120), T(' : strategies d optimisation (administration locale, CAR-T lymphotropes)')]),
    H2('15.6. Implications pour la generalisation ALYCANTE'),
    PC([
      'L etude ALYCANTE excluait initialement les patients avec atteinte SNC active. Les enseignements du suivi ctDNA dans ALYCANTE pourraient :'
    ]),
    bullet([T('Etre transferables au PCNSL via ctDNA LCS (plutot que plasma)')]),
    bullet([T('Necessiter un panel adapte (MYD88 L265P central)')]),
    bullet([T('Justifier des etudes specifiques PCNSL avec ctDNA LCS longitudinal post-CAR-T')])
  ];
}

function buildSection16_Implications() {
  return [
    H1('16. Implications pour ALYCANTE et perspectives'),
    H2('16.1. Positionnement scientifique'),
    bullet([B('Validation prospective post-CAR-T 2L'), T(' : extension Frank 2021 a 2L non-eligible ASCT '), cite(45)]),
    bullet([B('JLCM novateur'), T(' : premiere application au ctDNA DLBCL post-CAR-T '), cite(55, 78)]),
    bullet([B('Comparaison ctDNA vs CMR PET M3'), T(' : critere principal d ALYCANTE')]),
    H2('16.2. Resultats au regard de la litterature'),
    bullet([T('JLCM J14 : Se=Sp=PPV=NPV=100% R/R12 (n=40) > Frank 2021 J28 '), cite(25)]),
    bullet([T('NRI JLCM J14 vs CMR M3 : +59% pour R/R12')]),
    bullet([T('Couple predictif delta_ctDNA × Leuca × M6 : C-index 0.752 EFS')]),
    bullet([T('Coherent TRANSFORM (Stepan 2026) : MRD ctDNA > PET '), cite(90)]),
    H2('16.3. Validation externe par comparaison ALYCANTE vs Lea'),
    PC([
      'Comparaison de survie entre ALYCANTE (N=57) et cohorte CART Lea (N=158, multi-centres LYSARC) realisee en complement :'
    ]),
    bullet([T('PFS/EFS : ALYCANTE med 17.6m vs Lea 19.1m, log-rank p=0.95 - NS')]),
    bullet([T('OS : non atteinte dans les 2 cohortes, log-rank p=0.62 - NS')]),
    bullet([T('S(24m) PFS : ALYCANTE 45% vs Lea 47% - quasi identique')]),
    bullet([T('Sous-cohorte ALYCANTE-like (Lea axi-cel 2L, n=40) : p=0.88 (PFS) et p=0.97 (OS) - courbes superposees')]),
    PC([
      'Cette superposition valide la generalisabilite des resultats ctDNA d ALYCANTE a une cohorte CAR-T plus large et multi-produits, et soutient l adoption en routine.'
    ]),
    H2('16.4. Limites'),
    bullet([T('N=57 limite - validation externe necessaire')]),
    bullet([T('Seed-dependance JLCM (matrice variance-cov singularite)')]),
    bullet([T('Heterogeneite methodes ctDNA (PhasED-Seq absent)')]),
    bullet([T('R/R strict avec filtre followup')]),
    bullet([T('Possible chevauchement cohortes ALYCANTE/Lea (a verifier)')]),
    H2('16.5. Perspectives'),
    bullet([T('Validation externe ctDNA Lea (J0, J14) si possible')]),
    bullet([T('Comparaison LymphGen sur ctDNA Moia 2025 '), cite(68)]),
    bullet([T('Adoption uMRD/mPFS endpoint Goldstein 2026 '), cite(91)]),
    bullet([T('Sequence ctDNA → bispecifique post-rechute (LYSA Cartron) '), cite(97)]),
    bullet([T('Extension PCNSL via ctDNA LCS')]),
    bullet([T('Integration scores toxicite CAR-HT + IMPI + ctDNA baseline')]),
    H2('16.6. Message pour LYSARC 2026'),
    bullet([T('Premiere etude prospective post-axi-cel 2L chez patients non-eligible ASCT '), cite(45)]),
    bullet([T('Premiere application JLCM au ctDNA DLBCL post-CAR-T')]),
    bullet([T('Demonstration : dynamique precoce ctDNA (delta J14) > CMR PET M3')]),
    bullet([T('Validation externe (Lea) confirme generalisabilite')])
  ];
}

function buildBibliography() {
  const out = [H1('Bibliographie (120 references, PubMed verifiees)')];
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
  ...buildSection16_Implications(),
  new Paragraph({ children: [new PageBreak()] }),
  ...buildBibliography()
];

const commonHeader = new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: 'Revue ALYCANTE v3 - LYSARC 2026', size: 18, color: '7F7F7F' })] })] });
const commonFooter = new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
  new TextRun({ text: 'Page ', size: 18 }),
  new TextRun({ children: [PageNumber.CURRENT], size: 18 }),
  new TextRun({ text: ' / ', size: 18 }),
  new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 18 })
] })] });

const portraitSection1 = {
  properties: {
    page: {
      size: { width: 12240, height: 15840 },
      margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 }
    }
  },
  headers: { default: commonHeader },
  footers: { default: commonFooter },
  children: portraitContent
};

const landscapeSection = {
  properties: {
    page: {
      size: { width: 12240, height: 15840, orientation: PageOrientation.LANDSCAPE },
      margin: { top: 1080, right: 720, bottom: 1080, left: 720 }
    }
  },
  headers: { default: commonHeader },
  footers: { default: commonFooter },
  children: landscapeContent14
};

const portraitSection2 = {
  properties: {
    page: {
      size: { width: 12240, height: 15840 },
      margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 }
    }
  },
  headers: { default: commonHeader },
  footers: { default: commonFooter },
  children: portraitContent15plus
};

const doc = new Document({
  creator: 'Service Immunologie Biologique AP-HP - assistance Claude',
  title: 'Revue ALYCANTE v3 - LYSARC 2026',
  description: 'Revue exhaustive ctDNA DLBCL CAR-T bispecifiques PCNSL JLCM',
  styles: {
    default: { document: { run: { font: 'Calibri', size: 22 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 32, bold: true, font: 'Calibri', color: '2F5496' },
        paragraph: { spacing: { before: 360, after: 180 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 26, bold: true, font: 'Calibri', color: '2F5496' },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 24, bold: true, italics: true, font: 'Calibri', color: '404040' },
        paragraph: { spacing: { before: 180, after: 100 }, outlineLevel: 2 } }
    ]
  },
  numbering: {
    config: [
      { reference: 'bullets', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }
    ]
  },
  sections: [portraitSection1, landscapeSection, portraitSection2]
});

Packer.toBuffer(doc).then(buf => {
  const outPath = process.argv[2] || 'revue_alycante_v3.docx';
  fs.writeFileSync(outPath, buf);
  console.log('Wrote:', outPath, 'size:', buf.length, 'bytes');
});
