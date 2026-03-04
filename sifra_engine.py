# sifra_engine.py

import joblib
import pandas as pd
import shap
from openai import OpenAI
import numpy as np

# ===============================
# LOAD TRAINED MODELS
# ===============================

rf = joblib.load("models/rf.pkl")
gb = joblib.load("models/gb.pkl")   
lr = joblib.load("models/lr.pkl")
knn = joblib.load("models/knn.pkl")
nb = joblib.load("models/nb.pkl")
stack_model = joblib.load("models/stack.pkl")
scaler = joblib.load("models/scaler.pkl")

# Load feature order
X_columns = joblib.load("models/feature_columns.pkl")

# ===============================
# LLM CONFIG
# ===============================

LLM_MODEL = "meta-llama-3-8b-instruct"

llm = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)

# ===============================
# ML TOOL
# ===============================

def ml_tool(features):

    input_df = pd.DataFrame([features])
    input_df = input_df.reindex(columns=X_columns).fillna(0)
    input_scaled = pd.DataFrame(scaler.transform(input_df), columns=X_columns)

    rf_prob = rf.predict_proba(input_df)[0][1]
    gb_prob = gb.predict_proba(input_df)[0][1]
    stack_prob = stack_model.predict_proba(input_df)[0][1]
    lr_prob = lr.predict_proba(input_scaled)[0][1]
    knn_prob = knn.predict_proba(input_scaled)[0][1]

    consensus = (
        0.25*rf_prob +
        0.25*gb_prob +
        0.20*lr_prob +
        0.15*stack_prob +
        0.15*knn_prob
    )

    return consensus, input_df

# ===============================
# SHAP TOOL
# ===============================

shap_explainer = shap.TreeExplainer(rf)

def shap_tool(input_df):

    shap_values = shap_explainer(input_df)
    shap_vals = shap_values.values[0,:,1]

    impact_df = pd.DataFrame({
        "Feature": X_columns,
        "Impact": shap_vals
    }).sort_values(by="Impact", key=abs, ascending=False)

    return impact_df.head(5)

# ===============================
# AGENTS
# ===============================

def planning_agent(consensus, glucose, hba1c, impact_df, name):

    prompt = f"""
    You are SIFRA, a clinical decision support AI that explains the output of a diabetes risk prediction model.

    Your task is to interpret the model output responsibly and generate a structured clinical report.

    Patient Name: {name}

    Predicted Diabetes Risk Score: {round(consensus*100,2)}%

    Laboratory Results:
    Fasting Glucose: {glucose} mg/dL
    HbA1c: {hba1c} %

    Medical Reference Ranges:

    Fasting Glucose:
    70–99 mg/dL → Normal
    100–125 mg/dL → Impaired fasting glucose (prediabetes risk)
    ≥126 mg/dL → Diabetes range

    HbA1c:
    <5.7% → Normal
    5.7–6.4% → Prediabetes
    ≥6.5% → Diabetes range

    Risk Categories used by SIFRA:
    0–30% → Low Risk
    30–60% → Moderate Risk
    60–100% → High Risk

    Important Instructions:
    • This system predicts diabetes risk probability, not a medical diagnosis.
    • Do NOT exaggerate medical risk.
    • Interpret laboratory values strictly using the reference ranges above.

    Model Explainability (SHAP Output):

    {impact_df.to_string()}

    SHAP Interpretation Rules:
    • Positive SHAP values increase predicted diabetes risk.
    • Negative SHAP values decrease predicted diabetes risk.
    • Negative SHAP values represent protective factors and should NOT be described as harmful.

    Feature Definitions:
    GenHlth = Self-reported general health status
    BMI = Body Mass Index
    HighBP = History of high blood pressure
    HighChol = History of high cholesterol
    Age = Age category
    PhysActivity = Regular physical activity
    Fruits/Veggies = Dietary habits

    Generate a structured clinical report with the following sections:

    1. Risk Interpretation
    Explain what the predicted diabetes risk score means.

    2. Laboratory Interpretation
    Interpret fasting glucose and HbA1c using the medical ranges above.

    3. Key Risk Drivers
    Explain the most important factors influencing the prediction based on SHAP values.

    4. Clinical Recommendations
    Provide recommendations appropriate for the patient's risk level.

    5. Preventive Advice
    Suggest lifestyle strategies to reduce diabetes risk.

    6. Clinical Disclaimer
    State that this is an AI-assisted risk assessment and not a medical diagnosis.

    The report should be professional, medically responsible, and easy to understand.
    """

    response = llm.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()


def reasoning_agent(name, consensus, impact_df, glucose, hba1c):

    prompt = f"""
Patient: {name}
Risk Score: {round(consensus*100,2)}%

Glucose: {glucose}
HbA1c: {hba1c}

Top Risk Drivers:
{impact_df.to_string()}

Generate structured clinical report.
"""

    response = llm.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content


# ===============================
# MAIN FUNCTION (UI CALLABLE)
# ===============================

def run_sifra_from_ui(name, features, glucose, hba1c):

    consensus, input_df = ml_tool(features)
    impact_df = shap_tool(input_df)

    # ===============================
    # CLINICAL OVERRIDE LOGIC
    # ===============================

    # Severe uncontrolled diabetes
    if glucose >= 200 or hba1c >= 8:
        consensus = max(consensus, 0.90)

    # Strong diabetes signal
    elif glucose >= 170 or hba1c >= 7:
        consensus = max(consensus, 0.75)

    # Moderate diabetes risk
    elif glucose >= 126 or hba1c >= 6.5:
        consensus = max(consensus, 0.65)

    # Prediabetes
    elif 100 <= glucose < 126 or 5.7 <= hba1c < 6.5:
        consensus = max(consensus, 0.45)

    # Ensure valid range
    consensus = np.clip(consensus, 0, 1)

    # ===============================
    # AGENTS RUN AFTER FINAL RISK
    # ===============================

    decision = planning_agent(consensus, glucose, hba1c, impact_df, name)
    report = reasoning_agent(name, consensus, impact_df, glucose, hba1c)
    consensus = np.clip(consensus, 0, 1)

        # 👇 ADD HERE
    consent_prompt = None
    action_required = False

    if consensus >= 0.7:
        action_required = True

        consent_prompt = f"""
        The patient has high diabetes risk ({round(consensus*100,2)}%).

        Would you like to book an appointment?
        """

    return {
        "risk_score": consensus,
        "decision": decision,
        "report": report,
        "action_required": action_required,
        "consent_prompt": consent_prompt
    }