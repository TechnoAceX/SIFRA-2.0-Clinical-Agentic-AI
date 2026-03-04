# ===============================================================
# 🚀 SIFRA 2.0 – CLEAN FASTAPI BACKEND
# ===============================================================

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict
from datetime import datetime
import smtplib
import io

from email.mime.text import MIMEText
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import pdfplumber

from openai import OpenAI
from sifra_engine import run_sifra_from_ui


# ===============================================================
# 🧠 LLM SETUP (LM STUDIO)
# ===============================================================

LLM_MODEL = "meta-llama-3-8b-instruct"

llm = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)


# ===============================================================
# 🚀 FASTAPI APP
# ===============================================================

app = FastAPI(
    title="SIFRA 2.0 Clinical Agentic AI",
    version="2.0"
)

# ===============================================================
# 🌐 CORS
# ===============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===============================================================
# 📦 SCHEMAS
# ===============================================================

class PatientData(BaseModel):
    name: str
    features: Dict[str, float]
    glucose: float
    hba1c: float


class ChatRequest(BaseModel):
    message: str


class EmailRequest(BaseModel):
    email: str
    report: str


class ReportRequest(BaseModel):
    patient_name: str
    risk_score: str
    glucose: float
    hba1c: float
    clinical_interpretation: str
    risk_drivers: str
    recommendations: str
    preventive_advice: str


# ===============================================================
# 🏥 HEALTH CHECK
# ===============================================================

@app.get("/")
def root():
    return {
        "status": "SIFRA Backend Running",
        "message": "Agentic Clinical AI Ready"
    }


# ===============================================================
# 🔬 ML ANALYSIS
# ===============================================================

@app.post("/analyze")
def analyze(data: PatientData):

    try:

        result = run_sifra_from_ui(
            name=data.name,
            features=data.features,
            glucose=data.glucose,
            hba1c=data.hba1c
        )

        return {
            "success": True,
            **result
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"SIFRA processing error: {str(e)}"
        )


# ===============================================================
# 💬 CHAT WITH SIFRA
# ===============================================================

@app.post("/chat")
def chat(req: ChatRequest):

    response = llm.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "You are SIFRA, a clinical AI assistant."},
            {"role": "user", "content": req.message}
        ],
        temperature=0.3
    )

    return {
        "reply": response.choices[0].message.content
    }


# ===============================================================
# 📄 PDF GENERATOR
# ===============================================================

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from datetime import datetime
import io
import textwrap


def clean_text(text):
    if not text:
        return ""
    return text.replace("■","").replace("•","-").replace("\n"," ")


from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from datetime import datetime
import io
import textwrap


def clean_text(text):
    if not text:
        return ""
    return text.replace("■","").replace("•","-").replace("\n"," ")

from datetime import datetime
import io

# ===============================================================
# 📥 DOWNLOAD REPORT
# ===============================================================

@app.post("/download-report")
def download_report(data: dict):

    buffer = io.BytesIO()

    c = canvas.Canvas(buffer, pagesize=A4)

    date = datetime.now().strftime("%B %d, %Y")

    y = 800

    c.setFont("Helvetica-Bold", 20)
    c.drawString(180, y, "SIFRA Clinical AI Report")

    y -= 40
    c.setFont("Helvetica-Bold", 18)
    c.drawString(200, y, "MEDICAL CERTIFICATE")

    y -= 40
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Date: {date}")

    y -= 40
    c.drawString(50, y, f"Name: {data.get('patient_name','Unknown')}")

    y -= 25
    c.drawString(50, y, f"Risk Score: {data.get('risk_score','N/A')}")

    y -= 40
    c.drawString(50, y, "Clinical Interpretation:")

    y -= 20
    c.drawString(50, y, data.get("clinical_interpretation","N/A"))

    y -= 40
    c.drawString(50, y, "Laboratory Values")

    y -= 20
    c.drawString(50, y, f"Fasting Glucose: {data.get('glucose','N/A')}")

    y -= 20
    c.drawString(50, y, f"HbA1c: {data.get('hba1c','N/A')}")

    y -= 40
    c.drawString(50, y, "Key Risk Drivers")

    y -= 20
    c.drawString(50, y, data.get("risk_drivers","N/A"))

    y -= 40
    c.drawString(50, y, "Clinical Recommendations")

    y -= 20
    c.drawString(50, y, data.get("recommendations","N/A"))

    y -= 40
    c.drawString(50, y, "Preventive Advice")

    y -= 20
    c.drawString(50, y, data.get("preventive_advice","N/A"))

    y -= 80
    c.drawString(50, y, "Doctor Name: SIFRA Clinical AI System")

    y -= 20
    c.drawString(50, y, "Signature: Automated Clinical Report")

    c.save()

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition":"attachment; filename=SIFRA_Report.pdf"}
    )


