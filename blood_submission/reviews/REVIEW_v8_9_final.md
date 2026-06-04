# REVIEW — v8.9 → v8.9 final (28 May 2026)

Two corrections + one bibliography clean-up + one infrastructure improvement, all applied on the existing v8.9 manuscript. Version number unchanged (the substance is identical, the form is fixed).

## 1. Arithmetic fix — 25 → 26 EFS events

**Bug.** Two contradictory statements coexisted in v8.9:
- §107 Methods + §137 Results: *"22/22 EFS events high-risk vs 4/22 low-risk"* → 26 total
- §141 Discussion + §175 Limitation 2: *"n = 25 EFS events in 44 patients"*

**Diagnosis.** Empirical recount from `master_dataset.csv` × `jlcm_predict_j14.csv`:
- 22 high-risk × 22 events = 22
- 22 low-risk × 4 events (patients 15020101241003, 15020101371004, 15020101371005, 15020101871006; late EFS events at 537, 844, 1080, 556 days)
- **Total : 26 EFS events / n=44 ✓**

The 25 was the stale number, the 26 the correct one.

**Fix.** Replaced `25 events` → `26 events` in:
- `Blood_article_ALYCANTE_v8_9.md` × 2 (Discussion, Limitation)
- `59_build_blood_article_v8_9.py` × 4 (hardcoded captions for SuppFig S2, S5; SuppTable S2, S4)

**Verified.** Final docx contains `25 events` = 0 occurrences, `26 events` = 1 (main) + 4 (supp).

## 2. Citation-order renumbering (Blood style)

**Bug.** Blood uses citation-order numbering (references appear in the order they are first cited). The v8.9 bibliography had been added to over many revisions without renumbering. Concretely:
- Meriranta et al. cited in Introduction (early), numbered 40
- Alig et al. cited in Discussion (last), numbered 26
- Schoenfeld 1982 cited in Methods (mid), numbered 49
- Many other inversions (~10 total documented)

**Fix.** Wrote a Python script (`renumber_refs.py`) that:
1. Parses every `^N^` or `^N,M^` or `^N-M^` citation in the body in textual order
2. Builds OLD→NEW map preserving the order of first appearance
3. Rewrites all in-text citations with the new numbers
4. Rewrites the bibliography in the new order

Result: bibliography now monotonic 1→31. Body and bibliography internally consistent.

Selected OLD→NEW remapping:
| Old | New | Reference |
|---|---|---|
| 40 | 13 | Meriranta L. *Blood* 2022 |
| 13 | 25 | Roschewski M. *Lancet Oncol* 2015 |
| 26 | 29 | Alig SK. *Nature* 2024 |
| 43 | 20 | Firth D. *Biometrika* 1993 |
| 44 | 21 | Heinze-Schemper. *Biometrics* 2001 |
| 49 | 23 | Schoenfeld D. *Biometrika* 1982 |
| 21 | 15 | Stepan L. *Blood* 2026 (TRANSFORM) |
| 32 | 19 | Cheson BD. *J Clin Oncol* 2014 (Lugano) |

## 3. Bibliography hygiene — removed 19 orphan references

**Bug detected during renumbering.** The bibliography listed 50 references but only **31** were ever cited in the body (or in supplemental superscript runs). The 19 remaining were "orphan" — present in the list but never referred to.

Detected via a complete extraction across:
- Main MD body (`^N^` patterns)
- Supplemental docx (superscript runs in paragraphs + tables)
- Search for author cues (Sehgal/PILOT, Wright/LymphGen, Steyerberg, etc.) in supplemental text

**Orphan refs removed (19):**
22 (Vercellino predictive), 25 (Chong pembrolizumab), 27 (Claudel FL), 28 (Sehgal PILOT), 29 (Westin ZUMA-7 update), 30 (Kamdar TRANSFORM primary), 31 (Sehn DLBCL), 33 (Boellaard FDG-PET), 34 (Meignan FL MTV), 35 (Scherer ctDNA), 36 (Kurtz CAPP-Seq enhanced), 37 (Roschewski review), 38 (Cherng review), 39 (Wright LymphGen), 45 (Steyerberg prediction), 46 (Schemper follow-up), 47 (Charton QoL), 48 (Locke ZUMA-1 5y), 50 (Barrington imaging).

