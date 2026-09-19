import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# Load dataset
df = pd.read_csv("dataset/credit_data.csv")

# Convert employment status into numbers
employment_encoder = LabelEncoder()
df["employment_status"] = employment_encoder.fit_transform(
    df["employment_status"]
)

# Convert target risk into numbers
risk_encoder = LabelEncoder()
df["risk"] = risk_encoder.fit_transform(df["risk"])

# Features
features = [
    "monthly_income",
    "employment_status",
    "loan_amount",
    "emi",
    "existing_loans",
    "credit_utilization",
    "repayment_history",
    "delayed_payments",
    "outstanding_debt"
]

X = df[features]
y = df["risk"]

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# Random Forest model
model = RandomForestClassifier(
    n_estimators=200,
    random_state=42
)

model.fit(X_train, y_train)

# Test model
prediction = model.predict(X_test)

accuracy = accuracy_score(y_test, prediction)

print("Model Accuracy:", accuracy)
print(classification_report(y_test, prediction))

# Save model
joblib.dump(model, "model/cibil_model.pkl")

# Save encoders
joblib.dump(
    employment_encoder,
    "model/employment_encoder.pkl"
)

joblib.dump(
    risk_encoder,
    "model/risk_encoder.pkl"
)

print("Model saved successfully.")