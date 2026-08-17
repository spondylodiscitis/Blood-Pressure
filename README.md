# Blood Pressure Cancer Classification Project

## Overview

This repository contains the data description and preprocessing framework for a translational blood-pressure research project.

The project has two connected stages:

1. **Human EHR study**
   - Build a cancer (CA) vs non-cancer (NCA) classifier from longitudinal hospital blood-pressure data.
   - Control or document major clinical confounders such as surgery and medications that can influence blood pressure.
   - Learn blood-pressure representations using patient-level data without patient leakage.

2. **Mouse blood-pressure study**
   - Apply the final blood-pressure analysis/classification framework to mouse experiments.
   - Classify individual animals as cancer vs non-cancer from longitudinal systolic/diastolic blood-pressure measurements.
   - The mouse experiment is the final translational target of the project.

---

## Repository Structure

```text
bp_project/
├── README.md
├── docs/
│   ├── STUDY_DESIGN.md
│   ├── PREPROCESSING.md
│   └── HANDOVER.md
├── src/
│   ├── preprocess_hospital.py
│   └── preprocess_mouse.py
└── config/
    └── mouse_group_mapping.yaml
```

---

# 1. Human EHR Dataset

Human data are separated into **Cancer (CA)** and **Non-Cancer (NCA)** cohorts.

All tables are linked using the pseudonymized patient identifier:

```text
연구번호
R000000001
R000000002
...
```

### Main table families

| Prefix | Domain | Main content |
|---|---|---|
| `*_cohort_*` | Cohort | sex, birth information, follow-up |
| `*_inform_*` | Encounter | admission/discharge and department |
| `*_dia_*` | Diagnosis | diagnosis code/name/date |
| `*_sur_*` | Surgery | operation date, procedure, operative record |
| `*_drug_*` | Medication | ingredient, dose, administration date, route |
| `*_vs_*` | Vital signs | BP, ABP, pulse, respiration, temperature |

Files may be split into many physical CSV shards:

```text
ca_drug_1.csv
ca_drug_2.csv
...
ca_drug_60.csv
```

The number of shards is **not fixed**.

A patient may occur in more than one shard. Therefore, physical files must first be concatenated into one logical table before patient-level preprocessing.

```text
ca_drug_1 ─┐
ca_drug_2 ─┤
ca_drug_3 ─┤
    ...    ├──> CA medication logical table
ca_drug_N ─┘
```

**Never perform train/validation/test splitting by CSV file number.**

---

## Vital-sign variables

Typical variables include:

- `연구번호`
- `기록일자`
- `기록시간`
- `ABP(S)`, `ABP(D)`, `ABP(M)`
- `BP(S)`, `BP(D)`, `BP(M)`
- `맥박`
- `호흡`
- `체온`
- corresponding `_클린징` variables

The primary non-invasive blood-pressure variables are:

- systolic BP: `BP(S)_클린징`
- diastolic BP: `BP(D)_클린징`

ABP should be treated separately because invasive arterial monitoring is much sparser and clinically selective.

---

## Medication variables

Medication data contain both prescription and administration information.

Typical fields:

- `연구번호`
- `진료일자`
- `진료구분`
- `처방일자`
- `진료과`
- `처방코드`
- `성분명`
- `처방명`
- `처방한글명`
- `SELF약여부`
- `1일기준총용량`
- `용량단위`
- `1일기준총수량`
- `수량단위`
- `처방횟수`
- `처방일수`
- `실시일자`
- `1회투여수량`
- `1일투여횟수`
- `투여기간`
- `투약방식`
- `투약방식(한글명)`

Medication administration time is not consistently available. Therefore, medication exposure should generally be handled at the **date level**, not as an exact hour-level event.

See `docs/PREPROCESSING.md`.

---

# 2. Mouse Dataset

Input example:

```text
mouse 혈압 결과.xlsx
```

The workbook contains date-based sheets such as:

```text
11.27
11.28
...
12.17
```

Each measurement block contains:

- experimental group
- animal number
- three systolic measurements
- systolic mean
- three diastolic measurements
- diastolic mean

