# Notebook Guide

Use the `ml_pipeline/` scripts for the reproducible training path and keep exploratory work in notebooks that mirror these themes:

- `01_eda.ipynb`: class balance, feature distributions, missing-value review, correlation heatmap.
- `02_feature_selection.ipynb`: engineered feature inspection, mutual information, permutation importance.
- `03_model_comparison.ipynb`: Random Forest vs XGBoost vs Logistic Regression, ROC curves, threshold tuning.

The production code path lives in [`backend/app/ml/features.py`](C:\Users\91982\Desktop\MCA\pcos prediction system\pcos-prediction\backend\app\ml\features.py) and [`backend/app/ml/train.py`](C:\Users\91982\Desktop\MCA\pcos prediction system\pcos-prediction\backend\app\ml\train.py), so notebooks should import those modules rather than redefining preprocessing.
