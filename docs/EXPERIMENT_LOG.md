# Experiment Log

This file records the major experiments performed before handover.

The values below are historical observations and should not be treated as final publication results.

---

## Human CA vs NCA

### Classical Feature Dataset

Historical engineered-feature dataset:

```text
approximately 18,932 rows × 74 features
```

Typical features included descriptive BP statistics and variability measures.

### Logistic Regression

Historical result:

```text
Accuracy ≈ 0.608
AUROC   ≈ 0.617
```

Interpretation:
- weak discrimination
- useful as a simple baseline

### Random Forest

Historical result:

```text
Accuracy          ≈ 0.893
Balanced Accuracy ≈ 0.500
```

Interpretation:
- apparently high accuracy was misleading
- model likely favored the majority class
- demonstrates severe class imbalance risk

---

## Deep Learning History

Models attempted:

- LSTM + Attention
- GRU-D
- InceptionTime / Fusion
- Self-Supervised Learning encoder/projector
- BiLSTM + Attention

Observed validation AUROC in some experiments:

```text
~0.7
```

Major issue:

```text
Severe overfitting
```

Likely contributors:

1. class imbalance
2. sparse irregular BP
3. high-dimensional 168-step representation
4. surgery-related hemodynamic changes
5. medication-related hemodynamic changes
6. care-setting / measurement-frequency leakage
7. hospitalization pattern differences

---

## Representation Change

Initial:

```text
7 days × 24 hours = 168 time steps
```

Problem:
- high missingness
- potential for missingness-pattern learning

Current preferred representation:

```text
7 days × Day/Night = 14 temporal bins
```

Expected advantages:
- lower missingness
- lower model complexity
- preserves basic circadian BP pattern
- easier interpretation

---

## Mouse Historical Experiment

Historical result:

```text
TN = 0
FP = 4
FN = 0
TP = 12

Accuracy ≈ 0.75
AUROC   ≈ 0.583
```

Interpretation:
- model predicted essentially all mice as cancer
- apparent accuracy was driven by class imbalance
- this result should not be used as the final benchmark

Recommended action:
- rebuild mouse dataset using animal-level preprocessing
- evaluate simple baselines first
- use animal-level cross-validation or leave-one-animal-out when appropriate

---

# New Experiment Entry Template

Copy this section for each new experiment.

```text
Date:
Researcher:
Commit hash:
Data version:
Preprocessing config:
Split seed:

Model:
Input features:
Hyperparameters:

Train N:
Validation N:
Test N:

AUROC:
Balanced accuracy:
Sensitivity:
Specificity:
F1:
Accuracy:

Notes:
Failure modes:
Next action:
```
