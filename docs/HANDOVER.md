# Project Handover Notes

## 프로젝트 한 줄 설명

병원 EHR의 longitudinal blood-pressure data에서 cancer/non-cancer 차이를 탐색하고 모델링한 뒤, 최종적으로 mouse longitudinal BP를 이용해 **mouse cancer vs non-cancer classification**을 수행하는 프로젝트.

---

## 후속 연구자가 가장 먼저 해야 할 일

### 1. Raw file inventory

CA/NCA 각각 실제 파일 수를 확인한다.

절대 아래처럼 가정하지 말 것:

```python
for i in range(1, 61):
    ...
```

대신:

```python
glob("ca_drug_*.csv")
```

사용.

이유:
- 60개보다 적거나 많을 수 있음.
- 파일 번호가 중간에 빠질 수 있음.
- 동일 환자가 여러 shard에 걸쳐 존재할 수 있음.

---

### 2. Logical table 생성

각 domain별로 전체 shard를 합친다.

예:

```text
CA
├── cohort
├── inform
├── dia
├── sur
├── drug
└── vs

NCA
├── cohort
├── inform
├── dia
├── sur
├── drug
└── vs
```

`patient_id`별 chronological sorting까지 한 결과를 intermediate dataset으로 저장하는 것을 권장.

---

### 3. QC report 생성

최소 확인 항목:

- shard 개수
- total rows
- unique patients
- duplicate rows
- patient overlap between shards
- date range
- missing BP percentage
- CA/NCA patient counts
- measurements per patient
- admission duration
- medication-exposed patient count
- surgery patient count

---

## 지금까지 발생했던 핵심 문제

### Severe class imbalance

Random Forest에서 accuracy가 높지만 balanced accuracy가 0.5 수준으로 나온 적이 있음.

즉 majority-class prediction 가능성이 높았음.

### Overfitting

deep-learning validation AUC가 대략 0.7까지 나온 실험이 있었지만 train/validation gap이 컸음.

### Sparse hourly series

24 × 7 = 168 sequence는 임상 측정 특성상 너무 sparse했음.

그래서 day/night aggregation 방향으로 변경.

### Confounding

모델이 cancer physiology 대신 아래를 학습할 수 있음:

- surgery
- medications
- ICU care
- measurement frequency
- admission characteristics

---

## 현재 추천 baseline

Human:

1. patient-level QC
2. 7-day day/night features
3. Logistic Regression
4. Random Forest / XGBoost
5. BiLSTM + Attention

Mouse:

1. workbook tidy conversion
2. animal trajectory plot
3. group QC
4. animal-level statistical features
5. Logistic Regression
6. regularized/tree baseline
7. sample size가 충분할 때 temporal model

---

## Mouse groups

현재 workbook에서 확인한 그룹:

```text
control
MC38
ID8 s.c.
ID8 i.p.
CFPAC
CFPAC A1
CFPAC A2
```

현재 binary 작업 mapping:

```text
control  -> 0

MC38     -> 1
ID8 s.c. -> 1
ID8 i.p. -> 1
CFPAC    -> 1
CFPAC A1 -> 1
CFPAC A2 -> 1
```

단, `CFPAC A1/A2`가 실제로 어떤 intervention/treatment subgroup인지 animal experimental protocol을 확인하고 기록할 것.

원래 group label은 절대로 삭제하지 말 것.

---

## Mouse old experiment note

과거 mouse classification 실험에서:

```text
TN = 0
FP = 4
FN = 0
TP = 12
AUC ≈ 0.583
Accuracy = 0.75
```

수준의 결과가 있었고 사실상 모든 sample을 cancer로 예측하는 현상이 관찰되었다.

따라서 기존 결과를 성능 기준으로 사용하지 말고, 새 preprocessing 이후 baseline부터 다시 평가하는 것이 좋다.

---

## 절대 하지 말아야 할 것

- CSV shard별 train/test split
- 같은 patient를 train/test에 동시에 포함
- 같은 mouse를 train/test에 동시에 포함
- missing BP를 아무 검토 없이 0으로 대체
- accuracy 하나만으로 성능 판단
- medication administration time을 없는 상태에서 임의 생성
- mouse `Animal #`만 이용해 ID 생성
- cancer subgroup 정보를 binary label로 덮어쓰기
- 실험 결과를 보고 preprocessing threshold를 반복 변경

---

## 최종 목표 output

Human 단계:

```text
processed_human_windows.parquet
human_feature_table.csv
human_split.json
```

Mouse 단계:

```text
mouse_tidy.csv
mouse_features.csv
mouse_predictions.csv
mouse_metrics.json
```

최종적으로 각 mouse에 대해:

```text
animal_id
original_group
true_label
predicted_probability
predicted_label
```

형태의 결과를 남긴다.
