# Study Design

## 1. 연구의 최종 목적

본 프로젝트의 최종 목적은 **혈압 시계열을 이용하여 mouse 개체가 cancer group인지 non-cancer group인지 분류하는 것**이다.

병원 환자 데이터는 단순한 별도 연구가 아니라, 사람의 실제 임상 EHR에서 암/비암에 연관된 혈압 시계열 표현과 분석 방법을 개발하고 검증하기 위한 선행 단계로 사용한다.

전체 연구 흐름은 다음과 같다.

```text
Human CA / NCA EHR
        ↓
혈압 시계열 전처리 방법 확립
        ↓
CA vs NCA 패턴 탐색
        ↓
시계열 모델 개발 및 오류 분석
        ↓
Mouse longitudinal BP
        ↓
Cancer vs Non-cancer mouse classification
```

---

## 2. Human Study

### Primary question

입원 중 반복 측정된 혈압의 절대값, 변동성, 일중 패턴 및 시간적 변화가 cancer 환자와 non-cancer 환자 사이에서 구분 가능한 신호를 제공하는가?

### Human labels

- `CA`: cancer cohort
- `NCA`: non-cancer cohort

진단 데이터와 cohort 정의는 별도 원자료 정의를 따른다.

### Main input

- longitudinal systolic/diastolic BP
- optional pulse / other vital signs
- static covariates: age, sex

### Major confounders

- surgery
- antihypertensive drugs
- vasopressors/inotropes
- diuretics
- sedatives/analgesics
- fluid administration
- steroid and other potentially hemodynamic medications
- ICU/ward workflow
- measurement frequency

특히 모델이 암의 생리학적 신호가 아니라 `치료 강도`, `중환자 관리`, `혈압 측정 빈도`를 학습하지 않는지 계속 확인해야 한다.

---

## 3. Human Temporal Design

### Initial approach

7 days × 24 hours = 168 hourly slots.

문제점:

- 임상 BP가 정시 측정이 아니므로 missingness가 매우 큼.
- interpolation/imputation의 영향이 커질 수 있음.
- 측정 빈도 자체가 label proxy가 될 수 있음.

### Current preferred approach

7-day **Day/Night aggregation**.

Conceptual example:

```text
D1-Day → D1-Night → D2-Day → D2-Night → ... → D7-Night
```

정확한 day/night 시간 경계는 분석 코드에서 하나의 설정값으로 관리해야 하며, 결과를 본 후 임의로 변경해서는 안 된다.

### Minimum density

현재 작업 기준:
- 7-day window 내 최소한 약 2일에 1회 이상의 BP가 존재하는 window를 우선 사용.

최종 논문화 전에는 이 기준을 명시적으로 고정하고 sensitivity analysis를 고려한다.

---

## 4. Surgery Design

Surgery는 큰 혈역학적 변화를 유발하므로 중요 confounder이다.

현재 작업 방향:

- CA: 가능하면 pre-operative BP 중심
- NCA: 표본 부족 문제 때문에 post-operative data를 허용했던 실험이 있음

이 비대칭 규칙은 최종 연구에서 bias가 될 수 있다.

따라서 후속 연구자는 다음 두 분석을 구분하는 것이 좋다.

1. **Strict analysis**: CA/NCA 모두 동일 surgery rule
2. **Exploratory analysis**: 기존의 CA pre-op / NCA post-op 허용 규칙

두 결과가 비슷한지 반드시 확인할 것.

---

## 5. Medication Design

Medication table에는 약물 성분, 용량, 날짜, 투여 방식 등이 포함되지만 일관된 투여 시각은 없다.

따라서:

- `실시일자`를 핵심 exposure date로 사용
- 정확한 hour-level pre/post medication 판정은 하지 않음
- BP-impacting medication을 정의한 뒤 day-level exclusion 또는 censoring 적용

예:

```text
Day 1     Day 2     Day 3       Day 4
 BP        BP       medication   BP
                    ↑
              exposure boundary
```