Example groups observed in the workbook include:

| Group | Preliminary binary label | Interpretation |
|---|---:|---|
| `control` | 0 | Non-cancer control |
| `MC38` | 1 | Tumor-model group |
| `ID8 s.c.` | 1 | ID8 tumor model, subcutaneous route |
| `ID8 i.p.` | 1 | ID8 tumor model, intraperitoneal route |
| `CFPAC` | 1* | Cancer-cell-line group |
| `CFPAC A1` | 1* | Experimental CFPAC subgroup |
| `CFPAC A2` | 1* | Experimental CFPAC subgroup |

`*` The exact experimental meaning of `A1` and `A2` must be confirmed against the animal protocol before publication or final analysis. They should not be reinterpreted from the spreadsheet name alone.

The binary task is:

```text
0 = Non-cancer
1 = Cancer / tumor-bearing
```

For modeling, preserve the original `group` column in addition to the binary label so that cancer models are not unintentionally mixed without traceability.

---

# 3. Current Modeling Direction

Recommended human pipeline:

```text
Raw CA/NCA EHR
      ↓
Merge all shards by domain
      ↓
Patient-level timeline reconstruction
      ↓
Surgery / medication handling
      ↓
7-day BP windows
      ↓
Day / Night aggregation
      ↓
Age + Sex
      ↓
Patient-level Train / Validation / Test
      ↓
Baseline ML → BiLSTM + Attention
      ↓
CA vs NCA prediction
```

Final translational pipeline:

```text
Human BP representation / modeling strategy
                   ↓
        Mouse BP preprocessing
                   ↓
       Animal-level time series
                   ↓
     Cancer vs Non-cancer mouse
```

---

# 4. Important Rules

1. Concatenate **all shards** before patient-level processing.
2. The same patient can span `*_1.csv`, `*_2.csv`, etc.
3. Sort by patient identifier and clinical date/time after concatenation.
4. Check duplicates after concatenation.
5. Never split the same patient across train and test.
6. Do not use accuracy alone under class imbalance.
7. Report AUROC, balanced accuracy, sensitivity, specificity, F1 and confusion matrix.
8. Missingness itself can become a model signal; do not blindly replace missing BP with zero.
9. Surgery and BP-altering medication may create major hemodynamic confounding.
10. Preserve the original mouse experimental group even when converting to binary CA/NCA labels.

Detailed design and preprocessing decisions are documented under `docs/`.

---

# Handover / Reproducibility Files

Additional documentation for project continuation:

| File | Purpose |
|---|---|
| `docs/STUDY_DESIGN.md` | Research objective, human→mouse translational design, confounders, modeling strategy |
| `docs/PREPROCESSING.md` | Detailed preprocessing specification |
| `docs/DATA_DICTIONARY.md` | Variable-level descriptions for hospital and mouse data |
| `docs/QC_CHECKLIST.md` | Data and modeling quality-control checklist |
| `docs/EXPERIMENT_LOG.md` | Historical model results, failures, and experiment template |
| `docs/RUNBOOK.md` | Step-by-step execution order for a new researcher |
| `docs/TODO.md` | Remaining research tasks in priority order |
| `docs/HANDOVER.md` | Practical handover notes |

Configuration:

| File | Purpose |
|---|---|
| `config/config.yaml` | Paths, window size, day/night settings, split seed, censoring rules |
| `config/mouse_group_mapping.yaml` | Mouse original-group → binary-label mapping |
| `config/BP_IMPACTING_DRUGS.csv` | Reviewable dictionary of medication ingredients with potential BP effects |

Pipeline scripts:

```text
src/
├── 01_inventory.py
├── 02_merge_hospital.py
├── 03_qc_human.py
├── 04_build_windows.py
├── 05_train_baseline.py
├── 06_preprocess_mouse.py
├── 07_train_mouse.py
├── preprocess_hospital.py
└── preprocess_mouse.py
```

The numbered scripts are intended to be executed in order.  
See `docs/RUNBOOK.md` before running the pipeline.

