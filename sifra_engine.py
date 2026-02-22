# sifra_engine.py

import joblib
import pandas as pd
import shap
from openai import OpenAI

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

def planning_agent(consensus, glucose, hba1c):

    prompt = f"""
Risk Score: {round(consensus*100,2)}%
Glucose: {glucose}
HbA1c: {hba1c}

Choose one:
1. Lifestyle intervention
2. Specialist referral
3. Monitoring
4. No action

Return number + short justification.
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

    # 🔬 Clinical override logic
    if glucose >= 126 or hba1c >= 6.5:
        consensus = max(consensus, 0.75)

    elif 100 <= glucose < 126 or 5.7 <= hba1c < 6.5:
        consensus = max(consensus, 0.45)   # Moderate Risk

    decision = planning_agent(consensus, glucose, hba1c)
    report = reasoning_agent(name, consensus, impact_df, glucose, hba1c)

    return {
        "risk_score": consensus,
        "decision": decision,
        "report": report
    }