# ===============================================================
# 📧 EMAIL REPORT
# ===============================================================

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io
from datetime import datetime

def generate_pdf(data):

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    y = 800

    def safe(value):
        return str(value) if value else "Not available"

    def draw_multiline(text, y):
        for line in text.split("\n"):
            c.drawString(50, y, line[:100])
            y -= 15
        return y

    c.setFont("Helvetica-Bold", 20)
    c.drawString(180, y, "SIFRA Clinical AI Report")

    y -= 40
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Date: {datetime.now().strftime('%B %d, %Y')}")

    y -= 40
    c.drawString(50, y, f"Patient Name: {safe(data.get('patient_name'))}")

    y -= 30
    c.drawString(50, y, f"Risk Score: {safe(data.get('risk_score'))}")

    y -= 30
    c.drawString(50, y, f"Glucose: {safe(data.get('glucose'))}")

    y -= 30
    c.drawString(50, y, f"HbA1c: {safe(data.get('hba1c'))}")

    y -= 40
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Clinical Interpretation:")

    y -= 20
    c.setFont("Helvetica", 11)
    y = draw_multiline(safe(data.get("clinical_interpretation")), y)

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Recommendations:")

    y -= 20
    c.setFont("Helvetica", 11)
    y = draw_multiline(safe(data.get("recommendations")), y)

    y -= 40
    c.drawString(50, y, "Generated by: SIFRA Clinical AI System")

    c.save()

    buffer.seek(0)

    return buffer


from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

@app.post("/send-report")
def send_report(data: dict):

    sender_email = "sifra.care.ai@gmail.com"
    app_password = "lpihctlkdfkiwcjl"

    # generate pdf
    pdf_buffer = generate_pdf(data)

    msg = MIMEMultipart()
    msg["Subject"] = "Your SIFRA Health Report"
    msg["From"] = sender_email
    msg["To"] = data["email"]

    body = f"""
    Dear {data.get("patient_name", "Patient")},

    Greetings from SIFRA — Smart Clinical AI.

    Thank you for using SIFRA for your health risk assessment. Based on the information and clinical indicators you provided, our system has completed an AI-assisted evaluation of your metabolic health profile.

    Attached to this email you will find your personalized Diabetes Risk Assessment Report generated through SIFRA's multi-model clinical analysis system.

    The report includes:
    • A summary of your clinical risk evaluation
    • Key health indicators such as glucose and HbA1c levels
    • AI-assisted interpretation of your risk profile
    • Preventive guidance and general health recommendations

    Please note that this report is intended to support health awareness and is not a medical diagnosis. We strongly recommend consulting a qualified healthcare professional for clinical interpretation and advice.

    Thank you for using SIFRA.

    Warm regards,  
    SIFRA Clinical AI  
    AI-Powered Clinical Decision Support System
    """

    msg.attach(MIMEText(body, "plain"))

    # attach pdf
    part = MIMEBase("application", "octet-stream")
    part.set_payload(pdf_buffer.read())
    encoders.encode_base64(part)

    part.add_header(
        "Content-Disposition",
        "attachment; filename=SIFRA_Report.pdf",
    )

    msg.attach(part)

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, app_password)
    server.sendmail(sender_email, data["email"], msg.as_string())
    server.quit()

    return {"status": "Email sent with report"}

# ===============================================================
# 📄 MEDICAL PDF ANALYZER
# ===============================================================

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):

    text_content = ""

    with pdfplumber.open(file.file) as pdf:
        for page in pdf.pages:
            text_content += page.extract_text() + "\n"

    completion = llm.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are SIFRA, a medical AI assistant."
            },
            {
                "role": "user",
                "content": f"Medical Report:\n{text_content}\n\nPlease analyze it."
            }
        ],
        temperature=0.5
    )

    return {
        "reply": completion.choices[0].message.content
    }