"""
Generate ml/notebooks/leakage_check.ipynb
"""
import nbformat as nbf
from pathlib import Path

def create_leakage_notebook():
    nb = nbf.v4.new_notebook()
    nb['cells'] = []

    # Cell 1: Markdown
    nb['cells'].append(nbf.v4.new_markdown_cell("""# Leakage Diagnostic & Data Integrity Analysis
## EngineFaultDB Automotive Diagnostics

This notebook performs a deep-dive diagnostic inspection into:
1. Exact full-row duplicate detection.
2. Near-duplicate analysis across various float rounding precisions (4, 3, 2, 1 decimals).
3. Train/Test leakage verification for stratified 80/20 splitting.
4. Feature separability analysis explaining why **No Fault** and **Rich Mixture** are easily separable, while **Lean Mixture** and **Low Voltage** exhibit significant overlap.
"""))

    # Cell 2: Code
    nb['cells'].append(nbf.v4.new_code_cell("""import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split

repo_root = Path().resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from ml.src.features import FEATURE_ORDER, FAULT_LABELS, TARGET_COLUMN
from ml.src.preprocessing import load_data, clean_data

df = load_data()
print(f"Loaded dataset shape: {df.shape}")
"""))

    # Cell 3: Markdown
    nb['cells'].append(nbf.v4.new_markdown_cell("""## 1. Exact Duplicate Analysis"""))
    
    # Cell 4: Code
    nb['cells'].append(nbf.v4.new_code_cell("""exact_dups = df.duplicated().sum()
print(f"Exact full-row duplicates: {exact_dups:,} / {len(df):,} ({exact_dups/len(df):.4%})")

features = [c for c in df.columns if c != 'Fault']
feat_dups = df.duplicated(subset=features, keep=False).sum()
print(f"Rows sharing identical 14-feature sensor readings: {feat_dups:,} / {len(df):,} ({feat_dups/len(df):.4%})")

print("\\nPer-Class Duplicate Breakdown:")
for fid, name in FAULT_LABELS.items():
    sub = df[df['Fault'] == fid]
    d_count = sub.duplicated().sum()
    print(f"  Class {fid} ({name:<14}): {len(sub):6,d} total | {d_count:4d} exact dups ({d_count/len(sub):.2%}) | {len(sub)-d_count:6,d} unique")
"""))

    # Cell 5: Markdown
    nb['cells'].append(nbf.v4.new_markdown_cell("""## 2. Near-Duplicate Analysis (Rounded Float Precision)"""))

    # Cell 6: Code
    nb['cells'].append(nbf.v4.new_code_cell("""for decimals in [4, 3, 2, 1]:
    df_sub = df.copy()
    df_sub[features] = df_sub[features].round(decimals)
    n_dups = df_sub.duplicated().sum()
    print(f"Precision: {decimals} decimals -> Near duplicates: {n_dups:,} / {len(df):,} ({n_dups/len(df):.4%})")
"""))

    # Cell 7: Markdown
    nb['cells'].append(nbf.v4.new_markdown_cell("""## 3. Train/Test Partition Leakage Check (80/20 Stratified)"""))

    # Cell 8: Code
    nb['cells'].append(nbf.v4.new_code_cell("""X = df[features]
y = df['Fault']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

train_tuples = set(tuple(x) for x in X_train.values)
test_in_train = sum(tuple(x) in train_tuples for x in X_test.values)
print(f"Test samples exactly present in Training partition: {test_in_train} / {len(X_test):,} ({test_in_train/len(X_test):.4%})")
"""))

    # Cell 9: Markdown
    nb['cells'].append(nbf.v4.new_markdown_cell("""## 4. Root Cause of Class 0/1 (100%) vs Class 2/3 (~50%) Confusion
Physical feature distributions reveal:
- **Rich Mixture (Class 1)** is cleanly delineated by extreme spikes in CO, HC, and low AFR.
- **No Fault (Class 0)** is distinct with nominal stoichiometric combustion and baseline load.
- **Lean Mixture (Class 2) vs Low Voltage (Class 3)** overlap almost identically across all 14 combustion features because weak ignition coil voltage generates incomplete combustion misfires that mimic lean mixture telemetry.
"""))

    # Cell 10: Code
    nb['cells'].append(nbf.v4.new_code_cell("""fig, axes = plt.subplots(1, 3, figsize=(16, 4.5), dpi=150)

sns.kdeplot(data=df, x='CO', hue='Fault', palette='tab10', common_norm=False, ax=axes[0])
axes[0].set_title("CO Emission Distribution by Fault", fontweight='bold')

sns.kdeplot(data=df, x='HC', hue='Fault', palette='tab10', common_norm=False, ax=axes[1])
axes[1].set_title("HC Emission Distribution by Fault", fontweight='bold')

sns.kdeplot(data=df, x='Lambda', hue='Fault', palette='tab10', common_norm=False, ax=axes[2])
axes[2].set_title("Lambda Distribution by Fault", fontweight='bold')

plt.tight_layout()
plt.show()
"""))

    out_path = Path("ml/notebooks/leakage_check.ipynb")
    with open(out_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"Generated {out_path}")

if __name__ == "__main__":
    create_leakage_notebook()
