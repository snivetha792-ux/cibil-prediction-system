from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import joblib
import pandas as pd
from pathlib import Path

from werkzeug.security import generate_password_hash, check_password_hash

from database.db import get_predictions_by_user, init_db, create_user, get_user_by_email, save_prediction
app = Flask(__name__)
app.secret_key = "cibil-prediction-secret-key-2026"
init_db()

# Project directory
BASE_DIR = Path(__file__).resolve().parent

# Load trained model
model = joblib.load(BASE_DIR / "model" / "cibil_model.pkl")
employment_encoder = joblib.load(
    BASE_DIR / "model" / "employment_encoder.pkl"
)

risk_encoder = joblib.load(
    BASE_DIR / "model" / "risk_encoder.pkl"
)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()

        # Get user input
        monthly_income = float(data["monthly_income"])
        employment_status = data["employment_status"]
        loan_amount = float(data["loan_amount"])
        emi = float(data["emi"])
        existing_loans = int(data["existing_loans"])
        credit_utilization = float(data["credit_utilization"])
        repayment_history = float(data["repayment_history"])
        delayed_payments = int(data["delayed_payments"])
        outstanding_debt = float(data["outstanding_debt"])

        # Encode employment status
        employment_encoded = employment_encoder.transform(
            [employment_status]
        )[0]

        # Create input dataframe
        input_data = pd.DataFrame([{
            "monthly_income": monthly_income,
            "employment_status": employment_encoded,
            "loan_amount": loan_amount,
            "emi": emi,
            "existing_loans": existing_loans,
            "credit_utilization": credit_utilization,
            "repayment_history": repayment_history,
            "delayed_payments": delayed_payments,
            "outstanding_debt": outstanding_debt
        }])

        # Predict risk
        prediction = model.predict(input_data)[0]

        # Convert encoded prediction back to text
        risk = risk_encoder.inverse_transform([prediction])[0]

        # Prediction probability
        probabilities = model.predict_proba(input_data)[0]
        confidence = round(max(probabilities) * 100, 2)

        # Save prediction for logged-in user
        if "user_email" in session:
            save_prediction(
                session["user_email"],
                monthly_income,
                employment_status,
                loan_amount,
                emi,
                existing_loans,
                credit_utilization,
                repayment_history,
                delayed_payments,
                outstanding_debt,
                risk,
                confidence
            )

        return jsonify({
            "success": True,
            "risk": risk,
            "confidence": confidence
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

@app.route("/dashboard")
def dashboard():
    if "user_email" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")

@app.route("/calculator")
def calculator():
    if "user_email" not in session:
        return redirect(url_for("login"))

    return render_template("calculator.html")


@app.route("/simulator")
def simulator():
    if "user_email" not in session:
        return redirect(url_for("login"))

    return render_template("simulator.html")


@app.route("/history")
def history():
    if "user_email" not in session:
        return redirect(url_for("login"))

    predictions = get_predictions_by_user(session["user_email"])

    return render_template(
        "history.html",
        predictions=predictions
    )

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not name or not email or not password:
            return render_template(
                "register.html",
                error="Please fill all fields."
            )

        if len(password) < 6:
            return render_template(
                "register.html",
                error="Password must be at least 6 characters."
            )

        password_hash = generate_password_hash(password)

        user_created = create_user(
            name,
            email,
            password_hash
        )

        if not user_created:
            return render_template(
                "register.html",
                error="This email is already registered."
            )

        # Store login session
        session["user_email"] = email
        session["user_name"] = name

        # After registration → Home page
        return redirect(url_for("home"))

    return render_template("register.html")

@app.route("/explain")
def explain():

    if "user_email" not in session:
        return redirect(url_for("login"))

    return render_template("explain.html")

@app.route("/credit-plan")
def credit_plan():

    if "user_email" not in session:
        return redirect(url_for("login"))

    return render_template("credit_plan.html")

@app.route("/advisor")
def advisor():

    if "user_email" not in session:
        return redirect(url_for("login"))

    return render_template("advisor.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        user = get_user_by_email(email)

        if user and check_password_hash(user["password"], password):
            session["user_email"] = user["email"]
            session["user_name"] = user["name"]
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Invalid email or password.")

    return render_template("login.html")

    
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

def generate_risk_factors(data):
    factors = []

    if data["credit_utilization"] >= 70:
        factors.append({
            "title": "High Credit Utilization",
            "value": f'{data["credit_utilization"]}%',
            "level": "High"
        })
    elif data["credit_utilization"] >= 40:
        factors.append({
            "title": "Moderate Credit Utilization",
            "value": f'{data["credit_utilization"]}%',
            "level": "Medium"
        })

    if data["delayed_payments"] >= 3:
        factors.append({
            "title": "Delayed Payments",
            "value": str(data["delayed_payments"]),
            "level": "High"
        })

    if data["outstanding_debt"] > data["monthly_income"] * 3:
        factors.append({
            "title": "High Outstanding Debt",
            "value": f'₹{data["outstanding_debt"]:,.0f}',
            "level": "High"
        })

    if data["repayment_history"] >= 90:
        factors.append({
            "title": "Good Repayment History",
            "value": f'{data["repayment_history"]}%',
            "level": "Good"
        })

    return factors

def generate_credit_plan(data):

    plan = []

    if data["credit_utilization"] > 30:
        plan.append({
            "priority": "High",
            "title": "Reduce Credit Utilization",
            "current": f'{data["credit_utilization"]}%',
            "target": "Below 30%"
        })

    if data["delayed_payments"] > 0:
        plan.append({
            "priority": "High",
            "title": "Avoid Delayed Payments",
            "current": str(data["delayed_payments"]),
            "target": "0 delayed payments"
        })

    if data["outstanding_debt"] > data["monthly_income"] * 2:
        plan.append({
            "priority": "Medium",
            "title": "Reduce Outstanding Debt",
            "current": f'₹{data["outstanding_debt"]:,.0f}',
            "target": "Reduce outstanding balance"
        })

    if data["existing_loans"] > 2:
        plan.append({
            "priority": "Medium",
            "title": "Manage Existing Loans",
            "current": str(data["existing_loans"]),
            "target": "Avoid unnecessary new loans"
        })

    return plan

if __name__ == "__main__":
    app.run(debug=True)