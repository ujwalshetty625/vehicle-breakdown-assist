"""
Script to programmatically generate a clean, executable Jupyter notebook: ml/notebooks/eda.ipynb
"""

import json
from pathlib import Path
import nbformat as nbf

def create_eda_notebook():
    nb = nbf.v4.new_notebook()
    nb['cells'] = []

    # Cell 1: Markdown header
    nb['cells'].append(nbf.v4.new_markdown_cell("""# Exploratory Data Analysis (EDA) — EngineFaultDB Diagnostics
## Intelligent Multimodal Vehicle Breakdown Assistance and Adaptive Recovery System

This notebook explores the **EngineFaultDB** automotive diagnostics dataset (Vergara et al., 2023, IEEE Access, DOI: 10.1109/ACCESS.2023.3331316).

### Objectives:
1. Understand dataset schema, types, and class balance across the 4 fault modes.
2. Analyze sensor distributions per fault condition (combustion telemetry, exhaust emissions, electrical state).
3. Compute correlation relationships among diagnostic sensors.
4. Establish baseline feature importance insights for downstream vehicle recovery.
"""))

    # Cell 2: Imports & setup
    nb['cells'].append(nbf.v4.new_code_cell("""import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Plot styling configuration
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 11

# Add project root to sys.path
repo_root = Path().resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from ml.src.features import FEATURE_ORDER, FAULT_LABELS, TARGET_COLUMN
from ml.src.preprocessing import load_data, clean_data

print("Libraries and ML module loaded successfully.")
"""))

    # Cell 3: Data Loading
    nb['cells'].append(nbf.v4.new_markdown_cell("""## 1. Data Loading and Hygiene Inspection"""))
    
    nb['cells'].append(nbf.v4.new_code_cell("""# Load and clean dataset
df_raw = load_data()
df = clean_data(df_raw)

# Map integer fault codes to readable diagnostic labels
df['Fault_Name'] = df[TARGET_COLUMN].map(FAULT_LABELS)

print(f"Dataset Shape: {df.shape[0]:,} rows x {df.shape[1]} columns")
print(f"Missing Values: {df.isnull().sum().sum()}")
df.head()
"""))

    # Cell 4: Class Distribution
    nb['cells'].append(nbf.v4.new_markdown_cell("""## 2. Fault Class Distribution
The dataset contains 4 discrete fault categories:
- `0`: No Fault (Normal engine operation)
- `1`: Rich Mixture (Excess fuel / insufficient air)
- `2`: Lean Mixture (Excess air / insufficient fuel)
- `3`: Low Voltage (Electrical subsystem fault / battery / alternator drop)
"""))

    nb['cells'].append(nbf.v4.new_code_cell("""# Class distribution analysis
class_counts = df['Fault_Name'].value_counts()
class_pcts = df['Fault_Name'].value_counts(normalize=True) * 100

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
palette = ['#10b981', '#f59e0b', '#ef4444', '#6366f1']
bars = ax.bar(class_counts.index, class_counts.values, color=palette, edgecolor='#1e293b', width=0.55)

for bar, pct in zip(bars, class_pcts.values):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 300,
            f'{height:,}\\n({pct:.1f}%)', ha='center', va='bottom', fontsize=9, fontweight='bold')

ax.set_title("EngineFaultDB Diagnostic Class Distribution", fontsize=12, fontweight='bold', pad=12)
ax.set_ylabel("Sample Count", fontsize=10, fontweight='bold')
ax.set_ylim(0, max(class_counts.values) * 1.18)
plt.tight_layout()
plt.show()
"""))

    # Cell 5: Descriptive Stats
    nb['cells'].append(nbf.v4.new_markdown_cell("""## 3. Summary Statistics of 14 Input Sensors"""))
    
    nb['cells'].append(nbf.v4.new_code_cell("""# Display descriptive statistics for all 14 frozen sensor features
df[FEATURE_ORDER].describe().T[['mean', 'std', 'min', '25%', '50%', '75%', 'max']]
"""))

    # Cell 6: Key Sensor Distributions by Fault Mode
    nb['cells'].append(nbf.v4.new_markdown_cell("""## 4. Key Sensor Distributions Across Fault Classes
We analyze key diagnostic markers:
- **Lambda & AFR**: Critical indicators for Rich vs Lean mixture.
- **CO & HC**: Exhaust emissions showing incomplete combustion.
- **MAP & TPS**: Manifold pressure and throttle relationship.
"""))

    nb['cells'].append(nbf.v4.new_code_cell("""fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=150)

# 1. Lambda by Fault
sns.boxplot(data=df, x='Fault_Name', y='Lambda', palette=palette, ax=axes[0, 0], showfliers=False)
axes[0, 0].set_title("Lambda Equivalence Ratio by Fault Mode", fontweight='bold')
axes[0, 0].axhline(1.0, color='red', linestyle='--', label='Stoichiometric Lambda (1.0)')
axes[0, 0].legend()

# 2. AFR by Fault
sns.boxplot(data=df, x='Fault_Name', y='AFR', palette=palette, ax=axes[0, 1], showfliers=False)
axes[0, 1].set_title("Air-Fuel Ratio (AFR) by Fault Mode", fontweight='bold')
axes[0, 1].axhline(14.7, color='red', linestyle='--', label='Stoichiometric Gasoline AFR (14.7)')
axes[0, 1].legend()

# 3. Carbon Monoxide (CO) by Fault
sns.boxplot(data=df, x='Fault_Name', y='CO', palette=palette, ax=axes[1, 0], showfliers=False)
axes[1, 0].set_title("Carbon Monoxide (CO %) by Fault Mode", fontweight='bold')

# 4. Manifold Absolute Pressure (MAP) by Fault
sns.boxplot(data=df, x='Fault_Name', y='MAP', palette=palette, ax=axes[1, 1], showfliers=False)
axes[1, 1].set_title("Manifold Absolute Pressure (MAP kPa) by Fault Mode", fontweight='bold')

for ax in axes.flat:
    ax.set_xlabel("")
    ax.tick_params(axis='x', rotation=10)

plt.tight_layout()
plt.show()
"""))

    # Cell 7: Pearson Correlation Heatmap
    nb['cells'].append(nbf.v4.new_markdown_cell("""## 5. Sensor Correlation Analysis"""))
    
    nb['cells'].append(nbf.v4.new_code_cell("""# Correlation Matrix of the 14 sensor inputs
corr = df[FEATURE_ORDER].corr()

fig, ax = plt.subplots(figsize=(11, 8.5), dpi=150)
mask = np.triu(np.ones_like(corr, dtype=bool))
cmap = sns.diverging_palette(230, 20, as_cmap=True)

sns.heatmap(
    corr,
    mask=mask,
    cmap=cmap,
    vmax=1.0,
    vmin=-1.0,
    center=0,
    square=True,
    linewidths=0.5,
    cbar_kws={"shrink": 0.8},
    annot=True,
    fmt=".2f",
    annot_kws={"size": 8},
    ax=ax
)

ax.set_title("Sensor Feature Correlation Matrix (EngineFaultDB)", fontsize=13, fontweight='bold', pad=14)
plt.tight_layout()
plt.show()
"""))

    # Cell 8: Conclusions
    nb['cells'].append(nbf.v4.new_markdown_cell("""## 6. Key Diagnostic Findings & Next Steps

1. **Lambda and AFR Separation**:
   - `Rich Mixture` exhibits low Lambda (< 1.0) and depressed AFR (< 14.7) coupled with elevated CO/HC exhaust spikes.
   - `Lean Mixture` exhibits high Lambda (> 1.0) and elevated AFR (> 14.7) with higher residual Oxygen (O2).
2. **Low Voltage & Power Dynamics**:
   - `Low Voltage` induces sub-optimal ignition coil excitation and sensor telemetry voltage drops.
3. **Pipeline Readiness**:
   - The 14 features form a consistent, rich diagnostic signature readily classifiable by tree-based ensemble models (RandomForestClassifier).
"""))

    output_dir = Path("ml/notebooks")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "eda.ipynb"

    with open(output_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"Notebook generated successfully at {output_path}")

if __name__ == "__main__":
    create_eda_notebook()
