# Preprocessing Specification

## 1. 가장 중요한 파일 로딩 규칙

원본 CSV는 여러 shard로 분리될 수 있다.

예:

```text
ca_drug_1.csv
ca_drug_2.csv
...
ca_drug_60.csv
```

파일 수를 `60`으로 hard-code하지 않는다.

항상 glob pattern으로 존재하는 파일을 전부 탐색한다.

```python
ca_drug_*.csv
nca_drug_*.csv
ca_vs_*.csv
nca_vs_*.csv
...
```

### Why?

한 환자의 데이터가 파일 경계를 넘어 이어질 수 있다.

```text
ca_drug_1.csv
  ...
  R000001234

ca_drug_2.csv
  R000001234
  R000001234
  ...
```

따라서 `ca_drug_1.csv`와 `ca_drug_2.csv`를 서로 독립된 환자 집합으로 보면 안 된다.

### Correct order

```text
discover shards
      ↓
read all shards
      ↓
column harmonization
      ↓
concatenate
      ↓
deduplicate
      ↓
sort by patient + date/time
      ↓
patient-level processing
```

---

# 2. Shard Concatenation

`src/preprocess_hospital.py`의 `load_sharded_csv()`를 사용한다.

중요:

- shard 번호는 numeric sort
- source filename/source shard 컬럼을 남길 수 있음
- concatenation 후에만 patient grouping
- duplicate row 수를 로그로 남김

---

# 3. Date Handling

병원 데이터의 날짜는 다음처럼 숫자 또는 문자열로 들어올 수 있다.

```text
20231128
```

다음으로 통일한다.

```text
2023-11-28
```

혈압의 경우 `기록일자 + 기록시간`으로 timestamp를 만든다.

예:

```text
기록일자 = 20231201
기록시간 = 100000
→ 2023-12-01 10:00:00
```

`기록시간`이 없으면 date-level record로 유지한다.

---

# 4. Vital Sign Cleaning

가능하면 원본 변수보다 `_클린징` 컬럼을 우선 사용한다.

추천:

```text
SBP = BP(S)_클린징
DBP = BP(D)_클린징
```

주의:

- missing을 0으로 채우지 않는다.
- 0은 실제 mouse sheet에서 '측정 없음/실패'처럼 보이는 경우도 있으므로 mouse에서도 결측 처리 규칙을 명확히 적용한다.
- physiologic range filter를 새로 적용할 경우 threshold를 코드와 문서에 명시한다.

---

# 5. 7-Day Human Window

기본 window:

```text
7 days
```

긴 입원의 경우 여러 window를 생성할 수 있다.

그러나 모든 window에는 `patient_id`를 유지한다.

split은 window가 생성된 **후에도 patient_id 기준**으로 수행한다.

---

# 6. Day / Night Aggregation

현재 권장 representation.

각 day/night bin에서 다음을 계산할 수 있다.

```text
SBP_mean
SBP_std
SBP_min
SBP_max
DBP_mean
DBP_std
DBP_min
DBP_max
measurement_count
```

day/night 경계는 configuration 값으로 고정한다.

예시일 뿐인 초기 설정:

```text
Day   : 06:00–17:59
Night : 18:00–05:59
```

최종 분석 전에 임상팀과 확정할 것.

---

# 7. Surgery

수술 날짜를 patient timeline에 merge한다.

필요 변수 예:

```text
연구번호
수술일자
수술시작일시
수술종료일시
```

수술 관련 exclusion은 study design에 따라 적용한다.

수술이 없는 환자는 그대로 유지한다.

---

# 8. Medication

`drug` shard를 모두 먼저 concatenate한다.

핵심 필드:

```text
연구번호
성분명
처방일자
실시일자
1일기준총용량
용량단위
1일투여횟수
투여기간
투약방식
```

### Important limitation

일관된 medication administration time이 없으므로 정확한 hourly pre/post exposure를 생성하지 않는다.

### Recommended method

1. BP-impacting ingredient dictionary 작성
2. `성분명` normalization
3. 대상 약물 exposure date 추출
4. patient별 earliest exposure date 계산
5. 분석 설계에 따라 exposure 당일/이후 BP censoring

---

# 9. Diagnosis

CA/NCA cohort label validation에 사용한다.

과거 작업에서는 cancer diagnosis 데이터에서 cancer code 규칙을 확인하고 잘못 포함된 환자를 제외/재분류하는 작업도 고려했다.

최종 사용 규칙은 별도 versioned function으로 구현하고 raw data를 직접 수정하지 않는다.

---

# 10. Mouse Excel Preprocessing

현재 workbook은 일반적인 tidy table이 아니다.

특징:

- 날짜별 sheet
- 한 sheet에 measurement block이 반복될 수 있음
- group 이름은 첫 animal row에만 있고 다음 row는 blank
- `Animal #`은 group 내부 번호
- systolic 3회 측정 + mean
- diastolic 3회 측정 + mean
- `Mean`, `SD` summary row 존재
- 측정되지 않은 cancer group에서 0 값이 보이는 날짜가 있음

따라서 parsing 후 다음 tidy format으로 변환한다.

```text
date
time
group
animal_no
animal_id
sbp_1
sbp_2
sbp_3
sbp_mean
dbp_1
dbp_2
dbp_3
dbp_mean
label
source_sheet
```

### Mouse ID

반드시:

```python
animal_id = normalized_group + "_" + animal_no
```

### Zero handling

SBP/DBP 반복값이 모두 0인 row는 생리적 BP로 사용하지 않고 결측 measurement로 처리하는 것을 기본으로 한다.

단, 원 실험자가 `0`을 실제 관측값으로 사용한 것이 아님을 최종 확인할 것.

### Binary labels

mapping은 `config/mouse_group_mapping.yaml`에서 관리한다.

코드에 label을 여러 군데 hard-code하지 않는다.

---

# 11. Mouse Feature Dataset

tidy time-series에서 animal-level feature table을 생성한다.

예:

```text
animal_id
group
label
n_measurements
sbp_mean
sbp_std
sbp_min
sbp_max
sbp_slope
dbp_mean
dbp_std
dbp_min
dbp_max
dbp_slope
pulse_pressure_mean
...
```

모델 split도 반드시 **animal_id 단위**이다.

---

# 12. Reproducibility

모든 preprocessing 실행 시 다음을 저장한다.

- input file list
- file count
- total rows before/after concat
- duplicate count
- unique patient/animal count
- exclusion count + reason
- preprocessing parameters
- random seed
