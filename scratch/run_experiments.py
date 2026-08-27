"""
Fast & Comprehensive ML experimentation script with real-time logging.
Evaluates:
1. Deduplicated baseline vs raw baseline.
2. Class Weighting (balanced vs balanced_subsample vs None).
3. SMOTE oversampling.
4. Feature Engineering (Lambda/AFR deviation, combustion ratios).
5. Hyperparameter Tuning (n_estimators, max_depth, max_features, min_samples_leaf).
6. Model Family Benchmark (Random Forest vs HistGradientBoosting vs ExtraTrees).
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import StratifiedKFold, train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.metrics import classification_report, f1_score, accuracy_score
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline

# Load dataset
df_raw = pd.read_csv("ml/data/EngineFaultDB_Final.csv")

# 1. Deduplication
df_clean = df_raw.drop_duplicates().reset_index(drop=True)
print(f"Raw shape: {df_raw.shape} -> Deduplicated shape: {df_clean.shape}", flush=True)

raw_features = [c for c in df_clean.columns if c != "Fault"]
X_raw = df_clean[raw_features].values
y = df_clean["Fault"].values

# Train/Test Split (80/20 Stratified, random_state=42)
X_train_raw, X_test_raw, y_train, y_test = train_test_split(
    X_raw, y, test_size=0.2, random_state=42, stratify=y
)

scaler_raw = StandardScaler()
X_train_raw_scaled = scaler_raw.fit_transform(X_train_raw)
X_test_raw_scaled = scaler_raw.transform(X_test_raw)

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

print("\n" + "="*70, flush=True)
print("EXPERIMENT 1: Class Weighting Strategies (Random Forest)", flush=True)
print("="*70, flush=True)
for cw in [None, "balanced", "balanced_subsample"]:
    rf = RandomForestClassifier(n_estimators=200, class_weight=cw, random_state=42, n_jobs=-1)
    f1_cv = cross_val_score(rf, X_train_raw_scaled, y_train, cv=skf, scoring="f1_macro", n_jobs=-1)
    acc_cv = cross_val_score(rf, X_train_raw_scaled, y_train, cv=skf, scoring="accuracy", n_jobs=-1)
    print(f"class_weight={str(cw):<18} | Macro F1: {np.mean(f1_cv):.4f} +/- {np.std(f1_cv):.4f} | Acc: {np.mean(acc_cv):.4f}", flush=True)

print("\n" + "="*70, flush=True)
print("EXPERIMENT 2: SMOTE Oversampling on Training Folds", flush=True)
print("="*70, flush=True)
smote_pipe = ImbPipeline([
    ('smote', SMOTE(random_state=42)),
    ('rf', RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1))
])
f1_smote = cross_val_score(smote_pipe, X_train_raw_scaled, y_train, cv=skf, scoring="f1_macro", n_jobs=-1)
acc_smote = cross_val_score(smote_pipe, X_train_raw_scaled, y_train, cv=skf, scoring="accuracy", n_jobs=-1)
print(f"SMOTE + RF (n_estimators=200) | Macro F1: {np.mean(f1_smote):.4f} +/- {np.std(f1_smote):.4f} | Acc: {np.mean(acc_smote):.4f}", flush=True)

print("\n" + "="*70, flush=True)
print("EXPERIMENT 3: Feature Engineering (Combustion & Physics Signals)", flush=True)
print("="*70, flush=True)
df_feat = df_clean.copy()
df_feat["Lambda_deviation"] = (df_feat["Lambda"] - 1.0).abs()
df_feat["AFR_deviation"] = (df_feat["AFR"] - 14.7).abs()
df_feat["CO_HC_ratio"] = df_feat["CO"] / (df_feat["HC"] + 1e-5)
df_feat["HC_O2_ratio"] = df_feat["HC"] / (df_feat["O2"] + 1e-5)
df_feat["CO_CO2_ratio"] = df_feat["CO"] / (df_feat["CO2"] + 1e-5)
df_feat["Specific_Fuel_Cons"] = df_feat["Consumption L/H"] / (df_feat["Power"] + 1e-5)

eng_features = [c for c in df_feat.columns if c != "Fault"]
X_eng = df_feat[eng_features].values

X_train_eng, X_test_eng, _, _ = train_test_split(
    X_eng, y, test_size=0.2, random_state=42, stratify=y
)
scaler_eng = StandardScaler()
X_train_eng_scaled = scaler_eng.fit_transform(X_train_eng)
X_test_eng_scaled = scaler_eng.transform(X_test_eng)

rf_eng = RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=42, n_jobs=-1)
f1_eng = cross_val_score(rf_eng, X_train_eng_scaled, y_train, cv=skf, scoring="f1_macro", n_jobs=-1)
acc_eng = cross_val_score(rf_eng, X_train_eng_scaled, y_train, cv=skf, scoring="accuracy", n_jobs=-1)
print(f"Engineered Features ({len(eng_features)} feats) | Macro F1: {np.mean(f1_eng):.4f} +/- {np.std(f1_eng):.4f} | Acc: {np.mean(acc_eng):.4f}", flush=True)

# Feature Importances
rf_eng.fit(X_train_eng_scaled, y_train)
importances_eng = rf_eng.feature_importances_
print("\nEngineered Feature Importances Ranking:", flush=True)
for f, imp in sorted(zip(eng_features, importances_eng), key=lambda x: x[1], reverse=True):
    print(f"  {f:<24}: {imp:.4f} ({imp*100:.2f}%)", flush=True)

print("\n" + "="*70, flush=True)
print("EXPERIMENT 4: Hyperparameter Tuning (Random Forest)", flush=True)
print("="*70, flush=True)
rf_configs = [
    {"name": "RF_D15_N200_Bal", "params": {"n_estimators": 200, "max_depth": 15, "min_samples_split": 2, "class_weight": "balanced", "random_state": 42, "n_jobs": -1}},
    {"name": "RF_D25_N200_Bal", "params": {"n_estimators": 200, "max_depth": 25, "min_samples_split": 2, "class_weight": "balanced", "random_state": 42, "n_jobs": -1}},
    {"name": "RF_DNone_N200_Bal", "params": {"n_estimators": 200, "max_depth": None, "min_samples_split": 2, "class_weight": "balanced", "random_state": 42, "n_jobs": -1}},
    {"name": "RF_DNone_N300_Bal", "params": {"n_estimators": 300, "max_depth": None, "min_samples_split": 2, "class_weight": "balanced", "random_state": 42, "n_jobs": -1}},
    {"name": "RF_DNone_N300_Leaf2_Bal", "params": {"n_estimators": 300, "max_depth": None, "min_samples_leaf": 2, "class_weight": "balanced", "random_state": 42, "n_jobs": -1}},
    {"name": "RF_DNone_N300_Log2_Bal", "params": {"n_estimators": 300, "max_depth": None, "max_features": "log2", "class_weight": "balanced", "random_state": 42, "n_jobs": -1}},
    {"name": "RF_DNone_N300_Feat07_Bal", "params": {"n_estimators": 300, "max_depth": None, "max_features": 0.7, "class_weight": "balanced", "random_state": 42, "n_jobs": -1}},
]

for cfg in rf_configs:
    model = RandomForestClassifier(**cfg["params"])
    f1_cv = cross_val_score(model, X_train_raw_scaled, y_train, cv=skf, scoring="f1_macro", n_jobs=-1)
    acc_cv = cross_val_score(model, X_train_raw_scaled, y_train, cv=skf, scoring="accuracy", n_jobs=-1)
    print(f"{cfg['name']:<28} | Macro F1: {np.mean(f1_cv):.4f} +/- {np.std(f1_cv):.4f} | Acc: {np.mean(acc_cv):.4f}", flush=True)

print("\n" + "="*70, flush=True)
print("EXPERIMENT 5: Model Family Comparison", flush=True)
print("="*70, flush=True)
models_to_compare = [
    ("Random Forest (Champion)", RandomForestClassifier(n_estimators=300, max_features="sqrt", class_weight="balanced", random_state=42, n_jobs=-1)),
    ("Extra Trees Classifier", ExtraTreesClassifier(n_estimators=300, max_features="sqrt", class_weight="balanced", random_state=42, n_jobs=-1)),
    ("HistGradientBoosting", HistGradientBoostingClassifier(max_iter=300, learning_rate=0.1, max_depth=12, random_state=42)),
]

for name, clf in models_to_compare:
    f1_cv = cross_val_score(clf, X_train_raw_scaled, y_train, cv=skf, scoring="f1_macro", n_jobs=-1)
    acc_cv = cross_val_score(clf, X_train_raw_scaled, y_train, cv=skf, scoring="accuracy", n_jobs=-1)
    print(f"{name:<28} | Macro F1: {np.mean(f1_cv):.4f} +/- {np.std(f1_cv):.4f} | Acc: {np.mean(acc_cv):.4f}", flush=True)

print("\n" + "="*70, flush=True)
print("HELD-OUT TEST SET EVALUATION ON CHAMPION MODEL", flush=True)
print("="*70, flush=True)
champ = RandomForestClassifier(n_estimators=300, max_depth=None, min_samples_split=2, class_weight="balanced", random_state=42, n_jobs=-1)
champ.fit(X_train_raw_scaled, y_train)
y_pred = champ.predict(X_test_raw_scaled)
print(classification_report(y_test, y_pred, target_names=['No Fault', 'Rich Mixture', 'Lean Mixture', 'Low Voltage'], digits=4), flush=True)
