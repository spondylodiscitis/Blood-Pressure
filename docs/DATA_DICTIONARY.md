# Data Dictionary

This document summarizes the major variables used in the blood-pressure project.

---

# 1. Common identifier

| Variable | Meaning | Notes |
|---|---|---|
| `연구번호` | Pseudonymized research patient ID | Primary key used to link hospital tables |

Example:

```text
R000000001
R000000002
```

A single patient may occur in multiple physical CSV shards.  
Always concatenate all shards before grouping by `연구번호`.

---

# 2. Cohort Table

Typical file pattern:

```text
ca_cohort_*.csv
nca_cohort_*.csv
```

| Variable | Meaning | Use |
|---|---|---|
| `연구번호` | Research patient ID | Required |
| `생년월` | Birth date/month | Used to derive age when appropriate |
| `성별` | Sex | Static feature |
| `사망여부` | Mortality status | Descriptive/QC |
| `사망일자` | Death date | Descriptive/QC |
| `최종추적일자` | Last follow-up date | Descriptive/QC |
| `주소` | Residential region | Usually not used for modeling |

---

# 3. Admission / Encounter Table

Typical file pattern:

```text
ca_inform_*.csv
nca_inform_*.csv
```

| Variable | Meaning | Use |
|---|---|---|
| `연구번호` | Research patient ID | Required |
| `진료과` | Clinical department | Descriptive / possible confounder |
| `퇴원과` | Department at discharge | Descriptive |
| `입원(진료)일` | Admission / encounter date | Episode construction |
| `퇴원일` | Discharge date | Episode construction |
| `진료구분(I/O/E)` | Inpatient / outpatient / emergency classification | Episode QC |
| `접수구분` | Visit classification | Optional |

---

# 4. Diagnosis Table

Typical file pattern:

```text
ca_dia_*.csv
nca_dia_*.csv
```

| Variable | Meaning | Use |
|---|---|---|
| `연구번호` | Research patient ID | Required |
| `nU최초진단나이` | Age at first diagnosis | Optional covariate / QC |
| `진료과` | Department | Descriptive |
| `진단코드` | Diagnosis code | Cohort verification / comorbidity |
| `진단명` | Diagnosis name | Cohort verification |
| `진단한글명` | Korean diagnosis name | Cohort verification |
| `진단일자` | Diagnosis date | Temporal alignment |
| `nU최초진단일자` | First diagnosis date | Temporal alignment |
| `진단상태(확정/Rule Out)` | Confirmed / rule-out | Cohort QC |
| `진단분류(주진단/부진단)` | Primary / secondary diagnosis | Cohort QC |

Important:
- Do not infer CA/NCA solely from file name if diagnosis rules indicate otherwise.
- Keep cohort-label validation as a reproducible function.

---

# 5. Surgery Table

Typical file pattern:

```text
ca_sur_*.csv
nca_sur_*.csv
```

| Variable | Meaning | Use |
|---|---|---|
| `연구번호` | Research patient ID | Required |
| `수술일자` | Surgery date | Main surgery event |
| `수술명` | Procedure name | Descriptive |
| `수술코드` | Procedure code | Descriptive |
| `수술전진단` | Pre-operative diagnosis | Optional |
| `수술후진단` | Post-operative diagnosis | Optional |
| `수술시작일시` | Surgery start timestamp | Use when reliable |
| `수술종료일시` | Surgery end timestamp | Use when reliable |
| `수술기록` | Operative record | Not used directly for baseline modeling |

Surgery is a major hemodynamic confounder.

---

# 6. Medication Table

Typical file pattern:

```text
ca_drug_*.csv
nca_drug_*.csv
```

The number of files is not fixed.

Example:

```text
ca_drug_1.csv
ca_drug_2.csv
...
ca_drug_60.csv
```

A patient can continue across shard boundaries.

| Variable | Meaning | Use |
|---|---|---|
| `연구번호` | Research patient ID | Required |
| `진료일자` | Encounter date | Context |
| `진료구분` | Encounter type | Context |
| `처방일자` | Prescription date | Secondary exposure date |
| `진료과` | Department | Context |
| `처방코드` | Prescription code | Drug identification |
| `성분명` | Active ingredient | Primary field for BP-impacting drug matching |
| `처방명` | Prescription name | Drug identification |
| `처방한글명` | Korean medication name | Drug identification |
| `SELF약여부` | Self-medication flag | Optional |
| `1일기준총용량` | Total daily dose | Dose information |
| `용량단위` | Dose unit | Dose information |
| `1일기준총수량` | Total daily quantity | Dose information |
| `수량단위` | Quantity unit | Dose information |
| `처방횟수` | Prescription/admin frequency | Dose information |
| `처방일수` | Number of prescription days | Exposure duration |
| `실시일자` | Actual administration date | Preferred exposure date |
| `1회투여수량` | Quantity per administration | Dose information |
| `1일투여횟수` | Administrations per day | Dose information |
| `투여기간` | Administration duration | Exposure duration |
| `투약방식` | Route code | Administration route |
| `투약방식(한글명)` | Route description | Administration route |

Important limitation:
- Exact administration time is not consistently available.
- Therefore, medication censoring should generally be date-level.

---

# 7. Vital Sign Table

Typical file pattern:

```text
ca_vs_*.csv
nca_vs_*.csv
```

| Variable | Meaning | Use |
|---|---|---|
| `연구번호` | Research patient ID | Required |
| `기록일자` | Measurement date | Timestamp |
| `기록시간` | Measurement time | Timestamp |
| `ABP(S)` | Invasive systolic arterial BP | Secondary |
| `ABP(D)` | Invasive diastolic arterial BP | Secondary |
| `ABP(M)` | Invasive mean arterial BP | Secondary |
| `BP(S)` | Non-invasive systolic BP | Raw main variable |
| `BP(D)` | Non-invasive diastolic BP | Raw main variable |
| `BP(M)` | Non-invasive mean BP | Optional |
| `맥박` | Pulse | Optional |
| `호흡` | Respiratory rate | Optional |
| `체온` | Temperature | Optional |

Cleaned columns:

```text
ABP(S)_클린징
ABP(D)_클린징
ABP(M)_클린징
BP(S)_클린징
BP(D)_클린징
BP(M)_클린징
맥박_클린징
호흡_클린징
체온_클린징
```

Preferred baseline variables:

```text
SBP = BP(S)_클린징
DBP = BP(D)_클린징
```

Do not replace missing BP with zero.

---

# 8. Mouse Workbook

Input example:

```text
mouse 혈압 결과.xlsx
```

Observed group names include:

```text
control
MC38
ID8 s.c.
ID8 i.p.
CFPAC
CFPAC A1
CFPAC A2
```

Expected tidy output:

| Variable | Meaning |
|---|---|
| `date` | Measurement date |
| `time` | Measurement time/block |
| `group` | Original experimental group |
| `animal_no` | Animal number within group |
| `animal_id` | Composite unique animal ID |
| `sbp_1` | Systolic replicate 1 |
| `sbp_2` | Systolic replicate 2 |
| `sbp_3` | Systolic replicate 3 |
| `sbp_mean` | Mean systolic BP |
| `dbp_1` | Diastolic replicate 1 |
| `dbp_2` | Diastolic replicate 2 |
| `dbp_3` | Diastolic replicate 3 |
| `dbp_mean` | Mean diastolic BP |
| `label` | Binary CA/NCA label |
| `source_sheet` | Original worksheet |

Never use `Animal #` alone as a globally unique identifier.
