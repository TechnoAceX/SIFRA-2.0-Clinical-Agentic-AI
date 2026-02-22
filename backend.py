# ===============================================================
# 🚀 SIFRA 2.0 – FastAPI Backend
# ===============================================================

from openai import OpenAI

LLM_MODEL = "meta-llama-3-8b-instruct"

llm = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from sifra_engine import run_sifra_from_ui
from fastapi import UploadFile, File
import pdfplumber

# ===============================================================
# 🧠 APP INITIALIZATION
# ===============================================================

app = FastAPI(
    title="SIFRA 2.0 Clinical Agentic AI",
    version="2.0"
)

# ===============================================================
# 🌐 CORS CONFIGURATION
# ===============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================================================
# 📦 REQUEST SCHEMA
# ===============================================================

class PatientData(BaseModel):
    name: str = Field(..., example="John Doe")
    features: Dict[str, float]
    glucose: float
    hba1c: float

# ===============================================================
# 🏥 HEALTH CHECK ROUTE
# ===============================================================

@app.get("/")
def root():
    return {
        "status": "SIFRA Backend Running",
        "message": "Agentic Clinical AI Ready"
    }

# ===============================================================
# 🔬 MAIN ANALYSIS ROUTE
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
            "risk_score": result.get("risk_score"),
            "decision": result.get("decision"),
            "report": result.get("report"),
            "evaluation": result.get("evaluation")
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"SIFRA processing error: {str(e)}"
        )
    
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str


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
# ▶ RUN WITH:
# uvicorn backend:app --reload --port 8000
# ===============================================================



@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):

    text_content = ""

    with pdfplumber.open(file.file) as pdf:
        for page in pdf.pages:
            text_content += page.extract_text() + "\n"

    completion = llm.chat.completions.create(
    model="meta-llama-3-8b-instruct",
    messages=[
        {
            "role": "system",
            "content": "You are SIFRA..."
        },
        {
            "role": "user",
            "content": f"Medical Report:\n{text_content}\n\nPlease analyze and give precautionary measures."
        }
    ],
    temperature=0.5
)


    return {
        "reply": completion.choices[0].message.content
    }
