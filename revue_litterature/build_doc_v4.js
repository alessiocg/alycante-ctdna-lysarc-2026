// Revue de literature ALYCANTE v4 - redaction analytique fluide
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
  // Paragraphe sans indentation de premiere ligne (apres titre)
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

// Construit un paragraphe a partir d'un tableau de parts (string | {b} | {i} | {cite})
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

// ============ TABLES (reused from v3) ============
function buildCARTcomparisonTable() {
  const cellBorder = { style: BorderStyle.SINGLE, size: 1, color: 'BFBFBF' };
  const cellBorders = { top: cellBorder, bottom: cellBorder, left: cellBorder, right: cellBorder };
  const headers = ['Caracteristique', 'Axi-cel (Yescarta)', 'Tisa-cel (Kymriah)', 'Liso-cel (Breyanzi)'];
  const colW = [3500, 3700, 3700, 3700];

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
    width: { size: 14600, type: WidthType.DXA },
    columnWidths: colW, rows: [headerRow, ...dataRows]
  });
}

function buildMethodsTable() {
  const cellBorder = { style: BorderStyle.SINGLE, size: 1, color: 'BFBFBF' };
  const cellBorders = { top: cellBorder, bottom: cellBorder, left: cellBorder, right: cellBorder };
  const headers = ['Methode', 'Approche', 'LoD', 'Biopsie ?', 'Avantages', 'Limites', 'Etudes representatives'];
  const colW = [1700, 2300, 1400, 1300, 2500, 2500, 2900];
  const rows = [
    ['IgH-NGS / clonotype VDJ', 'Clonotype Ig dominant tissu puis quantification plasma', '~1 ppm', 'Oui', 'Specifique tumeur, sensible, tout B-NHL', 'Necessite biopsie informative', 'Roschewski 2015 [2], Frank 2021 [25], Wang 2025 [69]'],
    ['CAPP-Seq', 'Panel cible recurrent + UMI deep sequencing', '~1-10 ppm', 'Non', 'Tumor-naive, genotypage simultane', 'Cout, expertise bioinfo', 'Scherer 2016 [3], Kurtz 2018 [5], Alig 2021 [21], Moia 2025 [68]'],
    ['PhasED-Seq', 'Variants phases co-localises (reduction bruit fond)', '~0.7 ppm', 'Recommandee', 'Sensibilite ultra-elevee, ideal MRD', 'Cout eleve', 'Kurtz 2021 [26], Klimova 2025 [71], Roschewski 2025 [75], Stepan 2026 [90]'],
    ['Signatera (mPCR)', 'Panel multiplex 16 SNV tumor-informed', '~1-10 ppm', 'Oui', 'Workflow commercial', 'Limite a 16 SNV', 'Narkhede 2024 [65]'],
    ['EuroClonality-NDC', 'Panel NGS standardise europeen', '~10^-5', 'Plasma seul', 'Standardisation europeenne', 'Sensibilite < PhasED-Seq', 'Alcoceba 2024 [62]'],
    ['CLEARS (521 genes)', 'Panel etendu mutations lymphome', '~10^-4-10^-5', 'Non', 'Couverture genique etendue', 'Recouvrement variable', 'Vodicka 2025 [76], Hamova 2025 [81]'],
    ['ULP-WGS cfDNA', 'WGS faible profondeur (CNV/burden)', 'TF >3%', 'Non', 'Faible cout, detecte CNV', 'Sensibilite limitee MRD', 'Zhao 2025 [74]'],
    ['ddPCR (single mut)', 'PCR digitale mutation specifique', '~10^-3-10^-4', 'Oui', 'Cout faible, rapide', 'Une seule cible', 'Cas reports [72]'],
    ['Flow cytometry MRD', 'Phenotype B clonal residuel', '~10^-4', 'Non (moelle)', 'Bien etabli leucemie aigue', 'Peu applicable DLBCL', 'Liu 2023 [54]'],
    ['cfDNA 5hmC-Seal', 'Profilage epigenetique', '~10^-4', 'Non', 'Approche epigenetique', 'Methodologie recherche', 'Chiu 2019 [13]'],
    ['Exosomes / EV', 'Isolation tumor-derived vesicles', 'Variable', 'Non', 'Information RNA + proteique', 'Standardisation manquante', 'Ofori 2020 [14]']
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
  return new Table({ width: { size: 14600, type: WidthType.DXA }, columnWidths: colW, rows: [headerRow, ...dataRows] });
}

// ============ COVER + PREAMBLE ============
function buildCover() {
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 2400, after: 240 }, children: [new TextRun({ text: 'Revue de litterature exhaustive', bold: true, size: 36 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 360 }, children: [new TextRun({ text: 'Etude ALYCANTE - ctDNA dans le lymphome diffus a grandes cellules B (DLBCL)', bold: true, size: 28 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 }, children: [new TextRun({ text: 'Suivi longitudinal post-CAR-T, modeles a classes latentes joints et positionnement dans le paysage therapeutique 2026', italics: true, size: 22 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 720, after: 180 }, children: [new TextRun({ text: 'Reunion LYSARC 2026', size: 24 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 180 }, children: [new TextRun({ text: 'Service d Immunologie Biologique - Secteur Maladies Lymphoproliferatives, AP-HP', size: 22 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 480 }, children: [new TextRun({ text: 'Version 4 (redaction analytique) - 11 mai 2026', size: 22 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 720 }, children: [new TextRun({ text: '120 references PubMed verifiees - 5 figures de synthese - 2 tableaux comparatifs', italics: true, size: 20 })] }),
    new Paragraph({ children: [new PageBreak()] })
  ];
}

function buildPreambule() {
  return [
    H1('Preambule'),
    para([
      'Le lymphome diffus a grandes cellules B reste, malgre les progres therapeutiques accumules depuis l avenement du R-CHOP, une maladie ou la rechute precoce demeure frequente et le pronostic incertain pour 20 a 50 % des patients. Dans ce contexte, deux innovations bouleversent simultanement la prise en charge du DLBCL R/R : d une part les CAR-T cells anti-CD19, dont l indication s est etendue de la troisieme ligne (',
      { i: 'ZUMA-1, JULIET, TRANSCEND' },
      ') a la deuxieme ligne (',
      { i: 'ZUMA-7, TRANSFORM' },
      ') et, recemment, a la deuxieme ligne chez les patients non eligibles a l autogreffe avec l etude ',
      { b: 'ALYCANTE' },
      ' ; et d autre part, l essor du suivi par ADN tumoral circulant (ctDNA), qui permet une evaluation moleculaire non invasive plus precoce et plus sensible que l imagerie metabolique.'
    ], { first: true }),
    para([
      'La presente revue accompagne le travail biostatistique de l etude ALYCANTE-biomarqueurs (n = 57 patients, 421 mesures ctDNA longitudinales) presentee a la reunion LYSARC 2026. Elle vise a situer l originalite methodologique du projet - l application des modeles a classes latentes joints (JLCM) au suivi du ctDNA - dans le paysage international des biomarqueurs du DLBCL post-CAR-T. Elle integre egalement les developpements therapeutiques qui modifient le pronostic et la trajectoire de soins de cette population : anticorps bispecifiques CD20xCD3, complications immunologiques iatrogenes (CRS, ICANS, ICAHT) et perspectives dans le lymphome primaire du systeme nerveux central.'
    ]),
    H2('Methodologie de la recherche bibliographique'),
    para([
      'Les references ont ete identifiees par interrogations systematiques de PubMed (via l API officielle NCBI E-utilities) sur la periode 2014-2026, en croisant les termes MeSH appropries pour onze thematiques : ctDNA pronostic dans le DLBCL, ctDNA post-CAR-T, methodes analytiques (CAPP-Seq, PhasED-Seq, IgH-NGS), essais cliniques CAR-T pivots, imagerie metabolique PET et reponse selon les criteres de Lugano, modeles statistiques longitudinaux a classes latentes, anticorps bispecifiques CD20xCD3, complications immunologiques post-CAR-T, meta-analyses quantitatives des hazard ratios ctDNA, lymphome primaire du SNC, et methodologies comparees de detection. Chaque reference a fait l objet d un appel API ',
      { i: 'get_article_metadata' },
      ' garantissant l exactitude des informations bibliographiques (PMID, DOI, auteurs, journal, date) ; aucune reference n a ete generee de novo. Le corpus final compte 120 publications uniques apres deduplication.'
    ]),
    para([
      'Trois precautions methodologiques meritent d etre soulignees. Premierement, les resultats chiffres rapportes (medianes, hazard ratios, intervalles de confiance, taux de reponse) proviennent exclusivement des abstracts ou textes complets des publications referencees ; tout chiffre cite peut etre retrace via le PMID indique. Deuxiemement, plusieurs travaux de 2026 sont actuellement ',
      { i: 'in press' },
      ' et leurs volumes/pages restent provisoires. Troisiemement, l heterogeneite des methodes de quantification du ctDNA limite la comparabilite directe des seuils entre etudes : un seuil de 2.5 log hGE/mL en CAPP-Seq ne saurait etre transpose tel quel en PhasED-Seq, dont la sensibilite analytique est superieure de plus de deux ordres de grandeur.'
    ]),
    H2('Plan du document'),
    para([
      'L exposition suit un cheminement allant du contexte clinique general (sections 1 a 2) aux methodologies analytiques (section 3), puis a la valeur pronostique du ctDNA dans ses dimensions baseline (section 4), dynamique (section 5) et post-CAR-T (section 6). La section 7 confronte le ctDNA a l imagerie metabolique de reference, tandis que la section 8 detaille la methodologie statistique des modeles a classes latentes joints qui constitue l originalite analytique d ALYCANTE. Les sections 11 a 13 abordent les developpements therapeutiques recents (bispecifiques CD20xCD3, complications immunologiques) et la synthese quantitative meta-analytique. Les sections 14 et 15 traitent respectivement du comparatif entre les trois produits CAR-T et de la specificite du lymphome primaire du SNC. La section 16, conclusive, synthese les implications du projet ALYCANTE et discute les perspectives ouvertes par ses resultats.'
    ]),
    new Paragraph({ children: [new PageBreak()] })
  ];
}

// ============ SECTION 1 ============
function buildSection1() {
  return [
    H1('1. Contexte clinique : DLBCL et positionnement de l etude ALYCANTE'),
    H2('1.1. Une maladie heterogene encore imparfaitement stratifiee'),
    para([
      'Premier lymphome non hodgkinien en frequence, le DLBCL est curable dans environ 60 % des cas par R-CHOP, mais reste responsable d une rechute precoce ou d une refractarite chez 20 a 50 % des patients ',
      { cite: [14, 47, 77] },
      '. Cette dispersion des trajectoires cliniques traduit une heterogeneite biologique profonde, que les indices pronostiques cliniques classiques (IPI, R-IPI, NCCN-IPI) ne capturent que partiellement. L emergence des classifications moleculaires - cellule d origine (GCB versus non-GCB) puis sous-groupes genomiques LymphGen (EZB, BN2, MCD, N1, ST2) - a affine la comprehension de la biologie tumorale, sans pour autant guider de maniere reproductible l individualisation des strategies therapeutiques en routine ',
      { cite: [68] },
      '.'
    ], { first: true }),
    para([
      'Cette limite de la stratification clinico-biologique baseline a conduit au developpement de marqueurs dynamiques. Les parametres tumoraux volumetriques mesures par 18F-FDG-PET (TMTV, TLG, IMPI) ont apporte une dimension quantitative au-dela des criteres de Lugano ',
      { cite: [1, 32, 35, 50] },
      ', tandis que le ctDNA - objet central de cette revue - integre simultanement information sur la masse tumorale, genotype, et dynamique de reponse. C est dans ce paysage en mutation rapide que se positionne l etude ALYCANTE.'
    ]),
    H2('1.2. Place des CAR-T cells dans le DLBCL R/R'),
    para([
      'L approbation reglementaire des trois CAR-T anti-CD19 - axicabtagene ciloleucel (axi-cel), tisagenlecleucel (tisa-cel) et lisocabtagene maraleucel (liso-cel) - a profondement modifie l histoire naturelle du DLBCL R/R ',
      { cite: [19, 31, 113, 118] },
      '. La section 14 et le Tableau 2 detaillent leurs caracteristiques comparees ; on retiendra ici que les trois produits different non seulement par leur domaine de costimulation (CD28 pour axi-cel, 4-1BB pour les deux autres), mais aussi par leur profil de tolerance, leur procede de fabrication et leur cible d AMM.'
    ], { first: true }),
    para([
      'Au-dela de la troisieme ligne, deux essais randomises ont valide en 2021-2022 l utilisation des CAR-T en deuxieme ligne. ZUMA-7 a demontre la superiorite de l axi-cel sur le standard de soins (chimiotherapie de rattrapage suivie d ASCT) avec une mediane d EFS portee de 2.0 a 8.3 mois (HR 0.40 ; IC95 0.31-0.51 ; p < 0.001) et une survie globale a quatre ans de 54.6 % contre 46 % (HR 0.73 ; p = 0.03) ',
      { cite: [18, 43] },
      '. TRANSFORM a confirme un benefice analogue pour le liso-cel, avec un argument biologique supplementaire : la profondeur et la duree de la reponse moleculaire mesurees par ctDNA-MRD etaient significativement superieures dans le bras CAR-T par rapport au bras ASCT ',
      { cite: [90] },
      ', ce qui constitue un argument fort en faveur de l interet du ctDNA comme critere de substitution.'
    ]),
    H2('1.3. L originalite de l etude ALYCANTE'),
    para([
      'L etude ALYCANTE (NCT04531046) repond a une question laissee ouverte par ZUMA-7 et TRANSFORM, qui n incluaient que des patients eligibles a l autogreffe. Or, dans la pratique reelle, pres de la moitie des patients DLBCL R/R en seconde ligne ne le sont pas, soit en raison de comorbidites, soit en raison de l age. ALYCANTE, etude de phase 2 multicentrique francaise, evalue specifiquement l axi-cel dans cette population fragile : sur 62 patients inclus, le taux de reponse metabolique complete (CMR) a trois mois - critere principal - atteint 71 % (IC95 58-82 %), avec une PFS mediane de 11.8 mois et un profil de toxicite comparable a celui des essais pivots (CRS de grade superieur ou egal a 3 chez 8.1 %, neurotoxicite de grade superieur ou egal a 3 chez 14.5 %) ',
      { cite: [45] },
      '. Les donnees de qualite de vie publiees ulterieurement ',
      { cite: [86] },
      ' montrent meme une recuperation a trois mois superieure a celle observee dans ZUMA-7, suggerant que la population eligible a ALYCANTE n est pas plus penalisee que les patients plus fits dans le contexte d un CAR-T 2L.'
    ], { first: true }),
    H2('1.4. La question biomarqueur que pose ALYCANTE'),
    para([
      'La reussite clinique d ALYCANTE pose immediatement la question de l identification precoce des patients qui beneficieront durablement du traitement, et de ceux qui rechuteront. La CMR par PET a trois mois, bien que critere principal d evaluation, presente plusieurs limites : elle est tardive, son interpretation peut etre perturbee par l inflammation post-CAR-T residuelle, et sa specificite pour la maladie active reste imparfaite. Le suivi longitudinal du ctDNA (',
      { b: '421 mesures sur 57 patients' },
      ', des prelevements de leucapherese jusqu a vingt-quatre mois post-infusion) offre une alternative et un complement attractifs.'
    ], { first: true }),
    para([
      'Le projet biomarqueur ALYCANTE se distingue par plusieurs choix originaux. Premierement, il evalue la valeur pronostique du ctDNA en termes de delta ratio (log10[quota(Tx)/quota(BL)]) plutot que de quantite absolue, ce qui standardise les comparaisons entre patients aux burdens initiaux differents. Deuxiemement, il applique un ',
      { b: 'modele a classes latentes joint (JLCM)' },
      ' - approche emergente decrite en detail en section 8 - pour identifier des sous-classes de trajectoires ctDNA correlees au risque d evenement. Troisiemement, il confronte directement la classification JLCM tronquee a J14 avec la CMR PET M3, dans le but de demontrer une superiorite predictive du marqueur moleculaire precoce sur l imagerie tardive.'
    ]),
    H2('1.5. Schema synoptique du protocole'),
    para([
      'La Figure 5 schematise le deroulement temporel du protocole et la position des biomarqueurs : leucapherese pre-traitement (J-30 a J-5), lymphodepletion par fludarabine-cyclophosphamide, reinfusion d axi-cel a J0, mesures ctDNA aux temps J14, M1, M3, M6, M9 et M12, et evaluations PET aux memes timepoints. Le critere principal CMR M3 est mis en exergue. Cette representation permet de visualiser le decalage temporel entre les mesures moleculaires precoces (J14 a M1) et l evaluation clinique du critere principal (M3), justifiant l interet pronostique potentiel des marqueurs precoces.'
    ], { first: true }),
    ...figureBlock('fig5_protocole_ALYCANTE.png',
      'Figure 5. Schema synoptique du protocole ALYCANTE. Timeline des visites cles et insertion des mesures longitudinales ctDNA (n = 421 observations / 57 patients) integrees au modele JLCM. La CMR M3, critere principal de l essai, est mise en evidence.', 560)
  ];
}

// ============ SECTION 2 ============
function buildSection2() {
  return [
    H1('2. Le ctDNA dans les lymphomes B agressifs : principes generaux'),
    H2('2.1. Definition et biologie de la cellule a la circulation'),
    para([
      'L ADN tumoral circulant (',
      { i: 'circulating tumor DNA' },
      ', ctDNA) designe la fraction d ADN extracellulaire derivant des cellules tumorales et liberee dans le plasma sanguin, principalement par apoptose. Les fragments mesurent typiquement entre 140 et 170 paires de bases, taille caracteristique des nucleosomes, et constituent un sous-ensemble d un pool plus large d ADN libre circulant (cfDNA) dont la majorite provient des leucocytes normaux. Cette dilution du signal tumoral dans un bruit de fond important pose le defi analytique central : la detection du ctDNA exige des methodes capables d identifier de tres faibles fractions tumorales, jusqu a une partie par million dans les approches les plus sensibles ',
      { cite: [4, 7, 27, 67, 111] },
      '. La revue methodologique de Fu et coll. (2025) ',
      { cite: [111] },
      ' propose une synthese actualisee des plateformes disponibles.'
    ], { first: true }),
    para([
      'Dans le DLBCL specifiquement, deux approches dominent. La premiere repose sur la detection et la quantification des rearrangements V(D)J du recepteur d immunoglobuline (IgH, IgK, IgL), uniques pour chaque clone tumoral et stables au cours de l evolution ; elle necessite l identification prealable du clonotype dominant sur un echantillon tissulaire au diagnostic. La seconde repose sur le suivi simultane de multiples mutations somatiques par sequencage cible profond, et a l avantage majeur de ne pas requerir de biopsie informative prealable. La quantite de ctDNA est habituellement exprimee en ',
      { b: 'hGE/mL' },
      ' (',
      { i: 'haploid genome equivalents per milliliter' },
      ') ou, plus frequemment en pratique, en log10 de cette grandeur, transformation qui linearise les distributions tres asymetriques observees dans les populations de patients. Avec les methodes contemporaines, le ctDNA est detectable chez 90 a 98 % des patients DLBCL au diagnostic ',
      { cite: [5, 21, 50, 62, 65] },
      '.'
    ]),
    H2('2.2. Une panoplie d utilites cliniques, encore inegalement validees'),
    para([
      'L interet clinique du ctDNA dans le DLBCL se decline en cinq utilites complementaires, dont la maturite varie considerablement. Le ',
      { b: 'genotypage non invasif' },
      ' permet d identifier des mutations somatiques recurrentes (TP53, KMT2D, CARD11, MYD88, B2M, EZH2) et de classer les tumeurs selon la cellule d origine ou les sous-groupes LymphGen directement sur plasma, avec une concordance superieure a 95 % par rapport aux biopsies tissulaires ',
      { cite: [3, 29, 36, 68] },
      '. Cette dimension diagnostique transforme la prise en charge des situations ou la biopsie est inaccessible ou non informative.'
    ], { first: true }),
    para([
      'L ',
      { b: 'estimation de la masse tumorale' },
      ' constitue la deuxieme application validee : les niveaux baseline de ctDNA sont fortement correles aux marqueurs traditionnels (LDH, stade Ann Arbor, IPI) et plus particulierement au TMTV mesure par PET, avec des coefficients de Spearman compris entre 0.37 et 0.7 selon les etudes ',
      { cite: [21, 50, 52, 74] },
      '. Cette correlation offre une alternative non invasive et quantitative au TMTV, particulierement utile lorsque l acces a une plateforme de quantification metabolique automatisee fait defaut.'
    ]),
    para([
      'Les trois utilites suivantes relevent du suivi temporel et constituent le cœur de la presente revue. La ',
      { b: 'reponse moleculaire precoce' },
      ', formalisee par les seuils EMR/MMR de Kurtz et coll. ',
      { cite: [5] },
      ', identifie des le premier ou deuxieme cycle de chimiotherapie les patients dont la trajectoire pronostique est favorable. La ',
      { b: 'maladie residuelle measurable' },
      ' (MRD) en fin de traitement, dont la valeur pronostique surpasse celle de la reponse PET selon les donnees recentes ',
      { cite: [26, 71, 75, 90] },
      ', ouvre la voie a une redefinition de la remission. Enfin, la ',
      { b: 'surveillance post-remission' },
      ' permet de detecter une rechute moleculaire trois a six mois avant l apparition de la rechute clinique radiologique ',
      { cite: [2, 25, 67] },
      ', avec des implications majeures pour la mise en place precoce d une therapie de sauvetage.'
    ])
  ];
}

// ============ SECTION 3 ============
function buildSection3() {
  return [
    H1('3. Methodes de detection du ctDNA dans le DLBCL'),
    para([
      'Le choix de la methode de detection conditionne directement la sensibilite, la specificite et l utilite clinique du ctDNA. Le Tableau 1 (section 13) et la Figure 3 synthetisent les onze plateformes principales selon leur limite de detection, leur necessite ou non de biopsie tissulaire prealable, et leur degre de validation clinique. Trois familles meritent une description detaillee.'
    ], { first: true }),
    H2('3.1. IgH-NGS et sequencage clonotypique V(D)J'),
    para([
      'L approche pionniere developpee par Roschewski, Wilson et coll. au NIH ',
      { cite: [2, 4, 12] },
      ' repose sur l identification, sur tissu tumoral, du clonotype V(D)J dominant du recepteur d immunoglobuline. Ce clonotype, unique pour chaque tumeur, est ensuite quantifie serie apres serie dans le plasma par sequencage profond. La sensibilite analytique atteint environ une cellule tumorale par million de cellules normales (1 ppm) et la specificite tumorale est tres elevee, les rearrangements V(D)J etant intrinsequement absents des cellules non lymphoides B circulantes. La plateforme commerciale clonoSEQ (Adaptive Biotechnologies) est largement utilisee dans cette approche.'
    ], { first: true }),
    para([
      'La principale limite de cette methode reside dans son exigence d une biopsie tissulaire informative au diagnostic, ce qui peut etre problematique dans le contexte de tumeurs profondes, transformees ou de lymphomes a faible cellularite. L ajout du sequencage IgK aux IgH augmente sensiblement le taux de detection clonotypique, de 43 % a 58 % dans la cohorte de 33 patients de Wang et coll. (2025) ',
      { cite: [69] },
      ', ce qui suggere une optimisation possible de la sensibilite par multiplexage des rearrangements cibles.'
    ]),
    H2('3.2. CAPP-Seq, le standard tumor-naive'),
    para([
      'Developpee par les equipes de Diehn et Alizadeh a Stanford, la technologie ',
      { i: 'Cancer Personalized Profiling by Deep Sequencing' },
      ' (CAPP-Seq) ',
      { cite: [3, 5, 11, 21, 80] },
      ' utilise un panel cible de regions genomiques frequemment alterees dans le DLBCL (typiquement 250 a 500 kilobases), sequencees a haute profondeur avec utilisation de codes-barres moleculaires uniques (',
      { i: 'unique molecular identifiers' },
      ', UMI) qui permettent la correction des erreurs de sequencage. La limite de detection se situe entre 10 et 1 ppm selon l input d ADN et la profondeur atteinte.'
    ], { first: true }),
    para([
      'L avantage decisif du CAPP-Seq sur l IgH-NGS est son caractere ',
      { b: 'tumor-naive' },
      ' : aucune biopsie tissulaire prealable n est requise puisque le panel cible des mutations frequentes dans la population DLBCL. Cette propriete simplifie l implementation clinique et autorise l analyse retrospective de cohortes ou les biopsies tissulaires ne sont pas disponibles. CAPP-Seq permet en outre une caracterisation genotypique simultanee, ouvrant la voie a la classification LymphGen sur plasma, comme l ont demontre Moia et coll. (2025) qui rapportent une concordance de 96 % entre les classes assignees sur ctDNA et sur tissu (n = 77) ',
      { cite: [68] },
      '. Le panel CLEARS (Clinical Lymphoma Exploration And Research Sequencing, 521 genes) developpe par l equipe tcheque ',
      { cite: [81] },
      ' represente une declinaison europeenne contemporaine de cette approche.'
    ]),
    H2('3.3. PhasED-Seq, l ultra-sensibilite par les variants phases'),
    para([
      'Introduit en 2021 par Kurtz, Alizadeh et coll. ',
      { cite: [26] },
      ', le sequencage des variants phases (PhasED-Seq) exploite un principe biophysique elegant : lorsque deux mutations somatiques sont localisees sur le meme fragment d ADN (typiquement moins de 170 paires de bases), leur co-detection augmente exponentiellement la specificite du signal et reduit drastiquement le bruit de fond. La limite de detection rapportee atteint 0.7 ppm avec 95 % de detection a partir de 120 nanogrammes d ADN d entree, soit une amelioration de plus d un ordre de grandeur sur CAPP-Seq classique. Le taux de faux positifs analytique est de 0.24 % et le taux d erreur de fond de 1.95 × 10⁻⁸, valeurs validees prospectivement par Klimova et coll. (2025-2026) ',
      { cite: [71, 89] },
      '.'
    ], { first: true }),
    para([
      'L impact clinique de cette gain de sensibilite est demontre par les donnees originelles de Kurtz et coll. : parmi les patients consideres comme MRD-negatifs apres deux cycles de chimiotherapie selon CAPP-Seq, 25 % presentent encore du ctDNA detectable par PhasED-Seq, et leur pronostic est significativement plus defavorable ',
      { cite: [26] },
      '. Cette observation suggere que la sensibilite analytique limite directement la valeur pronostique du marqueur, et que les seuils de remission moleculaire definis avec des methodes moins sensibles sous-estiment systematiquement la maladie residuelle. PhasED-Seq a depuis ete utilise dans plusieurs etudes pivotales, incluant TRANSFORM ',
      { cite: [90] },
      ' et l analyse poolee LBCL de Roschewski et coll. (2025) ',
      { cite: [75] },
      ' qui sera detaillee en section 7.'
    ]),
    H2('3.4. Methodes complementaires et emergentes'),
    para([
      'Plusieurs autres approches occupent des niches specifiques. ',
      { b: 'Signatera' },
      ' (Natera) repose sur un panel multiplex PCR de seize mutations somatiques personnalisees, identifiees sur biopsie initiale ; commercialise pour plusieurs tumeurs solides, son application au DLBCL a ete validee par Narkhede et coll. (2024, n = 50) avec une clairance ctDNA apres un cycle predisant une amelioration spectaculaire de l EFS (HR 6.5) et un avancement de la detection de reponse complete de 97 jours par rapport a l imagerie ',
      { cite: [65] },
      '. La plateforme ',
      { b: 'EuroClonality-NDC' },
      ' constitue l effort de standardisation europeen, integree dans plusieurs etudes multicentriques ',
      { cite: [62] },
      '.'
    ], { first: true }),
    para([
      'A l autre extreme du spectre cout-sensibilite, le sequencage du genome entier a faible profondeur (',
      { b: 'ULP-WGS' },
      ', environ 0.1×) propose par Zhao et coll. (2025) ',
      { cite: [74] },
      ' permet l estimation de la fraction tumorale et la detection de pertes chromosomiques majeures (notamment del(17p)) a cout reduit, au prix d une sensibilite limitee a des fractions tumorales superieures a 3 %. La ',
      { b: 'PCR digitale (ddPCR) ' },
      ' sur une mutation unique offre une approche bon marche et rapide adaptee a la surveillance ciblee, mais ne permet pas de genotypage tumoral exhaustif. Enfin, des approches plus exploratoires - profilage epigenetique 5-hydroxymethylcytosines ',
      { cite: [13] },
      ', exosomes et vesicules extracellulaires ',
      { cite: [14] },
      ' - elargissent le champ des biomarqueurs accessibles depuis le compartiment plasmatique, mais leur validation clinique reste preliminaire.'
    ]),
    para([
      'Cette panoplie methodologique pose la question recurrente, dans la litterature comme dans les essais cliniques, de la ',
      { b: 'standardisation' },
      ' : un seuil de positivite defini par CAPP-Seq n est pas directement applicable a PhasED-Seq, et les comparaisons entre etudes sont compromises par cette heterogeneite. Le roadmap propose par Goldstein, Alizadeh et coll. (2026) ',
      { cite: [91] },
      ' pour la validation de la MRD comme critere de substitution dans les essais de phase precoce souligne explicitement ce defi.'
    ])
  ];
}

// ============ SECTION 4 ============
function buildSection4() {
  return [
    H1('4. Valeur pronostique du ctDNA baseline au diagnostic'),
    H2('4.1. Le ctDNA comme reflet quantitatif de la masse tumorale'),
    para([
      'Le premier role pronostique du ctDNA est celui d un indicateur quantitatif de la charge tumorale globale, complementaire des marqueurs cliniques traditionnels. Les niveaux de ctDNA pre-traitement sont fortement correles aux LDH seriques, au stade Ann Arbor, a l IPI et surtout au TMTV mesure par 18F-FDG-PET. Dans la cohorte multicentrique de 267 patients d Alig, Kurtz et coll. (2021) ',
      { cite: [21] },
      ', les niveaux de ctDNA correlent significativement avec ces trois marqueurs (p < 0.001 pour chacun), et le coefficient de Spearman avec le TMTV atteint 0.37. Surtout, le ctDNA baseline reste un predicteur independant de l EFS apres ajustement multivarie sur l IPI et l intervalle diagnostic-traitement (DTI), avec un hazard ratio de 1.5 par log d augmentation (IC95 1.2-2.0).'
    ], { first: true }),
    para([
      'Cette association ctDNA-burden a une implication conceptuelle importante : le ctDNA capture non seulement la masse tumorale visible (TMTV) mais aussi probablement la dynamique de renouvellement cellulaire tumoral, ce qui pourrait expliquer pourquoi il apporte une information independante de l imagerie. Cette dimension ',
      { b: 'biologique active' },
      ' du ctDNA, par opposition a la mesure statique du volume metabolique, motive son interet pour la prediction d evolution.'
    ]),
    H2('4.2. Seuils pronostiques en immunochimiotherapie frontline'),
    para([
      'La definition d un seuil ctDNA permettant de stratifier les patients en groupes de risque distincts est un objectif methodologique majeur, mais les valeurs proposees varient selon les methodes et les cohortes. Kurtz et coll. (2018), dans leur etude princeps de 217 patients ',
      { cite: [5] },
      ', proposent un seuil de 2.5 log10 hGE/mL en CAPP-Seq, au-dela duquel l EFS et l OS sont significativement reduits. Le Goff, Blanc-Durand et coll. (2023) dans une cohorte real-world de 112 patients evalues par un panel de 40 genes ',
      { cite: [50] },
      ' identifient un seuil legerement different (3.57 log hGE/mL) au-dela duquel la PFS a un an chute de 83 % a 44 %. Plus recemment, Moia et coll. (2025) ',
      { cite: [68] },
      ' ont propose une approche integrant le seuil ctDNA (2.5 log) avec la classification moleculaire LymphGen : les patients du sous-groupe ST2/BN2 avec ctDNA faible ont un pronostic excellent (PFS 4 ans 87.5 %, OS 100 %), tandis que les autres clusters avec ctDNA eleve ont une PFS 4 ans de 38 %. Cette integration ctDNA + sous-type moleculaire ameliore le C-index pronostique de 0.59 a 0.63 pour la PFS et de 0.63 a 0.68 pour l OS.'
    ], { first: true }),
    para([
      'La disparite des seuils entre etudes (2.5 vs 3.57 log) refleterait moins une divergence biologique fondamentale qu une difference de sensibilite et de normalisation entre methodes analytiques. Cette observation renforce la necessite d une harmonisation des protocoles pre-analytiques (volume plasma, methode d extraction, controles internes) et de la calibration des plateformes, comme le souligne le travail de Klimova et coll. (2026) ',
      { cite: [89] },
      ' sur la robustesse analytique du PhasED-Seq face aux principales sources de variabilite.'
    ]),
    H2('4.3. Du genotype au pronostic : LymphGen sur plasma'),
    para([
      'Au-dela de la simple quantification, le ctDNA permet la determination du genotype tumoral. La concordance entre classification LymphGen realisee sur ctDNA et sur biopsie tissulaire depasse 95 % dans les etudes recentes ',
      { cite: [3, 36, 68] },
      ', ce qui valide l utilisation du plasma comme source primaire d information moleculaire. Les mutations recurrentes detectees au baseline (TP53, B2M, KMT2D, MYD88, CARD11) ont chacune leur signification pronostique propre. Zhang et coll. (2021) ',
      { cite: [29] },
      ' rapportent ainsi que la mutation TP53 ou B2M pre-traitement chez 38 patients DLBCL haut risque est associee a un pronostic significativement plus defavorable, observation confirmee dans plusieurs cohortes chinoises de plus grande taille ',
      { cite: [36] },
      '.'
    ], { first: true }),
    para([
      'Cette capacite a integrer simultanement quantite et qualite moleculaire fait du ctDNA un biomarqueur particulierement riche, dont la valeur pronostique combinee surpasse celle de chaque dimension prise isolement. L application directe au contexte CAR-T (section 6) demande toutefois quelques nuances : les patients arrivant en deuxieme ou troisieme ligne ont des paysages mutationnels remodeles par les chimiotherapies anterieures, et certaines mutations (comme TP53) acquierent une signification pronostique encore plus marquee dans ces situations refractaires.'
    ])
  ];
}

// ============ SECTION 5 ============
function buildSection5() {
  return [
    H1('5. Dynamique precoce du ctDNA et reponse moleculaire'),
    H2('5.1. Les seuils EMR et MMR : une convention devenue standard'),
    para([
      'L observation fondatrice de l interet pronostique de la cinetique ctDNA precoce remonte aux travaux de Kurtz, Scherer et coll. (2018) ',
      { cite: [5] },
      ', qui ont analyse les dynamiques de 217 patients DLBCL traites dans six centres internationaux. Sur la base d une cohorte de decouverte, deux seuils ont ete definis et valides dans deux cohortes independantes : la ',
      { b: 'reponse moleculaire precoce (EMR)' },
      ', definie par une diminution d au moins 2 log10 du ctDNA apres un cycle de chimiotherapie ; et la ',
      { b: 'reponse moleculaire majeure (MMR)' },
      ', definie par une diminution d au moins 2.5 log10 apres deux cycles. Les patients atteignant l EMR avaient une EFS a 24 mois de 83 % contre 50 % chez les non-EMR (p = 0.0015) ; le seuil MMR offrait une discrimination encore plus marquee (82 % vs 46 % ; p < 0.001).'
    ], { first: true }),
    para([
      'L originalite de ce travail tient au fait que ces deux seuils restent predictifs apres ajustement multivarie sur l IPI ',
      { b: 'et' },
      ' la reponse PET interim, deux marqueurs eux-memes solidement etablis. Cette independance suggere que la cinetique moleculaire precoce capture une dimension de la reponse tumorale qui n est ni le burden initial, ni la reponse metabolique imagee. Les replications dans d autres cohortes ',
      { cite: [11, 36, 38, 62, 65] },
      ' ont robustement valide ces seuils, faisant aujourd hui des concepts EMR/MMR un standard implicite dans la litterature DLBCL.'
    ]),
    H2('5.2. Combinaison ctDNA et PET interim : une stratification a trois niveaux'),
    para([
      'L etude d Alcoceba et coll. (2024, n = 68 patients DLBCL R-CHOP) ',
      { cite: [62] },
      ' a directement compare et combine la MMR ctDNA (mesuree par EuroClonality-NDC) et la reduction du SUVmax au PET interim apres deux cycles. Chaque marqueur, pris isolement, discrimine significativement le risque de progression : la MMR seule classifie les patients en deux groupes avec une PFS a deux ans de 76 % contre 0 % (p < 0.001) ; la reduction du SUVmax superieure a 66 % donne une PFS a deux ans de 83 % contre 38 % (p < 0.001). La combinaison des deux marqueurs identifie trois strates de pronostic tres distinct (PFS 2 ans de 84 %, 17 % et 0 % selon le nombre de criteres atteints ; p < 0.001).'
    ], { first: true }),
    para([
      'Ces resultats suggerent que ctDNA et PET ne sont pas substituables mais complementaires : ils capturent des dimensions partiellement orthogonales de la reponse tumorale, et leur integration ameliore la stratification au-dela de ce que chaque marqueur permet seul. Cette logique de complementarite ouvre la voie aux approches dites de ',
      { b: 'multimodal monitoring' },
      ' qui constituent l avenir probable de la stratification post-traitement.'
    ]),
    H2('5.3. CIRI : vers une prediction dynamique individualisee'),
    para([
      'Le concept ultime de la stratification dynamique a ete formalise par Kurtz, Esfahani et coll. dans leur publication phare de Cell (2019) ',
      { cite: [11] },
      ' : le ',
      { b: 'Continuous Individualized Risk Index (CIRI)' },
      ' integre l ensemble des informations disponibles a chaque temps clinique (IPI baseline, ctDNA initial, EMR/MMR, reponse PET interim) pour produire, pour chaque patient, une probabilite evolutive de PFS recalculee dynamiquement. L analogie avec les modeles de "win probability" en sport est explicite : la prediction n est pas figee au baseline mais s ajuste au cours du suivi.'
    ], { first: true }),
    para([
      'Le CIRI apporte une amelioration de prediction substantielle par rapport aux modeles statiques bases sur le seul IPI. Son inconvenient principal est sa nature combinatoire discrete : il opere par seuils successifs plutot que par modelisation continue d une trajectoire moleculaire. C est precisement ce point qui justifie le choix methodologique d ALYCANTE en faveur d une approche par modeles a classes latentes joints (JLCM, section 8) : plutot que de combiner des seuils discrets, le JLCM modelise la forme entiere de la trajectoire ctDNA et l associe directement au risque d evenement, capturant ainsi des configurations cinetiques qui echapperaient a des classifications binaires successives.'
    ])
  ];
}

// ============ SECTION 6 ============
function buildSection6() {
  return [
    H1('6. Le ctDNA dans le contexte CAR-T : un biomarqueur essentiel'),
    H2('6.1. Charge tumorale moleculaire pre-CAR-T : pronostic et toxicite'),
    para([
      'L un des constats les plus solides emerges de la litterature post-CAR-T est que la charge tumorale pre-infusion - qu elle soit mesuree par TMTV, par ctDNA ou par des indices combines - conditionne a la fois l efficacite et la toxicite du traitement. Frank, Hossain et coll. (2021), dans la premiere etude prospective multicentrique dediee a ce sujet (n = 72) ',
      { cite: [25] },
      ', ont montre que les patients avec un ctDNA baseline eleve avaient un risque accru de progression apres axi-cel, mais aussi un risque accru de developper un syndrome de relargage cytokinique (CRS) ou une neurotoxicite immunologique (ICANS) severes. Cette double association a un sens biologique simple : une plus grande quantite de cellules tumorales presente plus d antigene cible, ce qui amplifie a la fois l efficacite et la reponse inflammatoire associee.'
    ], { first: true }),
    para([
      'L analyse exploratoire de ZUMA-7 publiee par Locke et coll. (2024) ',
      { cite: [59] },
      ' confirme ces observations sur une base plus large : un TMTV baseline eleve est associe a un EFS inferieur (notamment dans le bras standard) et a un risque accru de CRS et d ICANS de grade 3 ou plus. L equipe chinoise de Zhou (2023, n = 48 patients R/R DLBCL) ',
      { cite: [53] },
      ' rapporte un effet dose particulierement marque pour le nombre de mutations detectables sur ctDNA pre-traitement : au-dela de dix mutations, l OS a un an chute a 0 % contre 73.8 % chez les patients avec dix mutations ou moins. Ces resultats convergent vers une conclusion clinique importante : la "debulking therapy" ou therapie de pont avant CAR-T pourrait beneficier preferentiellement aux patients identifies comme a haut risque sur des criteres moleculaires baseline.'
    ]),
    H2('6.2. La cinetique ctDNA precoce post-infusion : un signal puissant'),
    para([
      'L etude pivot de Frank et coll. (2021) ',
      { cite: [25] },
      ' a etabli des references pronostiques cruciales pour le suivi post-CAR-T. Les chiffres rapportes sont particulierement frappants : 70 % des patients en reponse durable a un an avaient un ctDNA indetectable des le septieme jour post-infusion (J7), contre seulement 13 % des patients qui ont finalement progresse (p < 0.0001). Au temps J28, soit un mois apres l infusion, la dichotomie devient encore plus saillante : la PFS mediane n est pas atteinte chez les patients ctDNA-negatifs contre seulement trois mois chez les patients ctDNA-positifs (p < 0.0001), et l OS a deux ans est respectivement non atteinte contre dix-neuf mois (p = 0.0080).'
    ], { first: true }),
    para([
      'L observation la plus marquante concerne les patients dont l imagerie PET a J28 donne un message discordant - reponse partielle ou maladie stable - et chez lesquels le ctDNA permet la decision pronostique. Dans ce sous-groupe, seulement un patient sur dix (10 %) avec un ctDNA simultanement indetectable a finalement rechute, contre quinze patients sur dix-sept (88 %) avec un ctDNA detectable (p = 0.0001). Autrement dit, ',
      { b: 'le ctDNA precoce reclasse correctement les patients dont le PET genere de l incertitude' },
      ', situation clinique frequente liee a l inflammation post-CAR-T residuelle non specifique. Pour completer cette demonstration, le ctDNA detecte la rechute moleculaire avant la rechute radiologique dans 94 % des cas (29 patients sur 30), avec un decalage temporel median de plusieurs semaines a plusieurs mois.'
    ]),
    H2('6.3. Confirmation en deuxieme ligne : l etude TRANSFORM'),
    para([
      'Ces observations issues de la population traitee en troisieme ligne ou au-dela ont ete confirmees en deuxieme ligne par l analyse correlative ctDNA de TRANSFORM (Stepan, Ansari et coll., 2026, n = 136) ',
      { cite: [90] },
      '. Aux trois temps predefinis (J43, J64 et J126 post-randomisation), la clairance ctDNA-MRD predisait significativement l EFS dans les deux bras (liso-cel et ASCT). Le bras liso-cel obtenait plus frequemment un statut MRD-negatif que le bras ASCT, et la MRD-negativite etait correlee a une EFS et une PFS prolongees ainsi qu a une plus grande duree de reponse parmi les repondeurs complets. Surtout, l analyse multivariee montre que la MRD reste associee a l EFS apres ajustement pour la reponse PET, et une interaction significative est detectee entre le statut PET et le bras de traitement, suggerant que la valeur predictive du PET differe selon que le patient ait recu un CAR-T ou une ASCT.'
    ], { first: true }),
    para([
      'Cette derniere observation est importante pour la pratique clinique : elle suggere que les seuils et les significations attribues a la reponse PET ne sont pas necessairement transposables d un contexte therapeutique a l autre, et qu une evaluation moleculaire concomitante pourrait offrir une grille de lecture plus stable. Cette idee est en parfait accord avec la philosophie d ALYCANTE.'
    ]),
    H2('6.4. Implications pour la prise en charge post-CAR-T'),
    para([
      'L ensemble de ces donnees converge vers un parcours clinique structure ou le ctDNA serait integre a plusieurs etapes successives. Au baseline, il permettrait de stratifier conjointement le risque toxicite et efficacite, et d orienter la therapie de pont chez les patients identifies comme a haut burden moleculaire. Tres precocement apres l infusion (entre J7 et J28), il permettrait d identifier les patients dont la reponse moleculaire est sous-optimale et d envisager des escalades therapeutiques precoces, sans attendre la confirmation imagerie tardive. Enfin, regulierement apres la reponse PET, le ctDNA permettrait la detection precoce des rechutes moleculaires avant leur manifestation clinique ou radiologique. La principale barriere a cette integration reste, en 2026, l acces aux plateformes ultra-sensibles - PhasED-Seq notamment - encore confinees a quelques centres specialises en Europe. C est precisement cette question methodologique que le projet ALYCANTE-biomarqueurs aborde, en demontrant la faisabilite d un suivi pertinent meme avec des plateformes moins ultra-sensibles, grace a une exploitation statistique optimale (modeles a classes latentes) des donnees longitudinales disponibles.'
    ], { first: true })
  ];
}

// ============ SECTION 7 ============
function buildSection7() {
  return [
    H1('7. ctDNA versus imagerie metabolique PET : complementarites et concurrences'),
    H2('7.1. La classification de Lugano : la reference contemporaine'),
    para([
      'Les criteres de Lugano, formalises par Cheson et coll. en 2014 ',
      { cite: [1] },
      ', constituent la reference internationale pour le staging et l evaluation de la reponse des lymphomes FDG-avides, incluant le DLBCL. Ils integrent l echelle visuelle de Deauville en cinq points : DS 1 et 2 correspondent a une absence d hypermetabolisme superieur au pool sanguin mediastinal, DS 3 a un hypermetabolisme superieur au pool mediastinal mais inferieur au foie, DS 4 et 5 a un hypermetabolisme superieur au foie. La reponse metabolique complete (CMR) est definie par un score DS inferieur ou egal a 3. Une etude de comparaison directe avec les criteres PERCIST realisee par Nielsen et coll. (2023) ',
      { cite: [49] },
      ' a montre une concordance de 98.4 % entre les deux approches au temps interim et de 86 % en fin de traitement, suggerant que le choix entre Lugano et PERCIST a peu d impact pratique.'
    ], { first: true }),
    H2('7.2. Les limites du PET interim : un message pronostique discordant'),
    para([
      'Malgre son statut de reference, le PET interim apres deux cycles (iPET2) presente des limites pronostiques bien documentees. Wight et coll. (2021), dans une cohorte de 200 patients DLBCL traites par R-CHOP ',
      { cite: [32] },
      ', montrent que seul le DS 5 (chez 19.5 % des patients) predit fortement l echec therapeutique (HR 6.29 ; IC95 3.01-13.17), tandis que le DS 4 - frequemment rapporte comme positif - est en realite equivalent en pronostic aux DS 1-3. Cette dichotomie inattendue limite la valeur clinique pratique du seuil de positivite PET interim, et a conduit a explorer des alternatives plus discriminantes comme l iFLT-PET (imagerie de la proliferation a la 18F-fluorothymidine) qui s avere superieur a l iFDG-PET dans la prediction de PFS dans la meme cohorte (Minamimoto 2021, ',
      { cite: [22] },
      ').'
    ], { first: true }),
    para([
      'Dans le contexte post-CAR-T, les limites du PET sont encore plus marquees. L inflammation residuelle post-infusion peut persister plusieurs semaines, generant des hypermetabolismes non specifiques qui rendent l interpretation a un mois (M1) particulierement delicate. Kitajima et coll. (2024) ',
      { cite: [60] },
      ' ont confirme la valeur de la CMR a M1 comme predicteur de PFS et OS apres CAR-T, mais au prix d une dispersion non negligeable des reponses : sur 53 patients evaluables, 32 etaient en CMR a M1 et 21 en non-CMR, avec des trajectoires ulterieures contrastees.'
    ]),
    H2('7.3. Le ctDNA-MRD en fin de traitement : une superiorite pronostique demontree'),
    para([
      'L etude la plus aboutie demontrant la superiorite pronostique du ctDNA sur le PET en fin de traitement est l analyse poolee de Roschewski, Kurtz, Westin et coll. (J Clin Oncol 2025) ',
      { cite: [75] },
      '. En agregeant les donnees de cinq etudes prospectives portant sur 137 patients LBCL traites en frontline par chimiotherapie a base d anthracyclines, suivis par 409 prelevements plasmatiques par PhasED-Seq, les auteurs comparent directement la valeur predictive de la MRD ctDNA en fin de traitement (EoT) avec celle du PET aux memes timepoints. Les resultats sont saisissants : la PFS a deux ans est de 29 % chez les patients ctDNA-detectable EoT contre 97 % chez les patients ctDNA-indetectable (HR 28.7 ; p < 0.0001), tandis que le PET positif a un HR de seulement 3.6. Quatre-vingt-quatorze pour cent des patients ctDNA-negatifs en fin de traitement restent en remission durable.'
    ], { first: true }),
    para([
      'Cet ecart d ordre de grandeur entre les HR (28.7 contre 3.6) ne disqualifie pas le PET, qui conserve sa valeur de marqueur anatomique permettant de localiser la maladie residuelle et de guider d eventuelles biopsies ciblees. Il suggere neanmoins fortement que la definition meme de la remission devrait integrer le ctDNA-MRD pour les patients eligibles : la specificite tumorale du marqueur moleculaire - variants somatiques presents exclusivement dans les cellules tumorales - elimine le bruit inflammatoire qui parasite l interpretation du PET. La Figure 4 rassemble ces resultats avec ceux d autres etudes recentes confrontant ctDNA et PET dans des contextes therapeutiques varies, et toutes convergent vers la meme conclusion : le ctDNA discrimine systematiquement mieux que le PET, avec un effet particulierement marque dans le contexte post-CAR-T (HR 14.0 pour le ctDNA J28 dans l etude de Frank, contre 4.5 pour le PET dans la meme cohorte).'
    ]),
    H2('7.4. Vers une redefinition de la remission ?'),
    para([
      'Cette superiorite analytique du ctDNA-MRD a des implications regulatoires majeures. Le ',
      { i: 'roadmap' },
      ' de Goldstein, Wang, Chamuleau et Alizadeh (2026) ',
      { cite: [91] },
      ' propose deux nouveaux criteres de jugement pour les essais cliniques dans le lymphome : la ',
      { b: 'PFS modifiee' },
      ' (mPFS), incluant la MRD-positivite a la fin du traitement comme equivalent d evenement, et le ',
      { b: 'taux d uMRD' },
      ' a un timepoint predefini comme mesure de la profondeur de reponse. Ces criteres permettraient d accelerer le developpement clinique de nouveaux traitements en raccourcissant les durees d essais et en augmentant leur sensibilite a la detection d efficacite. Leur adoption suppose toutefois une harmonisation methodologique encore inaboutie.'
    ], { first: true })
  ];
}

// ============ SECTION 8 ============
function buildSection8() {
  return [
    H1('8. Methodes statistiques : modeles a classes latentes joints (JLCM/LCMM)'),
    H2('8.1. Pourquoi sortir des modeles de Cox classiques ?'),
    para([
      'L analyse de biomarqueurs longitudinaux en oncologie pose plusieurs defis statistiques qui depassent le cadre des modeles de survie de Cox a covariables fixes. L heterogeneite inter-individuelle des trajectoires est rarement bien capturee par une seule courbe moyenne ; la dependance entre l evolution du biomarqueur et la survenue de l evenement clinique - un patient en progression genere mecaniquement une trajectoire ctDNA croissante avant deces ou rechute - viole l hypothese d independance des observations longitudinales ; les mesures repetees sont souvent non equilibrees, certains patients ayant plus de timepoints que d autres ; et l interet clinique se porte souvent sur l identification de sous-phenotypes plutot que sur des effets de population moyens.'
    ], { first: true }),
    para([
      'Les modeles a classes latentes mixtes (',
      { i: 'Latent Class Mixed Models' },
      ', LCMM) repondent specifiquement a ces defis en postulant l existence de plusieurs sous-populations non observees, chacune caracterisee par sa propre trajectoire moyenne (effets fixes specifiques de classe) et sa propre variabilite individuelle (effets aleatoires). Combines avec un sous-modele de survie specifique de classe et un modele multinomial d appartenance, ils forment les ',
      { i: 'Joint Latent Class Mixed Models' },
      ' (JLCM), qui permettent une modelisation simultanee et coherente des deux dimensions temporelles ',
      { cite: [55, 57, 78] },
      '.'
    ]),
    H2('8.2. Architecture du JLCM'),
    para([
      'Un JLCM comporte trois composantes interdependantes. Le ',
      { b: 'sous-modele longitudinal' },
      ' est un modele lineaire mixte qui decrit l evolution du biomarqueur conditionnellement a l appartenance a une classe latente, autorisant des pentes individuelles autour de la pente moyenne de classe (effets aleatoires sur l intercept et la pente, structure typiquement notee ',
      { i: 'random = ~time' },
      ' dans le package R ',
      { i: 'lcmm' },
      '). Le ',
      { b: 'sous-modele de survie' },
      ' est un modele de Cox proportionnel specifique de chaque classe, qui modelise la fonction de risque d evenement conditionnellement a la classe. Le ',
      { b: 'modele d appartenance aux classes' },
      ' est une regression multinomiale qui peut integrer des covariables baseline (age, IPI, stade) pour predire la probabilite d appartenance a chaque classe.'
    ], { first: true }),
    para([
      'L estimation des parametres se fait par maximum de vraisemblance via un algorithme de Newton-Raphson modifie, robuste aux optima locaux. Le choix du nombre de classes (parametre ng) repose sur des criteres bayesiens (BIC) combines avec des considerations de pertinence clinique. Le tutoriel methodologique recent de Kyheng, Babykina et Duhamel (2025) ',
      { cite: [78] },
      ' fournit un guide pratique d implementation pour cliniciens et statisticiens appliques, base sur des jeux de donnees reels. Le travail de Proust-Lima, Saulnier et coll. (2023) ',
      { cite: [55] },
      ' etend ce cadre aux marqueurs longitudinaux multivaries (',
      { i: 'mpjlcmm' },
      '), permettant la modelisation simultanee de plusieurs biomarqueurs sur un meme axe temporel.'
    ]),
    H2('8.3. Applications oncologiques publiees'),
    para([
      'Plusieurs travaux ont demontre la valeur ajoutee des approches a classes latentes en oncologie clinique. En cancer colorectal, Li et coll. (2021) ont analyse les trajectoires peri-operatoires de trois marqueurs (CEA, CA19-9, CA125) chez 3539 patients ',
      { cite: [28] },
      '. Le modele a classes latentes generalise (LCGMM) identifie trois trajectoires distinctes pour chaque marqueur (low-stable, early-rising, later-rising), et la combinaison des appartenances aux classes donne six groupes pronostiques avec des hazard ratios de mortalite allant de 1.59 a 12.40, captant une heterogeneite pronostique invisible aux seuils baseline statiques. Une approche similaire appliquee a l alpha-fetoprotein dans le carcinome hepatocellulaire post-chimioembolisation (Lu et coll. 2022, n = 881) ',
      { cite: [82] },
      ' identifie trois classes (high-rising, low-stable, sharp-falling) avec un hazard ratio ajuste de mortalite de 5.13 pour la classe rising par rapport a stable.'
    ], { first: true }),
    para([
      'L equipe bordelaise de Proust-Lima, qui a developpe le package ',
      { i: 'lcmm' },
      ', a applique ces methodes a des problemes neuro-oncologiques complexes (atrophie multi-systemes, n = 598 ',
      { cite: [55] },
      ') identifiant cinq sous-phenotypes distincts par leur trajectoire et leur risque de deces. Sur le versant exposition-maladie, Leveque et coll. (2020) ',
      { cite: [16] },
      ' ont utilise le LCMM pour stratifier les trajectoires d exposition au tabac et a l amiante chez 4636 sujets de l etude cas-temoins ICARE, identifiant des classes de risque differenciees pour le cancer du poumon. Cette diversite d applications - du suivi clinique au screening etiologique - illustre la robustesse et la flexibilite du cadre.'
    ]),
    H2('8.4. Choix entre Joint Model classique et JLCM'),
    para([
      'Le ',
      { b: 'joint model (JM)' },
      ' classique, formalise par Rizopoulos et coll. ',
      { cite: [79, 83, 84] },
      ', modelise la trajectoire individuelle (effets aleatoires) comme covariable temps-dependante dans le modele de survie, produisant une prediction continue individualisee. Le ',
      { b: 'JLCM' },
      ' postule au contraire l existence de classes latentes discretes et fournit une probabilite d appartenance par patient. Les deux approches sont complementaires : le JM optimise la prediction individuelle (logique de "win probability"), tandis que le JLCM optimise l identification de sous-phenotypes cliniquement utilisables (logique de stratification a deux ou trois bras).'
    ], { first: true }),
    para([
      'L etude comparative de Brombin, Di Serio et Rancoita (2014) ',
      { cite: [83] },
      ' sur la cohorte HIV-CASCADE (n = 648, lymphocytes CD4 longitudinaux) a directement compare ces deux approches sur le meme jeu de donnees : les deux donnent des inferences valides, mais avec des objectifs differents - le JM excelle pour la prediction de mortalite individuelle, le JLCM pour la description des sous-phenotypes evolutifs et l identification des facteurs associes a leur appartenance.'
    ]),
    H2('8.5. Choix methodologiques dans ALYCANTE'),
    para([
      'Le projet ALYCANTE-biomarqueurs a privilegie le JLCM plutot que le JM classique pour deux raisons. Premierement, l objectif clinique est l identification de sous-classes pronostiques actionnables - des groupes "BON" et "MAUVAIS" pronostic stratifiables des le J14 post-infusion - plutot qu une prediction individuelle continue dont l interpretation reste plus complexe en consultation. Deuxiemement, la taille d echantillon limitee (n = 57) favorise des modeles parsimonieux : deux classes latentes avec une structure aleatoire ',
      { i: 'random = ~time' },
      ' (intercept et pente individuels au sein de chaque classe) offrent un compromis raisonnable entre flexibilite et risque de surapprentissage.'
    ], { first: true }),
    para([
      'Le choix du seed 123 dans l algorithme d optimisation merite une mention specifique. Sur cette cohorte de 57 patients, certains seeds (456, 2024, 3141, 5000, etc.) conduisent l estimation a la frontiere de l espace des parametres - typiquement une variance d effet aleatoire convergeant vers zero ou une correlation atteignant ±1 - ce qui fait echouer la fonction ',
      { i: 'predictClass()' },
      ' avec une erreur de matrice non definie positive. Le seed 123 (et plusieurs autres : 42, 789, 1000) donne le meme BIC et la meme classification que les seeds problematiques, mais avec une matrice de variance-covariance correctement estimee a l interieur de l espace des parametres. Cette observation, documentee dans la memoire methodologique du projet, illustre les limites pratiques d application des modeles complexes sur des effectifs modestes, et plaide pour une validation externe sur cohorte plus large.'
    ]),
    para([
      'Le modele final identifie deux classes : une classe BON (cl1, n = 32, taux de R/R a 12 mois de 6 %) et une classe MAUVAIS (cl2, n = 25, taux de R/R a 12 mois de 96 %). Tronque a J14 - c est-a-dire en utilisant uniquement les mesures de leucapherese, J-5, J0 et J14 pour predire la classe d appartenance - le modele atteint Se = Sp = PPV = NPV = 100 % pour la prediction de R/R a 12 mois chez les 40 patients avec un followup adequat. Cette performance, qu il faudra confirmer par validation externe (notamment sur la cohorte CART de Lea, n = 158, presentee en annexe), constitue le resultat saillant du projet ALYCANTE-biomarqueurs.'
    ])
  ];
}

// ============ SECTION 11 ============
function buildSection11() {
  return [
    H1('11. Anticorps bispecifiques CD20xCD3 dans le DLBCL refractaire'),
    H2('11.1. Une alternative therapeutique en plein essor'),
    para([
      'Apres l essor des CAR-T, les anticorps bispecifiques CD20xCD3 (BsAbs) representent la deuxieme grande revolution immunotherapeutique du DLBCL R/R, avec plusieurs avantages logistiques majeurs sur les therapies cellulaires : disponibilite immediate, absence de necessite de leucapherese et de lymphodepletion, administration ambulatoire possible, cout moindre. Trois molecules ont obtenu une AMM apres au moins deux lignes de traitement : glofitamab (Roche/Columvi, IV), epcoritamab (AbbVie/Genmab, sous-cutane) et mosunetuzumab (Roche/Lunsumio, indication limitee au lymphome folliculaire). Odronextamab a recu une approbation europeenne plus recente ',
      { cite: [95] },
      ', et plusieurs autres BsAbs sont en developpement. La revue systematique de Bayly-McCredie et coll. (2024, 19 etudes, 1332 patients) ',
      { cite: [98] },
      ' synthetise l ensemble des donnees disponibles a fin 2024.'
    ], { first: true }),
    H2('11.2. Glofitamab : un format 2:1 ameliorant l engagement T'),
    para([
      'Le glofitamab presente une particularite structurelle : son format 2:1 (deux Fab anti-CD20 pour un Fab anti-CD3) augmente l affinite pour la cellule cible et favorise la formation du "synapse immunologique" entre lymphocyte T et cellule tumorale. L etude pivotale phase 2 de Dickinson, Carlo-Stella et coll. publiee dans le NEJM (2022, n = 154 patients DLBCL R/R apres au moins deux lignes) ',
      { cite: [94] },
      ' a rapporte un taux de reponse complete de 39 % (IC95 32-48 %) avec un schema d administration de duree fixe (12 cycles), apres pretraitement par obinutuzumab destine a moderer la liberation cytokinique. Le delai median d obtention de la reponse complete etait de 42 jours, et 78 % des reponses completes etaient maintenues a douze mois. La PFS a douze mois etait de 37 % pour l ensemble de la cohorte. Le syndrome de relargage cytokinique survenait chez 63 % des patients mais restait majoritairement de bas grade (CRS de grade superieur ou egal a 3 chez seulement 4 %), confirmant la securite acceptable du regime.'
    ], { first: true }),
    H3('Glofitamab apres echec de CAR-T : l etude LYSA'),
    para([
      'L application la plus pertinente pour la trajectoire des patients ALYCANTE est l etude phase 2 monobras de la LYSA conduite par Cartron, Houot, Al Tabaa et coll. (2025, Nat Cancer) ',
      { cite: [97] },
      '. Cette etude a enrole 46 patients DLBCL R/R apres echec de CAR-T, une population au pronostic historiquement dramatique avec une survie globale mediane inferieure a six mois. Grace a un schema d escalade rapide atteignant la dose pleine en une semaine, la survie globale mediane atteint 14.7 mois (IC95 8.8 - non atteinte), validant le critere principal. Le taux de reponse metabolique objective est de 76.1 % et le taux de reponse metabolique complete de 45.7 %. La PFS mediane plus courte (3.8 mois) suggere que les reponses ne sont pas toujours durables dans cette population fortement pretraitee, mais l absence de CRS et d ICANS de grade superieur ou egal a 3 valide la securite du protocole accelere et ouvre la voie a son utilisation en pratique courante.'
    ], { first: true }),
    H2('11.3. Epcoritamab et mosunetuzumab : profils et indications'),
    para([
      'L epcoritamab, administre par voie sous-cutanee, presente un profil pharmacocinetique stable et permet une utilisation ambulatoire. Les donnees du programme EPCORE NHL ',
      { cite: [102] },
      ' ont valide la dose recommandee de 48 mg, et l etude EPCORE NHL-3 conduite chez 36 patients japonais (Izutsu et coll. 2023) ',
      { cite: [100] },
      ' a confirme un taux de reponse globale de 56 % et de reponse complete de 44 %, avec un profil de tolerance comparable aux essais internationaux (CRS chez 83 %, principalement de grade 1-2). Le mosunetuzumab, qui dispose d une AMM principalement pour le lymphome folliculaire R/R (Budde et coll. 2022 ',
      { cite: [101] },
      '), reste en developpement dans le DLBCL, principalement en combinaison. Son profil de tolerance dans une serie de 218 patients NHL (Matasar et coll. 2023) ',
      { cite: [103] },
      ' est favorable, avec un CRS chez 39 % seulement et un ICANS chez 1 %.'
    ], { first: true }),
    H2('11.4. Donnees real-world : tolerance et limites'),
    para([
      'L analyse multicentrique americaine de Brooks, Zabor et coll. (2025) ',
      { cite: [96] },
      ', portant sur 245 patients DLBCL R/R traites par epcoritamab (n = 156) ou glofitamab (n = 89) en pratique reelle, apporte un eclairage essentiel sur la translation clinique. Pres de 60 % des patients auraient ete ineligibles aux essais pivots en raison de comorbidites ou de traitements anterieurs ; 60 % avaient deja recu un CAR-T. Le taux de reponse global etait comparable a celui des essais (51 % pour epcoritamab, 53 % pour glofitamab), mais la PFS mediane etait beaucoup plus courte en pratique reelle : seulement 2.6 mois (IC95 2.0-3.8) et l OS mediane de 7.8 mois. Cette discordance suggere que la population reelle est plus fragile que celle des essais et que les reponses obtenues ne sont pas systematiquement durables.'
    ], { first: true }),
    para([
      'Une observation biologique particulierement preoccupante emerge de cette etude real-world : sur les dix-sept patients ayant beneficie d une biopsie pairee avant et apres traitement par BsAb, quinze (88 %) avaient perdu l expression de CD20 a la rechute, avec un delai median de progression de 3.7 mois. Cette perte d antigene cible constitue un mecanisme de resistance majeur, analogue a la perte de CD19 observee apres CAR-T, et a des consequences directes sur la sequence therapeutique : si un patient recoit un BsAb avant un CAR-T anti-CD19, la perte de CD20 ne compromet pas le CAR-T ulterieur ; mais a l inverse, un patient traite d abord par CAR-T anti-CD19 puis perdant CD20 apres BsAb sera depourvu de cibles antigeniques validees.'
    ]),
    H2('11.5. Sequencement therapeutique : CAR-T puis bispecifique'),
    para([
      'L ensemble des donnees disponibles plaide pour la sequence CAR-T puis BsAb en cas d echec, plutot que l inverse. Trois arguments convergent en faveur de cette strategie. D abord, le benefice de survie demontre par le glofitamab apres echec de CAR-T (LYSA, OS mediane 14.7 mois) ',
      { cite: [97] },
      ' n a pas son equivalent dans la situation reciproque. Ensuite, la perte d antigene CD19 post-CAR-T n affecte pas la cible CD20 utilisee par les BsAbs, ce qui preserve l efficacite de la sequence. Enfin, la perte de CD20 post-BsAb compromettrait l efficacite ulterieure d un CAR-T anti-CD19, fermant cette option de sauvetage si le BsAb a ete utilise en premier. Cette logique de preservation des cibles antigeniques s applique directement aux patients d ALYCANTE : ceux qui rechuteront seront prioritairement orientes vers un BsAb, vraisemblablement le glofitamab compte tenu des donnees LYSA. Le suivi par ctDNA prend ici toute sa place : il pourrait permettre la detection precoce de la rechute moleculaire post-CAR-T, autorisant l initiation du bispecifique avant la reprise clinique de la maladie.'
    ], { first: true })
  ];
}

// ============ SECTION 12 ============
function buildSection12() {
  return [
    H1('12. Complications immunologiques post-CAR-T : CRS, ICANS et ICAHT'),
    H2('12.1. Le syndrome de relargage cytokinique (CRS) : un standard cliniquement maitrise'),
    para([
      'Le syndrome de relargage cytokinique reste la complication la plus frequente apres CAR-T anti-CD19, mais son management a considerablement progresse au cours de la derniere decennie. L analyse de registre CIBMTR de Shouval et coll. (2025), portant sur 1916 patients LBCL traites en pratique reelle aux Etats-Unis entre 2018 et 2020 ',
      { cite: [107] },
      ', donne les chiffres de reference contemporains : 75.2 % des patients developpent un CRS de tout grade, mais seulement 11.3 % presentent un CRS de grade 3 ou plus. La proportion de CRS severes a diminue significativement au fil des annees - de 14.0 % en 2018 a 9.2 % en 2020 (p < 0.01) - traduisant l amelioration de la prise en charge (utilisation precoce du tocilizumab, identification des facteurs predicteurs, anticipation thermique).'
    ], { first: true }),
    para([
      'Le risque de CRS de grade 3 ou plus differe significativement selon le produit CAR-T : l axi-cel y est associe a un odds ratio de 4.6 par rapport au tisa-cel (p < 0.01), ce qui doit etre pris en compte dans la decision therapeutique chez les patients fragiles. La physiopathologie - liberation massive d IL-6, IFN-gamma, TNF-alpha par les cellules T activees - et la prise en charge - tocilizumab (anti-IL6R), corticosteroides, support symptomatique selon les criteres ASTCT/Lee - sont aujourd hui bien codifiees ',
      { cite: [106] },
      '. Les recommandations conjointes EBMT/JACIE/EHA (Hayden et coll. 2022) constituent la reference pratique en Europe.'
    ]),
    H2('12.2. La neurotoxicite ICANS : un signal moins resolu'),
    para([
      'Le syndrome de neurotoxicite associe aux cellules effectrices immunologiques (ICANS) regroupe des manifestations diverses : encephalopathie, aphasie, convulsions, myoclonies, dans les cas les plus severes œdeme cerebral. Les donnees du registre CIBMTR rapportent un ICANS de tout grade chez 43.5 % des patients, et de grade 3 ou plus chez 21 % de la population totale (soit 47.7 % des cas d ICANS) ',
      { cite: [107] },
      '. Contrairement au CRS, la proportion d ICANS severes n a pas significativement diminue entre 2018 et 2020 (41.5 % a 53.7 % parmi les ICANS, p = 0.10), suggerant que les outils therapeutiques disponibles - principalement les corticosteroides - restent limites.'
    ], { first: true }),
    para([
      'Une observation cliniquement importante emerge de cette analyse : 57.1 % des CRS s accompagnent d un ICANS, et 97.5 % des ICANS surviennent chez des patients qui ont aussi presente un CRS. Cette colocalisation suggere un continuum physiopathologique entre les deux syndromes, possiblement relie a la production cytokinique systemique. Les valeurs d ALYCANTE - CRS de grade superieur ou egal a 3 chez 8.1 %, neurotoxicite de grade superieur ou egal a 3 chez 14.5 % ',
      { cite: [45] },
      ' - se situent dans la fourchette des essais pivots malgre une population non eligible a l ASCT, ce qui valide la securite du traitement dans cette population fragile.'
    ]),
    H2('12.3. ICAHT : la cytopenie prolongee, complication recemment formalisee'),
    para([
      'L ICAHT (',
      { i: 'Immune effector Cell-Associated HematoToxicity' },
      ') a ete formellement reconnu comme entite distincte en 2023 par les societes EHA-EBMT ',
      { cite: [104, 105] },
      '. Il se definit par une cytopenie prolongee post-CAR-T - typiquement une neutropenie de grade 3 ou plus persistant plus de quatorze jours apres l infusion ou suivant un profil bi/triphasique. Sa physiopathologie est multifactorielle : toxicite directe de la lymphodepletion, suppression medullaire par cytokines inflammatoires, infiltration tumorale residuelle, infections secondaires.'
    ], { first: true }),
    para([
      'L outil predictif le plus utilise est le score ',
      { b: 'CAR-HEMATOTOX (CAR-HT)' },
      ' developpe par Rejeski et coll., reposant sur cinq parametres pre-CAR-T : numeration des polynucleaires neutrophiles, des plaquettes, de l hemoglobine, et taux de CRP et de ferritine. Le score a ete prospectivement valide dans le LBCL et le MCL. La validation comparative chinoise de Zhang et coll. (2025, n = 119) ',
      { cite: [105] },
      ' confirme sa performance : 67 % des patients classes a haut risque presentent une neutropenie prolongee mediane de 17.7 jours contre seulement 5.3 jours dans le groupe a bas risque (p < 0.001). Pour les leucemies aigues B (B-ALL), Nair et coll. (2025) ',
      { cite: [104] },
      ' ont developpe une variante ALL-Hematotox dans laquelle la ferritine est remplacee par la charge medullaire au diagnostic, atteignant une AUC de 0.84 pour la prediction de neutropenie severe prolongee.'
    ]),
    H2('12.4. Mortalite non liee a la maladie et toxicites d organes'),
    para([
      'L etude de registre EBMT de Penack, Peczynski et coll. (2023) ',
      { cite: [108] },
      ', portant sur 492 patients LBCL post-axi-cel ou tisa-cel, fournit une evaluation globale de la securite a moyen terme. La mortalite non liee a la maladie (NRM) est de 3.1 % a trois mois et 5.2 % a un an, principalement liee aux toxicites des therapies cellulaires (6.4 % des deces) et aux infections (4.4 %). Les toxicites d organes severes (grade 3 ou plus) sont relativement rares : renale dans 3 % des cas, cardiaque dans 2.3 %, gastro-intestinale dans 2.3 %, hepatique dans 1.8 %. Toutes surviennent majoritairement dans les trois premieres semaines post-infusion. La cause de deces la plus frequente reste de loin la progression tumorale (85.1 % des deces), ce qui rappelle que l enjeu principal demeure l efficacite antitumorale plus que la maitrise de la toxicite chez les patients atteints d un DLBCL R/R.'
    ], { first: true }),
    H2('12.5. ctDNA et prediction des toxicites : une piste prometteuse'),
    para([
      'L association entre charge moleculaire baseline et risque de toxicite, deja evoquee en section 6, ouvre une piste de stratification preventive. Les patients identifies comme a haut risque sur la base du ctDNA pre-CAR-T pourraient beneficier d une surveillance renforcee (monitoring biologique rapproche, accessibilite au tocilizumab) et d une optimisation de la therapie de pont visant a reduire la masse tumorale. Le developpement de scores integratifs combinant ctDNA, CAR-HT, IMPI et caracteristiques cliniques reste un objectif de recherche prioritaire, qu aucune etude prospective n a encore valide a notre connaissance. La cohorte ALYCANTE-biomarqueurs, par son design et son suivi precoce, pourrait y contribuer.'
    ], { first: true })
  ];
}

// ============ SECTION 13 ============
function buildSection13() {
  return [
    H1('13. Synthese quantitative : meta-analyses des hazard ratios ctDNA'),
    H2('13.1. La meta-analyse pionniere de Yao (2021)'),
    para([
      'La premiere synthese quantitative de la valeur pronostique du ctDNA dans les lymphomes a ete proposee par Yao, Xu et coll. en 2021 (Clin Exp Med) ',
      { cite: [23] },
      ', sur la base de huit etudes publiees totalisant 767 patients. Les resultats sont coherents avec la litterature individuelle : un ctDNA eleve est associe a un hazard ratio pondere de 2.24 (IC95 1.63-3.08, p < 0.00001) pour la PFS dans les lymphomes pris globalement. Restreint aux DLBCL (sous-groupe de 379 patients sur trois etudes), le HR est de 2.01 (IC95 1.42-2.85, p < 0.0001), avec une heterogeneite modeste. Pour l EFS, le HR pondere est de 4.53 (1.79-11.47) dans deux etudes totalisant 192 patients ; pour l OS dans le DLBCL, il s eleve a 3.09 (1.50-6.35). Cette meta-analyse, bien que limitee par l heterogeneite des methodes ctDNA et des seuils utilises dans les etudes individuelles, etablit la robustesse globale de l effet.'
    ], { first: true }),
    H2('13.2. La meta-analyse bayesienne IPD de 2026 (lymphome de Hodgkin)'),
    para([
      'Une approche methodologique plus aboutie a ete developpee par Shahsavand, Forghani et coll. (Crit Rev Oncol Hematol 2026, in press) ',
      { cite: [110] },
      ' pour le lymphome de Hodgkin, sur la base de dix etudes totalisant 1158 patients. Cette meta-analyse bayesienne avec donnees individuelles patients (IPD) reconstruites a partir des courbes de Kaplan-Meier digitalisees apporte plusieurs raffinements importants : analyse temporelle de l effet pronostique, calcul des temps de survie restreints (RMST) avec leurs intervalles de credibilite, et stratification par timepoint de mesure.'
    ], { first: true }),
    para([
      'Les resultats objectivent un effet pronostique dose-dependant croissant au fil du traitement. Un ctDNA baseline eleve est associe a un HR PFS de 2.74 (IC95 1.30-5.75) et a une perte de RMST a cinq ans de 7.7 mois. La positivite ctDNA au temps interim multiplie l effet par presque trois (HR 5.99 ; perte RMST 22.7 mois). En fin de traitement, l association atteint une amplitude rarement rencontree : HR PFS de 13.4 (IC95 3.97-41.87), perte RMST de 39.2 mois - autrement dit, la quasi-totalite du benefice de survie predictible. Pour l OS, les HR sont respectivement de 2.49 et 4.74 pour baseline et fin de traitement. Cette gradation temporelle - la valeur pronostique du marqueur augmente avec le temps de mesure - est une observation profondement convergente avec les donnees DLBCL detaillees en section 7.'
    ]),
    H2('13.3. Le forest plot de synthese (Figure 1)'),
    para([
      'La Figure 1 propose une synthese visuelle des hazard ratios ctDNA dans les lymphomes B agressifs, sur la base de 18 estimations issues de 13 etudes representatives publiees entre 2015 et 2026. Cinq categories sont distinguees par code couleur : ctDNA baseline (bleu), reponse moleculaire C1-C2 (orange), fin de traitement (vert pour ctDNA, rouge pour la reference PET), post-CAR-T (violet) et meta-analyses (gris). Plusieurs observations se degagent de cette representation.'
    ], { first: true }),
    para([
      'Premierement, on observe un gradient temporel net : les HR baseline (1.5 a 3.8) sont moderes, ceux mesures apres un ou deux cycles atteignent 3 a 8, ceux mesures en fin de traitement explosent jusqu a 28.7. Cette observation confirme la convergence avec la meta-analyse Hodgkin et suggere un principe biologique general : plus la mesure ctDNA est proche de la fin du traitement, plus elle integre les determinants pronostiques de l ensemble du parcours therapeutique. Deuxiemement, la comparaison directe entre ctDNA et PET en fin de traitement - rendue possible par l etude de Roschewski (2025) qui rapporte les deux mesures chez les memes patients - montre une superiorite ecrasante du ctDNA (HR 28.7 contre 3.6) ',
      { cite: [75] },
      '. Troisiemement, dans le contexte post-CAR-T, l effet pronostique est conserve et meme amplifie : le HR du ctDNA J28 atteint 14.0 dans l etude pivotale de Frank (2021) ',
      { cite: [25] },
      '.'
    ]),
    H2('13.4. Limites et perspectives'),
    para([
      'Plusieurs limites temperent l interpretation de ces resultats. L heterogeneite methodologique entre etudes - methodes ctDNA, definitions de positivite, seuils, timing precis - est considerable et fait que la comparabilite directe des HR n est pas toujours pertinente. Le biais de publication est probable, les etudes negatives etant moins susceptibles de paraitre. Les donnees individuelles patient (IPD) ne sont disponibles que pour une minorite d etudes, limitant la possibilite de meta-analyses statistiquement plus puissantes. Enfin, la PhasED-Seq, plateforme la plus sensible, reste limitee a quelques etudes (Roschewski 2025, Stepan 2026, Klimova 2025) et son adoption europeenne est encore tres restreinte.'
    ], { first: true }),
    para([
      'Malgre ces reserves, le constat global est clair et coherent : le ctDNA constitue un marqueur pronostique extremement robuste dans les lymphomes B agressifs, dont l ordre d effet depasse largement celui de la plupart des marqueurs cliniques et d imagerie traditionnels. Sa transition de l outil de recherche vers la pratique clinique routiniere - question exploree dans le ',
      { i: 'roadmap' },
      ' de Goldstein et coll. ',
      { cite: [91] },
      ' - est un objectif desormais a court terme.'
    ])
  ];
}

// ============ FIGURES + TABLES (regrouped) ============
function buildFiguresAndTables() {
  return [
    H1('Figures de synthese et tableau comparatif des methodes'),
    para([
      'Les figures ci-apres synthetisent visuellement les principaux enseignements des sections precedentes. La Figure 1 propose une vue d ensemble du paysage pronostique du ctDNA dans les lymphomes B agressifs. La Figure 2 retrace la chronologie des avancees pivotales depuis 2015. La Figure 3 compare la sensibilite analytique des differentes methodes de detection. La Figure 4 confronte directement le ctDNA-MRD a la reponse PET en fin de traitement ou apres CAR-T. Le Tableau 1, en fin de section, detaille les onze methodes principales de detection.'
    ], { first: true }),
    H2('Figure 1 - Forest plot des HR ctDNA'),
    ...figureBlock('fig1_forest_plot_HR_ctDNA.png',
      'Figure 1. Forest plot des hazard ratios ctDNA dans les lymphomes B agressifs (18 estimations issues de 13 etudes publiees entre 2015 et 2026). Cinq categories distingues par code couleur : ctDNA baseline (bleu), reponse moleculaire C1-C2 (orange), fin de traitement (vert ctDNA, rouge PET pour reference), post-CAR-T (violet), meta-analyses (gris). La taille du marqueur est proportionnelle au logarithme de l effectif. La reference HR = 1 (absence d effet) est materialisee par la ligne rouge pointillee.', 560),
    H2('Figure 2 - Timeline des etudes pivot'),
    ...figureBlock('fig2_timeline_etudes.png',
      'Figure 2. Timeline 2014-2026 des etudes pivots dans le DLBCL post-CAR-T et le suivi par ctDNA. Code couleur : methodes ctDNA (orange), pronostic clinique (bleu), essais CAR-T (violet), bispecifiques (rouge). Les etudes francaises (ALYCANTE, LYSA glofitamab) sont indiquees.', 620),
    H2('Figure 3 - Sensibilite analytique des methodes'),
    ...figureBlock('fig3_methodes_sensibilite.png',
      'Figure 3. Comparaison de la limite de detection des methodes ctDNA et de l imagerie. Echelle logarithmique inversee de la fraction tumorale detectable. La PhasED-Seq atteint 7 x 10⁻⁷ (sub-ppm) contre environ 10⁻¹ pour le PET. Les paliers MRD classique (10⁻⁴) et ultra-sensible (10⁻⁶) sont materialises.', 620),
    H2('Figure 4 - ctDNA-MRD versus PET-CMR'),
    ...figureBlock('fig4_ctDNA_vs_PET.png',
      'Figure 4. Comparaison directe des hazard ratios ctDNA-MRD et PET-CMR mesures aux memes timepoints (fin de traitement ou post-CAR-T) dans six etudes representatives. Echelle logarithmique. Dans toutes les etudes, le ctDNA discrimine plus fortement que le PET, l effet etant particulierement marque dans le contexte post-CAR-T (Roschewski 2025, Frank 2021).', 560),
    new Paragraph({ children: [new PageBreak()] }),
    H2('Tableau 1 - Comparatif des methodes de detection ctDNA'),
    para([T('Synthese des onze methodes principales selon leur sensibilite analytique, leur necessite de biopsie tissulaire, leurs avantages et leurs limites cliniques, avec les etudes representatives correspondantes.')], { first: true }),
    buildMethodsTable()
  ];
}

// ============ SECTION 14 (landscape) ============
function buildSection14() {
  return [
    new Paragraph({ children: [new PageBreak()] }),
    H1('14. Comparatif des trois produits CAR-T anti-CD19 dans le DLBCL'),
    para([
      'Le paysage therapeutique du DLBCL R/R repose desormais sur trois produits CAR-T anti-CD19 cliniquement disponibles : axicabtagene ciloleucel (axi-cel, Yescarta), tisagenlecleucel (tisa-cel, Kymriah) et lisocabtagene maraleucel (liso-cel, Breyanzi). Bien que tous trois ciblent le meme antigene CD19 et reposent sur un meme principe immunotherapeutique, ils differencient sur des aspects structurels et cliniques qui conditionnent les indications, l efficacite et le profil de tolerance.'
    ], { first: true }),
    H2('14.1. Differences structurelles et pharmacologiques'),
    para([
      'La premiere difference fondamentale porte sur le domaine de costimulation intracellulaire. L axi-cel utilise un domaine CD28, associe a une activation plus rapide et plus puissante des lymphocytes T mais aussi a une demi-vie plus courte ; tisa-cel et liso-cel emploient un domaine 4-1BB, associe a une persistance plus longue des cellules effectrices mais une cinetique d activation plus progressive. Cette difference structurelle explique en partie le profil de toxicite distinct : l axi-cel induit plus frequemment des CRS et ICANS severes, comme le confirment les donnees CIBMTR (OR 4.6 pour CRS de grade ≥ 3 par rapport au tisa-cel) ',
      { cite: [107] },
      '. La deuxieme difference notable concerne la manufacture : le liso-cel est seul a separer les fractions CD4 et CD8 et a les reinfuser dans un ratio 1:1 controle, ce qui contribuerait a son profil de tolerance favorable (Filosto et coll. 2024, ZUMA-7) ',
      { cite: [56] },
      '.'
    ], { first: true }),
    H2('14.2. Essais pivots et indications AMM'),
    para([
      'L axi-cel et le tisa-cel ont d abord obtenu leur AMM en troisieme ligne et au-dela sur la base des etudes ZUMA-1 (axi-cel) et JULIET (tisa-cel, Schuster et coll. NEJM 2019) ',
      { cite: [113] },
      ', et le liso-cel sur l etude TRANSCEND NHL 001 (Salles et coll. 2021) ',
      { cite: [19, 31] },
      '. Cette etape a marque une transformation majeure du pronostic dans une population historiquement consideree comme palliative (SCHOLAR-1).'
    ], { first: true }),
    para([
      'L extension a la deuxieme ligne s est faite differemment pour les trois produits. L axi-cel a obtenu son AMM en 2L apres ZUMA-7 (FDA 2022) ',
      { cite: [44] },
      ', etude randomisee 1:1 dans laquelle l axi-cel a montre une superiorite sur la chimiotherapie standard suivie d ASCT (EFS median 8.3 vs 2.0 mois, HR 0.40 ; OS 4 ans 54.6 % vs 46 %, HR 0.73) ',
      { cite: [18, 43] },
      '. Le liso-cel a egalement obtenu son AMM en 2L grace a l essai TRANSFORM, dont l analyse correlative ctDNA (Stepan 2026) ',
      { cite: [90] },
      ' montre une superiorite supplementaire sur le critere moleculaire (MRD plus profonde et plus durable). Le tisa-cel n a pas d AMM en 2L, faute d essai randomise concluant. L etude ALYCANTE (Houot et coll. 2023) ',
      { cite: [45] },
      ' s inscrit dans le sillage de ZUMA-7 mais cible une population non couverte par cet essai : les patients non eligibles a l ASCT en raison de l age ou de comorbidites.'
    ]),
    H2('14.3. Profils de tolerance compares'),
    para([
      'Sur le plan de la tolerance, le liso-cel se distingue par le profil le plus favorable. Les taux de CRS de grade ≥ 3 sont de 2 % pour liso-cel, 11-13 % pour axi-cel, et 22 % pour tisa-cel ; les taux d ICANS de grade ≥ 3 sont de 10 %, 21-32 % et 12 % respectivement. Cette difference de tolerance a des consequences pratiques importantes : le liso-cel peut etre administre en ambulatoire dans certains centres, ce qui n est pas envisageable pour l axi-cel. Pour les patients ages ou fragiles, ces considerations peuvent peser autant que l efficacite pure dans le choix du produit, comme le suggere la discussion accompagnant l etude ALYCANTE.'
    ], { first: true }),
    H2('14.4. Tableau de synthese (Tableau 2)'),
    para([
      'Le Tableau 2 ci-apres rassemble les caracteristiques principales des trois produits, des aspects structurels aux donnees d efficacite et de tolerance. Les chiffres reportes pour ALYCANTE (axi-cel uniquement) et pour la cohorte multicentrique de Lea (N = 158, distribution Yescarta 66 %, Breyanzi 18 %, Kymriah 15 %) permettent de situer les populations etudiees dans le contexte general.'
    ], { first: true }),
    buildCARTcomparisonTable(),
    para([T('Sources : ZUMA-1 (refs en bibliographie), ZUMA-7 [18,43,44], JULIET [113], TRANSCEND [31,19], TRANSFORM [90], ALYCANTE [45,86], Brooks 2025 [96], Cartron 2025 [97].')], { first: true }),
    new Paragraph({ children: [new PageBreak()] }),
    H2('14.5. Implications pour ALYCANTE et son interpretation'),
    para([
      'L etude ALYCANTE etant restreinte a l axi-cel, les resultats biomarqueurs s appliquent directement a la population ZUMA-7 (axi-cel 2L) et plus generalement aux patients traites par axi-cel toutes lignes confondues. Leur generalisation aux autres produits CAR-T (tisa-cel, liso-cel) suppose une validation specifique, dans la mesure ou les dynamiques cinetiques cellulaires et les profils de toxicite different. La cohorte multicentrique de Lea (N = 158), discutee en annexe, offre un materiau de validation precieux : elle inclut les trois produits dans des proportions reflechissant la pratique reelle francaise. La comparaison de survie entre ALYCANTE et Lea, qui montre des courbes PFS et OS quasi superposables (log-rank p = 0.95 et 0.62 respectivement), valide la representativite externe de la cohorte ALYCANTE et autorise une extrapolation prudente des conclusions ctDNA a la population CAR-T plus large.'
    ], { first: true }),
    para([
      'Une perspective interessante consisterait a stratifier l analyse ctDNA par produit CAR-T dans la cohorte de Lea, ce qui permettrait de tester si les seuils et trajectoires identifies dans ALYCANTE (entierement axi-cel) restent pertinents pour les patients traites par tisa-cel ou liso-cel. Cette analyse, en cours, completera l interpretation des resultats principaux.'
    ])
  ];
}

// ============ SECTION 15 (PCNSL) ============
function buildSection15() {
  return [
    H1('15. Le lymphome primaire du SNC : un terrain particulier'),
    H2('15.1. Une variante du DLBCL au pronostic intermediaire'),
    para([
      'Le lymphome primaire du systeme nerveux central (PCNSL) constitue une variante rare mais distincte du DLBCL, caracterisee par une localisation strictement encephalique (parenchyme cerebral, leptomeninges, vitreoretine) sans atteinte systemique au diagnostic. Sa biologie partage de nombreux traits avec le DLBCL extra-cerebral mais s en distingue par une frequence plus elevee de mutations MYD88 L265P, CD79B et CARD11 - configurations rappelant le sous-groupe MCD de la classification LymphGen. Le pronostic est intermediaire entre celui du DLBCL classique et celui des lymphomes systemiques avec atteinte SNC secondaire. Le traitement repose sur des regimes de chimiotherapie a haute dose de methotrexate, eventuellement suivis d ASCT pour les patients jeunes en bon etat general.'
    ], { first: true }),
    H2('15.2. Les limites de la biopsie tissulaire dans le PCNSL'),
    para([
      'La specificite anatomique du PCNSL rend la biopsie tissulaire particulierement problematique. Les lesions sont souvent profondes, multiples, voire deja diffuses au diagnostic, ce qui complique l acces chirurgical. Les biopsies stereotaxiques portent des risques neurologiques non negligeables et ne fournissent souvent qu un materiel limite, peu adapte aux analyses moleculaires exhaustives. Dans ce contexte, la liquid biopsy - qu il s agisse de plasma ou de liquide cephalorachidien - constitue une alternative particulierement attractive ',
      { cite: [114, 115, 116, 120] },
      '. La revue specifique de Šúri et Mocikova (2025) ',
      { cite: [116] },
      ' synthetise les approches CSF disponibles pour le diagnostic de l atteinte leptomeningee du DLBCL.'
    ], { first: true }),
    H2('15.3. Le ctDNA plasmatique : sensibilite reduite par la barriere hemato-encephalique'),
    para([
      'Contrairement au DLBCL systemique ou le ctDNA plasmatique est detectable chez plus de 95 % des patients au diagnostic, sa sensibilite dans le PCNSL est limitee par la barriere hemato-encephalique qui restreint le passage des fragments d ADN tumoral vers la circulation peripherique. L etude prospective de Yoon, Kim et coll. (2021, n = 42) ',
      { cite: [115] },
      ' a evalue le ctDNA plasmatique chez des patients PCNSL diagnostiques entre 2017 et 2018. La detection de mutations somatiques representant le ctDNA n a ete possible que chez 27 % des patients (11 sur 41 evaluables), une proportion considerablement inferieure a celle observee dans le DLBCL systemique. Les mutations principalement detectees concernent PIM1 (36 % des cas positifs), KMT2D, PIK3CA et MYD88 (27 % chacun). La concordance entre les profils mutationnels plasmatiques et tissulaires est de 45 %, ce qui indique que certaines mutations importantes presentes dans le tissu n atteignent pas la circulation peripherique. Pour le suivi longitudinal, sur sept patients en reponse complete tracables, quatre ont vu leurs mutations ctDNA disparaitre et trois ont conserve des mutations detectables en fin de traitement ; cette observation suggere une valeur potentielle pour la MRD, mais reste limitee par le faible taux de detection initial.'
    ], { first: true }),
    H2('15.4. Le ctDNA dans le LCS : sensibilite optimale pour le PCNSL'),
    para([
      'Le passage des fragments tumoraux vers le LCS etant facilite par la proximite anatomique, le ctDNA du LCS est plus concentre et permet une meilleure detection. Plusieurs strategies se sont developpees autour de ce compartiment ',
      { cite: [114, 116] },
      '. La detection de la mutation MYD88 L265P par ddPCR sur LCS constitue aujourd hui l approche la plus etablie pour le diagnostic du PCNSL : la mutation est presente chez environ 75 % des PCNSL avec composante ABC et offre une sensibilite/specificite tres elevee dans le LCS. Sa combinaison avec le dosage d interleukine 10 (IL-10) sur le meme prelevement ameliore encore les performances diagnostiques (Šúri 2025). Pour le suivi MRD post-traitement, des panels NGS plus etendus sur LCS sont en developpement.'
    ], { first: true }),
    H2('15.5. Lymphomes vitreoretiniens : le cas particulier des fluides oculaires'),
    para([
      'Une variante particulierement complexe est le lymphome vitreoretinien (VRL), sous-type du PCNSL touchant principalement le vitre et la retine. L etude pilote de Wang, Su et coll. (Haematologica 2022, n = 15) ',
      { cite: [117] },
      ' a evalue l analyse de ctDNA dans l humeur aqueuse (HA) et le fluide vitreen (FV) chez ces patients. Les profils moleculaires des prelevements HA et FV pries au baseline sont hautement concordants (>90 %), tandis que la concordance avec le LCS est plus faible avec des frequences alleliques nettement inferieures. Cette observation suggere que le compartiment oculaire est anatomiquement separable du compartiment cerebral, et que chaque type de prelevement reflete preferentiellement le siege primaire de la maladie. Pour le suivi du traitement, les changements de frequences alleliques en HA correlent avec les niveaux d IL-10, marqueur de reponse oculaire bien etabli.'
    ], { first: true }),
    para([
      'L etude apporte egalement une comparaison genetique interessante entre PCNSL et VRL : les mutations MYD88 sont plus frequentes dans le PCNSL, tandis que les pertes en CDKN2A/B sont plus frequentes dans le VRL. Cette difference biologique se traduit par une difference de reponse therapeutique a l ibrutinib : taux de reponse objective de 65 % pour le PCNSL contre seulement 14 % pour le VRL, ce qui appelle a une individualisation des strategies selon le compartiment anatomique.'
    ]),
    H2('15.6. CAR-T dans le PCNSL : prudence initiale, donnees rassurantes'),
    para([
      'Les essais pivots des CAR-T (ZUMA-1, JULIET, TRANSCEND) excluaient explicitement les patients avec atteinte SNC active, par crainte de neurotoxicite immunologique severe. Cette prudence reglementaire a longtemps prive les patients atteints de PCNSL ou de SCNSL d acces a une therapie potentiellement curative. La meta-analyse de Cook, Dorris et coll. (Blood Adv 2023) ',
      { cite: [119] },
      ' constitue la synthese la plus aboutie des donnees disponibles : 128 patients (30 PCNSL, 98 SCNSL) traites par CAR-T anti-CD19 en dehors des essais formels, dans des series single-center ou des registres. Les resultats sont rassurants : le CRS de grade 3 ou plus survient chez 13 % des PCNSL et 11 % des SCNSL, soit des taux comparables a ceux des patients DLBCL extra-cerebraux ; l ICANS de grade 3 ou plus survient chez 18 % des PCNSL et 26 % des SCNSL, taux egalement comparables. Les taux de reponse complete sont de 56 % pour le PCNSL et 47 % pour le SCNSL, avec 37 % de remission a six mois dans les deux groupes.'
    ], { first: true }),
    para([
      'Cette demonstration empirique a conduit a une evolution progressive des criteres d eligibilite dans les essais cliniques recents et a une plus large inclusion des patients atteints de PCNSL/SCNSL dans les programmes CAR-T. La revue de Miyao, Yokota et Sakemura (2023) ',
      { cite: [120] },
      ' discute les pistes d optimisation : administration intrathecale de CAR-T, ingenierie de cellules lymphotropes, combinaison avec des inhibiteurs de la BHE. Aucune de ces strategies n est encore validee en pratique courante mais elles ouvrent un champ de recherche actif.'
    ]),
    H2('15.7. Implications pour ALYCANTE et perspectives'),
    para([
      'L etude ALYCANTE excluait initialement les patients avec atteinte SNC active, conformement aux pratiques en vigueur pour les essais CAR-T DLBCL. Les enseignements methodologiques d ALYCANTE - en particulier l interet du suivi longitudinal ctDNA et l application des modeles a classes latentes joints - pourraient cependant etre transferables au PCNSL, sous reserve de plusieurs adaptations methodologiques. Premierement, le suivi devrait porter sur le LCS plutot que sur le plasma, compte tenu de la sensibilite limitee du plasma dans cette pathologie. Deuxiemement, le panel moleculaire devrait privilegier les mutations specifiques du PCNSL (MYD88 L265P, CD79B). Troisiemement, le calendrier des prelevements devrait integrer la realite clinique du suivi neurologique, generalement moins frequente que celle des prelevements plasmatiques. Une etude prospective dediee, en collaboration avec les equipes de neuro-oncologie, pourrait constituer une extension naturelle des resultats ALYCANTE.'
    ], { first: true })
  ];
}

// ============ SECTION 16 IMPLICATIONS ============
function buildSection16() {
  return [
    H1('16. Implications pour ALYCANTE et perspectives'),
    H2('16.1. Le positionnement scientifique de l etude'),
    para([
      'A la lumiere de la litterature internationale developpee dans les sections precedentes, l etude ALYCANTE-biomarqueurs s inscrit dans une triple lignee. Premierement, elle prolonge et etend les travaux pionniers de Frank et coll. (2021) sur le suivi ctDNA post-CAR-T ',
      { cite: [25] },
      ', en l appliquant a une population non couverte par les essais americains et europeens precedents : les patients non eligibles a l autogreffe traites en deuxieme ligne. Deuxiemement, elle constitue, a notre connaissance, la premiere application publiee des modeles a classes latentes joints au suivi du ctDNA dans le DLBCL post-CAR-T, transposant ainsi une approche statistique developpee initialement dans d autres contextes (cancer colorectal, hepatocarcinome, neurodegenerescences) ',
      { cite: [28, 55, 78, 82] },
      '. Troisiemement, elle apporte une comparaison directe entre marqueur moleculaire precoce (delta ctDNA J14) et marqueur d imagerie tardif (CMR PET M3, critere principal de l essai clinique), avec une demonstration de superiorite pronostique du premier sur le second.'
    ], { first: true }),
    H2('16.2. Les resultats principaux replaces dans la litterature'),
    para([
      'Le resultat le plus marquant du projet biomarqueur est la performance predictive du modele JLCM tronque au temps J14 : sensibilite, specificite, valeurs predictives positive et negative atteignent toutes 100 % pour la prediction de la rechute/refractarite a 12 mois (n = 40 patients avec followup adequat). Cette performance, sans equivalent direct dans la litterature, doit etre interpretee avec prudence : elle pourrait refleter en partie un surapprentissage lie a la taille d echantillon limitee, et necessite imperativement une validation externe sur cohorte independante. Elle est neanmoins coherente avec les donnees post-CAR-T disponibles, notamment l etude de Frank (2021) ou la valeur predictive positive du ctDNA J28 atteint deja environ 80 % chez les patients dont le PET genere de l incertitude ',
      { cite: [25] },
      '.'
    ], { first: true }),
    para([
      'L indice de reclassement net (NRI) du JLCM J14 par rapport a la CMR M3 est de + 59 % pour la prediction de R/R 12, une amelioration substantielle qui, si elle est confirmee, justifie pleinement l interet d une integration precoce du marqueur moleculaire dans la stratification post-CAR-T. Le couple predictif explore en analyses secondaires - delta_ctDNA_ratio x lymphocytes leucapheresis x duree de mesure M6 - atteint un C-index de 0.752 pour l EFS, valeur tres respectable dans le contexte des modeles pronostiques en oncologie. L ensemble de ces resultats est en accord conceptuel avec les donnees TRANSFORM (Stepan et coll. 2026) ',
      { cite: [90] },
      ' qui montrent une superiorite de la MRD ctDNA sur le PET dans le bras CAR-T, et avec la meta-analyse Hodgkin (Shahsavand 2026) ',
      { cite: [110] },
      ' qui objective un gradient temporel d effet pronostique du ctDNA.'
    ]),
    H2('16.3. La validation externe par comparaison avec la cohorte Lea'),
    para([
      'La comparaison de survie entre ALYCANTE (N = 57) et la cohorte CART de Lea (N = 158, multicentrique LYSARC) realisee en complement apporte un premier argument de generalisabilite. Les medianes de PFS sont quasi identiques (17.6 mois pour ALYCANTE contre 19.1 mois pour Lea, log-rank p = 0.95) ; la survie globale n est atteinte au point de mediane dans aucune des deux cohortes (log-rank p = 0.62) ; les estimations Kaplan-Meier de PFS a 24 mois sont de 45 % et 47 % respectivement, et de 70 % et 58 % pour l OS a 24 mois. La superposition est encore plus marquee lorsqu on restreint la cohorte Lea a la sous-population "ALYCANTE-like" - Yescarta administre en deuxieme ligne, n = 40 - avec p = 0.88 pour la PFS et p = 0.97 pour l OS, soit des courbes quasiment confondues.'
    ], { first: true }),
    para([
      'Cette absence de difference significative entre les deux cohortes - issues de centres et de selections differentes - constitue un argument fort en faveur de la representativite d ALYCANTE pour la pratique CAR-T francaise contemporaine, et autorise une extrapolation prudente des conclusions ctDNA. Une validation prospective de la performance du JLCM sur les donnees ctDNA de la cohorte Lea, lorsqu elles seront disponibles, constituera l etape de validation externe definitive.'
    ]),
    H2('16.4. Limites a discuter de maniere transparente'),
    para([
      'Plusieurs limites doivent etre clairement identifiees pour permettre une interpretation lucide des resultats. La taille d echantillon limitee (n = 57 patients) accroit le risque de surapprentissage du modele JLCM, en particulier compte tenu de la complexite parametrique du modele (effets aleatoires sur l intercept et la pente, plus parametres de classe specifique). La validation externe sur cohorte independante est donc une etape critique et imperative.'
    ], { first: true }),
    para([
      'La dependance au seed dans l algorithme d optimisation du JLCM, deja discutee en section 8, est un autre signe de fragilite numerique sur petit echantillon. Bien que les seeds qui donnent une estimation valide convergent vers le meme BIC et la meme classification, ce phenomene plaide pour une approche prudente et systematique : verification de la stabilite du modele sur plusieurs seeds, analyses de sensibilite, et idealement validation par bootstrap. La cohorte de validation devrait permettre de tester si les memes seeds restent utilisables sur un effectif plus grand, ou si une re-estimation complete est preferable.'
    ]),
    para([
      'L heterogeneite methodologique du ctDNA dans la litterature limite la transposabilite directe des seuils ALYCANTE a d autres centres. La plateforme PhasED-Seq, plus sensible que le CAPP-Seq employe dans ALYCANTE, pourrait redefinir comme positives certaines mesures actuellement classees comme negatives. Cette dimension methodologique merite d etre discutee dans la presentation des resultats : le modele JLCM s adresse a une plateforme donnee et son utilisation avec une plateforme differente necessiterait une recalibration des seuils.'
    ]),
    para([
      'Enfin, la definition stricte du R/R (Progression ou Relapse uniquement, exclusion des censures avant 12 ou 24 mois) constitue un choix methodologique conservateur mais critique. Il garantit que les performances rapportees sont valides pour les patients ayant un suivi suffisant, mais peut sous-estimer le taux d evenement reel dans la cohorte globale. La transparence sur cette definition est essentielle pour l interpretation comparative avec d autres etudes utilisant des definitions plus larges (EFS toute cause).'
    ]),
    H2('16.5. Perspectives ouvertes par les resultats'),
    para([
      'Plusieurs lignes de recherche se degagent naturellement des resultats ALYCANTE. La validation externe sur la cohorte Lea, pour laquelle les donnees ctDNA pourraient etre extraites a partir de GLIMS aux temps J0 et J14, est la priorite methodologique immediate. L integration des classifications LymphGen realisables sur ctDNA (Moia et coll. 2025) ',
      { cite: [68] },
      ' permettrait une stratification combinee moleculaire et dynamique, potentiellement encore plus discriminante que chaque approche prise isolement. L adoption des criteres uMRD ou mPFS comme criteres de jugement selon le ',
      { i: 'roadmap' },
      ' de Goldstein et coll. ',
      { cite: [91] },
      ' constituerait une translation pratique des resultats academiques vers les essais cliniques regulatoires.'
    ], { first: true }),
    para([
      'Une perspective particulierement riche concerne l articulation avec les anticorps bispecifiques. Pour les patients ALYCANTE en progression apres CAR-T - une proportion non negligeable au vu des courbes de survie - le glofitamab represente desormais la principale option therapeutique (etude LYSA de Cartron 2025) ',
      { cite: [97] },
      '. Le suivi ctDNA pourrait jouer un role majeur a deux niveaux : la detection precoce de la rechute moleculaire post-CAR-T, permettant d initier le bispecifique avant l explosion clinique de la maladie ; et le suivi de la perte d antigene CD20 post-bispecifique, mecanisme de resistance documente par Brooks et coll. (2025) ',
      { cite: [96] },
      ' dans 88 % des biopsies pairees, qui necessitera l elaboration de panels multi-antigeniques (CD19, CD20, CD22).'
    ]),
    para([
      'D autres extensions methodologiques sont envisageables : developpement de scores integratifs combinant ctDNA baseline, CAR-HEMATOTOX, IMPI et caracteristiques cliniques pour la prediction conjointe de l efficacite et de la toxicite ; application des approches JLCM aux donnees TMTV longitudinales en parallele du ctDNA, dans une logique d analyse multivariee de trajectoires ',
      { cite: [55] },
      ' ; et extension au PCNSL par adaptation du suivi au compartiment LCS, comme suggere en section 15.'
    ]),
    H2('16.6. Le message essentiel pour la reunion LYSARC 2026'),
    para([
      'L etude ALYCANTE-biomarqueurs apporte trois contributions originales au paysage scientifique du DLBCL post-CAR-T. Premierement, elle constitue la premiere etude prospective dediee a la population des patients non eligibles a l autogreffe en deuxieme ligne, comblant une lacune importante des essais ZUMA-7 et TRANSFORM ',
      { cite: [45] },
      '. Deuxiemement, elle introduit dans ce contexte une methodologie statistique novatrice - les modeles a classes latentes joints - dont l application au suivi ctDNA dans le DLBCL est, a notre connaissance, inedite. Troisiemement, elle apporte un element empirique fort en faveur de la superiorite predictive de la dynamique moleculaire precoce (delta ctDNA J14) sur l imagerie metabolique tardive (CMR PET M3), justifiant le developpement d outils de stratification ctDNA-bases en pratique clinique routiniere.'
    ], { first: true }),
    para([
      'La validation externe sur la cohorte CART de Lea (N = 158, log-rank PFS p = 0.95 et OS p = 0.62 contre ALYCANTE) renforce la representativite externe des resultats et autorise leur generalisation prudente. La transition entre l outil de recherche et l outil clinique routinier reste a accomplir, mais ALYCANTE fournit a la fois la preuve de concept methodologique et le materiel pratique - protocole, scripts d analyse reproductibles, comparaison directe avec la reference imagerie - necessaires a cette transition. Le projet illustre ainsi une voie possible pour l integration des biomarqueurs moleculaires dans la prise en charge du DLBCL post-CAR-T, dans une perspective de medecine de precision adaptee a la population fragile.'
    ])
  ];
}

function buildBibliography() {
  const out = [H1('Bibliographie (120 references PubMed verifiees)')];
  out.push(para([
    'L ensemble des references suivantes a ete identifie et verifie par interrogations API PubMed (NCBI E-utilities). Chaque entree comporte le PMID et le DOI permettant l acces direct aux articles. La numerotation est continue : les references 1 a 93 correspondent a la premiere phase de recherche thematique, 94 a 112 aux thematiques complementaires (anticorps bispecifiques, complications immunologiques post-CAR-T, meta-analyses), et 113 a 120 aux sections specialisees (essai JULIET, comparaison detaillee des trois produits CAR-T, PCNSL et liquid biopsy du LCS).'
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

const commonHeader = new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: 'Revue ALYCANTE v4 - LYSARC 2026', size: 18, color: '7F7F7F' })] })] });
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
      margin: { top: 1100, right: 1300, bottom: 1100, left: 1300 }
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
      margin: { top: 1100, right: 720, bottom: 1100, left: 720 }
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
      margin: { top: 1100, right: 1300, bottom: 1100, left: 1300 }
    }
  },
  headers: { default: commonHeader },
  footers: { default: commonFooter },
  children: portraitContent15plus
};

const doc = new Document({
  creator: 'Service Immunologie Biologique AP-HP - assistance Claude',
  title: 'Revue ALYCANTE v4 - LYSARC 2026',
  description: 'Revue analytique ctDNA DLBCL CAR-T bispecifiques PCNSL JLCM',
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
  sections: [portraitSection1, landscapeSection, portraitSection2]
});

Packer.toBuffer(doc).then(buf => {
  const outPath = process.argv[2] || 'revue_alycante_v4.docx';
  fs.writeFileSync(outPath, buf);
  console.log('Wrote:', outPath, 'size:', buf.length, 'bytes');
});
