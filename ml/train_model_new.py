import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.metrics import (
    accuracy_score, classification_report,
    confusion_matrix, ConfusionMatrixDisplay
)
import matplotlib.pyplot as plt
import xgboost as xgb

df = pd.read_csv('ml/training_dataset.csv')

X = df[["Data Type", "File Size (Bytes)", "CPU Ambient (%)", "Battery Ambient (%)"]].copy()
y = df["Best Algorithm"]

# NEW: log-transform file size — sizes span KB to tens of MB, so raw
# byte counts give trees very little to split on cleanly.
X["File Size (Bytes)"] = np.log1p(X["File Size (Bytes)"])

data_type_encoder = LabelEncoder()
algorithms_encoder = LabelEncoder()
X["Data Type"] = data_type_encoder.fit_transform(X["Data Type"])
y = algorithms_encoder.fit_transform(y)

# the last parameter fixes the random seed so the results are the same every time the program runs.
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# NEW: class_weight="balanced" — free to add, directly compensates for
# PRESENT having ~3x fewer rows than ChaCha20.
rf_model = RandomForestClassifier(
    n_estimators=100,
    class_weight="balanced",
    random_state=42
)

xgb_model = xgb.XGBClassifier(random_state=42, eval_metric="mlogloss")

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# NEW: cross-validate BOTH models (you were only doing this for RF
# before), and score on f1_macro instead of accuracy — with a 90/74/25
# split, accuracy alone can look fine even if PRESENT is barely learned.
rf_cv_scores = cross_val_score(rf_model, X, y, cv=cv, scoring="f1_macro")
xgb_cv_scores = cross_val_score(xgb_model, X, y, cv=cv, scoring="f1_macro")

print("RF  CV f1_macro:", rf_cv_scores, f"mean={rf_cv_scores.mean():.3f}")
print("XGB CV f1_macro:", xgb_cv_scores, f"mean={xgb_cv_scores.mean():.3f}")

# Train on the held-out split for the final report / confusion matrix
rf_model.fit(X_train, y_train)
rf_predictions = rf_model.predict(X_test)
print(f"Random Forest holdout accuracy: {accuracy_score(y_test, rf_predictions):.2f}")
print(classification_report(y_test, rf_predictions, target_names=algorithms_encoder.classes_))

# NEW: sample_weight — XGBoost has no class_weight param for multiclass,
# compute_sample_weight is the equivalent fix.
sample_weights = compute_sample_weight(class_weight="balanced", y=y_train)
xgb_model.fit(X_train, y_train, sample_weight=sample_weights)
xgb_predictions = xgb_model.predict(X_test)
print(f"XGBoost holdout accuracy: {accuracy_score(y_test, xgb_predictions):.2f}")
print(classification_report(y_test, xgb_predictions, target_names=algorithms_encoder.classes_))

joblib.dump(rf_model, "ml/random_forest.pkl")
joblib.dump(xgb_model, "ml/xgboost.pkl")

# NEW: pick "best" by CV mean f1_macro, not one train/test split — a
# single split can flip between models just from which rows landed in
# the 20% test set (likely why your report's CV scores swing 0.605–0.784).
if rf_cv_scores.mean() >= xgb_cv_scores.mean():
    best_model, best_name = rf_model, "random_forest"
else:
    best_model, best_name = xgb_model, "xgboost"

# NEW: this is the actual fix for the "encoders correctly saved" item —
# before, only the raw model was saved, with no way to reproduce the
# same encoding at prediction time.
joblib.dump({
    "model": best_model,
    "model_name": best_name,
    "data_type_encoder": data_type_encoder,
    "algorithms_encoder": algorithms_encoder,
    "feature_order": ["Data Type", "File Size (Bytes)", "CPU Ambient (%)", "Battery Ambient (%)"],
    "log_transform_file_size": True
}, "ml/predictor.joblib")

cm = confusion_matrix(y_test, xgb_predictions)
disp = ConfusionMatrixDisplay(cm, display_labels=algorithms_encoder.classes_)
disp.plot()
plt.show(block=False)
plt.pause(2)
plt.close()

print(df["Best Algorithm"].value_counts())