**Result.** Bibliography reduced from 50 → 31 entries, all cited.

**Rationale.** Blood Technical Review systematically deletes uncited references before publication. Better to clean now than to be edited.

## 4. Infrastructure improvement — auto-detect `revue_litterature/`

**Bug.** The build script `59_build_blood_article_v8_9.py` only copied output to `revue_litterature/` if the environment variable `BLOOD_NAS_REV_LIT` was set. The result: after several rebuilds today, `blood_article_package/output/Blood_article_v8_9.docx` was up to date but `revue_litterature/Blood_article_ALYCANTE_v8_9.docx` was still the morning version.

**Fix.** Modified path resolution at lines 67–88:
```python
_sibling_revue = PKG_DIR.parent / "revue_litterature"  # auto-detect
if _nas_md_env:
    _rev_lit_dir = Path(_nas_md_env)
elif _sibling_revue.exists():
    _rev_lit_dir = _sibling_revue
else:
    _rev_lit_dir = None
```
Now both `output/blood_article_package/output/` and `output/revue_litterature/` are kept synchronous on every rebuild.

## 5. Repository cleanup

Archived ~200 obsolete files into `output/archive/` subfolders :
- `blood_versions/` — 30+ Blood manuscript v2..v8.8 (md + docx + supplemental)
- `revue_lit_versions/` — 8 ALYCANTE_revue_litterature_v1..v8
- `intro_drafts/` — Blood_introduction draft files
- `planstat_versions/` — V18–V43 (keep V44 active)
- `legacy_build_scripts/` — 17 build scripts (40_..58_, including non-v8 helpers)
- `blood_review_reports/` — 10 historical REVIEW_v*_to_v*.md
- `matching_lea_debug/` — May 11–12 cohort-matching debug CSVs/PNGs
- `revue_lit_intermediate/` — 17 intermediate review markdown drafts + critique iterations
- `obsolete_top_level/` — 18 May 11–12 debug artifacts (LEA JLCM CSVs, audit reports)

Also removed: 56 `Thumbs.db`/`__pycache__`/temp scripts.

**Resulting structure (current state):**
```
output/
├── archive/                              221 MB — historical artifacts
├── pdfs_revue_litterature/               201 MB — PDF references
├── blood_article_package/                 18 MB — ★ canonical, autonomous submission ★
│   ├── README.md
│   ├── REVIEW_v8_8_to_v8_9_package.md
│   ├── REVIEW_v8_9_final.md              ← this file
│   ├── input/                            (15 patient + 8 derived CSVs)
│   ├── output/
│   │   ├── Blood_article_v8_9.docx       (1.05 MB, 28/05 11:28)
│   │   ├── Blood_article_v8_9.md
│   │   ├── Blood_article_v8_9_supplemental.docx (2.81 MB)
│   │   ├── figures/                      (24 PNG/PDF — Fig1–5 + SuppFig1–10 + Visual abstract)
│   │   └── tables/                       (30 CSVs — Table 1, Table 2, SuppTables S1–S19)
│   └── scripts/                          (50 active scripts, builds + analyses + figures)
├── figures/                               36 MB — current production figures
├── revue_litterature/                    3.9 MB — Blood_article_ALYCANTE_v8_9.{docx,md,_supp.docx} only
├── scripts_figures/                      12 MB — legacy shared scripts (kept as historical fallback)
└── PlanStat_ALYCANTE_V44.{docx,md}       — current PlanStat
```

## Final verification (28 May 2026, 11:28)

All four manuscript files identical and synchronized:

| Path | Size | Mtime |
|---|---|---|
| `blood_article_package/output/Blood_article_v8_9.docx` | 1.05 MB | 28/05 11:28 |
| `blood_article_package/output/Blood_article_v8_9_supplemental.docx` | 2.81 MB | 28/05 11:28 |
| `revue_litterature/Blood_article_ALYCANTE_v8_9.docx` | 1.05 MB | 28/05 11:28 |
| `revue_litterature/Blood_article_ALYCANTE_v8_9_supplemental.docx` | 2.81 MB | 28/05 11:28 |

Eleven independent checks all pass (citations 1–31 in superscript, no out-of-range >31, bibliography = 31 entries, `25 events` = 0, `26 events` = 1 main + 4 supp, `Cogliati` = 0). The package is ready for *Blood* submission.
