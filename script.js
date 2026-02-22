/* ============================================================
   SIFRA 2.0 — Fully Integrated UI + FastAPI Backend
============================================================ */

const API_ENDPOINT = "http://127.0.0.1:8000/analyze";
const CHAT_API     = "http://127.0.0.1:8000/chat";
const GAUGE_TOTAL  = 251.3;

/* ================== ELEMENT REFERENCES ================== */
const form           = document.getElementById("sifra-form");
const submitBtn      = document.getElementById("submit-btn");
const loadingOverlay = document.getElementById("loading-overlay");
const resultsPanel   = document.getElementById("results-panel");
const errorCard      = document.getElementById("error-card");
const errorMsg       = document.getElementById("error-msg");

const gaugeFill  = document.getElementById("gauge-fill");
const gaugeValue = document.getElementById("gauge-value");
const riskLabel  = document.getElementById("risk-label");

const textDecision = document.getElementById("text-decision");
const textReport   = document.getElementById("text-report");
const textEval     = document.getElementById("text-eval");

/* ================== TOGGLE BUTTON LOGIC ================== */
document.querySelectorAll(".toggle-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const field = btn.dataset.field;
    const value = btn.dataset.value;

    document.querySelectorAll(`.toggle-btn[data-field="${field}"]`)
      .forEach(b => b.classList.remove("active"));

    btn.classList.add("active");

    const hidden = document.getElementById(field);
    if (hidden) hidden.value = value;
  });
});

/* ================== COLLECT FORM DATA ================== */
function collectPayload() {
  return {
    name: form.name.value.trim(),
    glucose: parseFloat(form.glucose.value),
    hba1c: parseFloat(form.hba1c.value),
    features: {
      HighBP: parseInt(document.getElementById("highbp").value),
      HighChol: parseInt(document.getElementById("highchol").value),
      CholCheck: parseInt(document.getElementById("cholcheck").value),
      BMI: parseFloat(form.bmi.value),
      Smoker: parseInt(document.getElementById("smoker").value),
      Stroke: parseInt(document.getElementById("stroke").value),
      HeartDiseaseorAttack: parseInt(document.getElementById("heartdisease").value),
      PhysActivity: parseInt(document.getElementById("physactivity").value),
      Fruits: parseInt(document.getElementById("fruits").value),
      Veggies: parseInt(document.getElementById("veggies").value),
      HvyAlcoholConsump: parseInt(document.getElementById("hvyalcohol").value),
      AnyHealthcare: parseInt(document.getElementById("anyhealthcare").value),
      NoDocbcCost: parseInt(document.getElementById("nodocbccost").value),
      GenHlth: parseInt(form.genhlth.value),
      MentHlth: parseInt(form.menthlth.value),
      PhysHlth: parseInt(form.physhlth.value),
      DiffWalk: parseInt(document.getElementById("diffwalk").value),
      Sex: parseInt(form.sex.value),
      Age: parseInt(form.age.value),
      Education: parseInt(form.education.value),
      Income: parseInt(form.income.value)
    }
  };
}

/* ================== GAUGE ================== */
function animateGauge(percent) {
  const offset = GAUGE_TOTAL * (1 - percent / 100);
  gaugeFill.style.strokeDashoffset = offset;
  gaugeValue.textContent = percent;

  if (percent < 30) {
    riskLabel.textContent = "Low Risk";
    gaugeFill.style.stroke = "#10b981"; // Green
  } 
  else if (percent < 60) {
    riskLabel.textContent = "Moderate Risk";
    gaugeFill.style.stroke = "#f59e0b"; // Yellow
  } 
  else {
    riskLabel.textContent = "High Risk";
    gaugeFill.style.stroke = "#ef4444"; // Red
  }
}


/* ================== LOADING ================== */
function showLoading() {
  loadingOverlay.hidden = false;
  submitBtn.disabled = true;
}

function hideLoading() {
  loadingOverlay.hidden = true;
  submitBtn.disabled = false;
}

function showError(msg) {
  errorMsg.textContent = msg;
  errorCard.hidden = false;
}

/* ================== RENDER RESULTS ================== */

function formatMarkdown(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>") // Bold
    .replace(/\n/g, "<br>"); // Line breaks
}


function renderResults(data) {

  const percent = Math.round(Number(data.risk_score) * 100);

  animateGauge(percent);

  textDecision.innerHTML = formatMarkdown(data.decision || "—");
  textReport.innerHTML   = formatMarkdown(data.report || "—");
  textEval.innerHTML     = formatMarkdown(data.evaluation || "—");

  resultsPanel.hidden = false;
}


/* ================== FORM SUBMIT ================== */
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  errorCard.hidden = true;

  let payload;
  try {
    payload = collectPayload();
  } catch {
    showError("Invalid form data.");
    return;
  }

  showLoading();

  try {
    const response = await fetch(API_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const result = await response.json();
    console.log("FULL BACKEND RESPONSE:", result);

    if (!result || !result.success) {
      showError("Backend returned invalid data.");
      console.log("Problematic response:", result);
      return;
    }

    hideLoading();
    renderResults(result);


  } catch (err) {
    hideLoading();
    showError("Cannot connect to SIFRA backend.");
    console.error(err);
  }
});


/* ================== CHATBOT ================== */

/* ================== CHATBOT ================== */

async function sendChatMessage(message) {
  try {
    const response = await fetch(CHAT_API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    });

    const data = await response.json();
    return data.reply || "No response.";

  } catch (err) {
    console.error(err);
    return "Chat service unavailable.";
  }
}

const pdfBtn = document.getElementById("pdf-btn");
const pdfUpload = document.getElementById("pdf-upload");

pdfBtn.addEventListener("click", () => {
  pdfUpload.click();
});

pdfUpload.addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  addChatMessage("📄 Analyzing your medical report...", "bot-message");

  const response = await fetch("http://127.0.0.1:8000/upload-pdf", {
    method: "POST",
    body: formData
  });

  const data = await response.json();
  addChatMessage(data.reply, "bot-message");
});


const chatFab = document.getElementById("chat-fab");
const chatWindow = document.getElementById("chat-window");
const chatCloseBtn = document.getElementById("chat-close-btn");
const chatInput = document.getElementById("chat-input");
const chatSendBtn = document.getElementById("chat-send-btn");
const chatMessages = document.getElementById("chat-messages");
const suggestionChips = document.querySelectorAll(".suggestion-chip");

chatFab.addEventListener("click", () => {
  chatWindow.hidden = !chatWindow.hidden;
});

chatCloseBtn.addEventListener("click", () => {
  chatWindow.hidden = true;
});

function addChatMessage(text, type) {
  const msg = document.createElement("div");
  msg.className = `chat-message ${type}`;
  msg.innerHTML = formatMarkdown(text);
  chatMessages.appendChild(msg);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function handleSend() {
  const message = chatInput.value.trim();
  if (!message) return;

  addChatMessage(message, "user-message");
  chatInput.value = "";

  addChatMessage("Typing...", "bot-message");

  const reply = await sendChatMessage(message);

  chatMessages.lastChild.remove();
  addChatMessage(reply, "bot-message");
}

chatSendBtn.addEventListener("click", handleSend);

chatInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    handleSend();
  }
});

suggestionChips.forEach(chip => {
  chip.addEventListener("click", () => {
    chatInput.value = chip.dataset.msg;
    handleSend();
  });
});

window.addEventListener("DOMContentLoaded", () => {
  addChatMessage("Hello 👋 I am <strong>SIFRA</strong>. Ask me any clinical question.", "bot-message");
});
