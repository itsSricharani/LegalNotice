import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2
import re
import json

app = Flask(__name__)
CORS(app)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "arcee-ai/trinity-mini:free"

@app.route("/")
def home():
    return "Backend running (rule-based mode)"

def extract_deadline(text):
    match = re.search(r'within\s+(\d+)\s+days', text.lower())
    if match:
        return f"Within {match.group(1)} days"
    return "Not found"

def rule_based_analysis(text):
    text_lower = text.lower()

    summary = "This notice asks you to take certain actions mentioned in the document."
    intent = "Unknown"
    risk = "Unknown"

    if "rent" in text_lower or "lease" in text_lower:
        intent = "The intent is Recovery of unpaid rent"
        summary = "The notice demands payment of pending rent or lease dues."

    elif "electricity" in text_lower or "bill" in text_lower or "outstanding" in text_lower or "pending dues" in text_lower :
        intent = "The intent is Payment of pending dues"
        summary = "The notice demands payment of outstanding dues or bills."


    elif "loan" in text_lower or "emi" in text_lower or "interest" in text_lower or "bank" in text_lower:
        intent = "The intent is Loan repayment demand"
        summary = "The notice demands repayment of a loan or instalments."
    
    elif "breach" in text_lower or "non-fulfilment" in text_lower or "terminat" in text_lower:
        intent = "The intent is Contract or agreement violation"
        summary = "The notice refers to a breach or violation of agreed terms."

    elif "non-compliance" in text_lower or "penalty" in text_lower or "violation of regulation" in text_lower or "statutory" in text_lower:
        intent = "The intent is Compliance violation"
        summary = "The notice highlights a regulatory or statutory compliance issue."
    
    elif "traffic" in text_lower or "vehicle" in text_lower or "registration" in text_lower or "fine" in text_lower:
        intent = "The Intent is Traffic or vehicle fine"
        summary = "The notice informs about a traffic or vehicle fine."

    elif "defaulter" in text_lower or "recovery" in text_lower or "final notice" in text_lower:
        intent = "The Intent is Recovery / defaulter demand"
        summary = "The notice demands settlement of overdue accounts."

    
    if "legal action" in text_lower or "court" in text_lower or "suit" in text_lower or "liable" in text_lower or  "proceedings" in text_lower or "penalty" in text_lower:
        risk = "The Risk Factor is High"
    elif "failure to comply" in text_lower or "will be initiated" in text_lower:
        risk = "The Risk Factor is Medium"
    else:
        risk = "The Risk Factor is Low"

    return intent, summary, risk

def ai_based_analysis(text):
    if not OPENROUTER_API_KEY:
        raise Exception("Missing OpenRouter API key")

    prompt = f"""
You are a legal notice analyzer.

Analyze the following legal notice and return ONLY valid JSON in this exact format:

{{
  "summary": "...",
  "intent": "...",
  "deadline": "...",
  "risk": "Low | Medium | High"
}}

Legal notice:
{text}
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "LegalNoticeAnalyzer"
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    response = requests.post(
        OPENROUTER_URL,
        headers=headers,
        json=payload,
        timeout=20
    )

    response.raise_for_status()
    data = response.json()

    content = data["choices"][0]["message"]["content"]
    return json.loads(content)


@app.route("/analyze", methods=["POST"])
def analyze_text():
    data = request.get_json()
    text = data.get("text", "").strip()

    if not text or len(text) < 20:
        return jsonify({
            "summary": "Insufficient information to analyze notice.",
            "intent": "Unknown",
            "deadline": "Not found",
            "risk": "Unknown"
        })

   
    try:
        ai_result = ai_based_analysis(text)
        return jsonify(ai_result)

    except Exception as e:
        deadline = extract_deadline(text)
        intent, summary, risk = rule_based_analysis(text)

        return jsonify({
            "summary": summary,
            "intent": intent,
            "deadline": deadline,
            "risk": risk
        })


@app.route("/analyze-pdf", methods=["POST"])
def analyze_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    reader = PyPDF2.PdfReader(file)

    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"

    if len(text.strip()) == 0:
        return jsonify({
            "summary": "The PDF is not text-extractable.",
            "intent": "Unknown",
            "deadline": "Not found",
            "risk": "Unknown"
        })

    try:
        ai_result = ai_based_analysis(text)
        return jsonify(ai_result)

    except Exception as e:
        deadline = extract_deadline(text)
        intent, summary, risk = rule_based_analysis(text)

        return jsonify({
            "summary": summary,
            "intent": intent,
            "deadline": deadline,
            "risk": risk
        })

if __name__ == "__main__":
    app.run(debug=True)
