# Machine Learning Module — Engine Diagnostics & Fault Classification

**Intelligent Multimodal Vehicle Breakdown Assistance and Adaptive Recovery System**

This directory contains the complete, reproducible machine learning pipeline for automotive diagnostic fault classification based on the **EngineFaultDB** benchmark dataset (Vergara et al., 2023, IEEE Access).

---

## 📁 Directory Structure

```
ml/
├── data/                      # Raw and processed datasets (gitignored)
│   └── EngineFaultDB_Final.csv
├── models/                    # Trained artifacts & evaluation outputs (gitignored)
│   ├── model.pkl              # Champion RandomForestClassifier
│   ├── scaler.pkl             # Fitted StandardScaler
│   ├── feature_order.json     # Frozen 14-feature order contract
│   ├── labels.json            # Class ID to name mapping
│   ├── metrics.json           # Comprehensive test metrics
│   ├── confusion_matrix.png   # High-resolution confusion matrix plot
│   └── feature_importance.png # Sensor importance ranking plot
├── notebooks/
│   ├── eda.ipynb              # Exploratory Data Analysis notebook
│   └── generate_eda_notebook.py
├── src/
│   ├── __init__.py
│   ├── features.py            # Feature schema, ordering constants & metadata
│   ├── preprocessing.py       # Data fetch, validation, stratified 80/20 split & scaling
│   ├── train.py               # Model training with 5-fold CV hyperparameter tuning
│   └── evaluate.py            # Test evaluation, metrics export & plot generation
├── model_card.md              # Complete integration contract for backend FastAPI
├── requirements.txt           # Pinned dependencies
└── README.md                  # This documentation
```

---

## 🚀 Setup & Installation

### 1. Install Dependencies
```bash
pip install -r ml/requirements.txt
```

*(If running in a non-root environment on Windows/Linux, use `pip install --user -r ml/requirements.txt`)*

---

## 🛠️ Pipeline Execution

Run the pipeline sequentially with single CLI commands:

### Step 1: Preprocessing & Data Hygiene
Downloads `EngineFaultDB_Final.csv` (if absent), inspects data hygiene, performs an 80/20 stratified train/test split, fits `StandardScaler` on training data only, and serializes `scaler.pkl`:
```bash
python ml/src/preprocessing.py
```

### Step 2: Cross-Validation & Model Training
Executes 5-fold Stratified Cross-Validation across candidate Random Forest configurations, selects the champion model by Macro F1, trains on the full 44,799 training set, and exports `model.pkl`, `feature_order.json`, and `labels.json`:
```bash
python ml/src/train.py
```

### Step 3: Evaluation on Held-Out Test Set
Evaluates the champion model against 11,200 unseen test samples, generates high-res visualization plots (`confusion_matrix.png`, `feature_importance.png`), and writes `metrics.json`:
```bash
python ml/src/evaluate.py
```

---

## 📊 Dataset & Model Performance Summary

- **Source**: EngineFaultDB (55,999 total samples, 14 numeric sensor features)
- **Partitions**: 44,799 Train (80%) / 11,200 Test (20%), Stratified
- **Algorithm**: `RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=42)`

### Test Set Performance Metrics

| Metric | Value |
|:---|:---:|
| **Overall Accuracy** | **74.40%** |
| **Macro F1-Score** | **0.7528** |
| **Weighted F1-Score** | **0.7439** |
| **Macro Precision** | **0.7534** |
| **Macro Recall** | **0.7534** |

### Per-Class Breakdown

| Fault Class | Code | Precision | Recall | F1-Score | Test Support |
|:---|:---:|:---:|:---:|:---:|:---:|
| **No Fault** | `0` | 1.0000 | 1.0000 | **1.0000** | 3,200 |
| **Rich Mixture** | `1` | 1.0000 | 1.0000 | **1.0000** | 2,200 |
| **Lean Mixture** | `2` | 0.5244 | 0.4773 | **0.4997** | 3,000 |
| **Low Voltage** | `3` | 0.4891 | 0.5361 | **0.5115** | 2,800 |

---

## 🔌 Backend Integration Contract

For FastAPI backend developers integrating this model into production endpoints:
👉 **Refer to [`ml/model_card.md`](model_card.md)** for:
- The frozen 14-feature input ordering & unit types.
- Standard JSON output structure.
- Copy-pasteable `EngineFaultPredictor` class.
- "Known Limitations" boundary specifications.