보수적인 분석에서는 medication exposure 당일부터 이후 BP를 제거할 수 있다.

어떤 약물을 BP-impacting medication으로 정의했는지는 반드시 별도 목록으로 버전 관리할 것.

---

## 6. Split Strategy

가장 중요한 원칙:

**patient-level split**

같은 환자의 여러 7-day window가 서로 다른 split으로 가면 안 된다.

잘못된 예:

```text
Patient A / Window 1 -> train
Patient A / Window 2 -> test
```

올바른 예:

```text
Patient A -> train only
Patient B -> validation only
Patient C -> test only
```

---

## 7. Modeling History

시도한 접근:

- Logistic Regression
- Random Forest
- LSTM + Attention
- GRU-D
- InceptionTime/Fusion
- Self-supervised representation learning
- BiLSTM + Attention

기존 classical feature 실험에서 약 74개의 engineered features를 사용한 적이 있다.

과거 관찰 성능 예:

- Logistic Regression: accuracy 약 0.608, AUROC 약 0.617
- Random Forest: accuracy 약 0.893였으나 balanced accuracy 약 0.50
- Deep-learning validation AUROC는 약 0.7 수준의 실험이 있었으나 overfitting이 큼

따라서 `accuracy` 하나만 보고 모델을 선택하지 말 것.

---

## 8. Mouse Study

### Final prediction task

개별 mouse의 longitudinal blood pressure를 이용하여:

```text
Cancer vs Non-cancer
```

를 예측한다.

### Workbook structure

현재 전달된 workbook은 날짜별 worksheet로 구성되어 있고 한 날짜에 두 measurement block이 존재하는 형태가 확인된다.

각 animal에서 systolic/diastolic을 반복 측정하여 mean을 기록한다.

### Current group interpretation

- `control` → Non-cancer
- `MC38` → Cancer/tumor-model
- `ID8 s.c.` → Cancer/tumor-model
- `ID8 i.p.` → Cancer/tumor-model
- `CFPAC`, `CFPAC A1`, `CFPAC A2` → cancer-related experimental groups로 취급하되 A1/A2의 정확한 실험 의미는 animal protocol 확인 필요

중요:
binary label만 저장하지 말고 반드시 아래 둘을 모두 보존한다.

```text
original_group
binary_label
```

### Mouse ID

`Animal #` 값은 group 내부에서만 유일할 수 있으므로 다음과 같이 composite ID를 만든다.

```text
control_1
MC38_1
ID8_sc_2
ID8_ip_1
...
```

group을 제거하고 Animal #만 ID로 사용하면 서로 다른 그룹의 `Animal # = 1`이 합쳐질 수 있다.

---

## 9. Mouse Modeling Recommendation

mouse sample size가 작으므로 처음부터 큰 neural network를 사용하지 않는다.

우선 순서:

1. 데이터 QC
2. animal별 trajectory visualization
3. cancer/non-cancer SBP/DBP distribution
4. longitudinal feature extraction
5. Logistic Regression
6. Random Forest / regularized tree baseline
7. 필요 시 compact temporal model

추천 feature:

- SBP mean/std/min/max/range
- DBP mean/std/min/max/range
- first-to-last slope
- day-to-day slope
- early vs late BP difference
- systolic/diastolic variability
- pulse pressure = SBP - DBP
- measurement count
- missing rate

sample size가 작기 때문에 animal-level cross-validation 또는 leave-one-animal-out 평가가 더 적합할 수 있다.

---

## 10. Main Scientific Risk

Human model의 성능을 mouse에 그대로 transfer할 수 있다고 가정하면 안 된다.

사람과 mouse는:

- 혈압 scale
- 측정 protocol
- sampling frequency
- 암종
- disease progression
- treatment context

가 다르다.

따라서 human 단계는 **representation/design discovery**, mouse 단계는 **별도의 final classification experiment**로 보는 것이 안전하다.
