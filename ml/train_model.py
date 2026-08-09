import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import xgboost as xgb
df= pd.read_csv('ml/dataset.csv')

X= df[["Data Type", "File Size (Bytes)", "CPU Usage (%)", "Battery Level (%)"]]
y=df["Algorithms"]

data_type_encoder=LabelEncoder()
Algorithms_encoder=LabelEncoder()
# Encode file types as numbers for the ML model.
X["Data Type"] = data_type_encoder.fit_transform(X["Data Type"]) 
y = Algorithms_encoder.fit_transform(y)

# the last parameter fixes the random seed so the results are the same every time the program runs.
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
rf_model = RandomForestClassifier(
    n_estimators=100, # Build a Random Forest using 100 decision trees.
    random_state=42
)
# # Train the Random Forest using the training data.
rf_model.fit(X_train, y_train) 
# Make predictions on the test data.
rf_predictions = rf_model.predict(X_test)
# Evaluate the model's performance (accuracy and classification report).
rf_accuracy = accuracy_score(y_test, rf_predictions)
print(f"Random Forest Accuracy: {rf_accuracy:.2f}")
print(classification_report(y_test, rf_predictions)) #A detailed report card.

# xgboost model
xgb_model = xgb.XGBClassifier( random_state=42, eval_metrics = "mlogloss")
# train the model using the training data.
xgb_model.fit(X_train, y_train)
# Make predictions on the test data.
xgb_predictions = xgb_model.predict(X_test)
# Accuracy
xgb_accuracy = accuracy_score(y_test, xgb_predictions)
print(f"XGBoost Accuracy: {xgb_accuracy:.2f}")
#Classification report
print(classification_report(y_test, xgb_predictions)) #A detailed report card.
# Save the trained models to disk for later use.
joblib.dump(rf_model, "ml/random_forest.pkl")
joblib.dump(xgb_model, "ml/xgboost.pkl")
# save the model with the highest accuracy to disk for later use.
if rf_accuracy >= xgb_accuracy:
    joblib.dump(rf_model, "ml/best_model.pkl")
else:
    joblib.dump(xgb_model, "ml/best_model.pkl")