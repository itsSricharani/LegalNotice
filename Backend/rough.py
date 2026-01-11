"""from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import PyPDF2
from openai import OpenAI
import re
import json
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/")
def home():
    return "Backend running"

def extract_deadline(text):
    match = re.search(r'within\s+(\d+)\s+days', text.lower())
    if match:
        return f"Within {match.group(1)} days"
    return "Not found"

def ai_extract_fields(text):
    

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract information from the legal notice.\n\n"
                        "Return ONLY valid JSON with these keys:\n"
                        "intent (5–6 words), summary (10–15 words), risk (Low, Medium, or High).\n\n"
                        "Do not add extra text."
                    )
                },
                {"role": "user", "content": text}
            ],
            max_tokens=120
        )

        content = response.choices[0].message.content.strip()
        print("RAW AI OUTPUT:\n", content)
        data = json.loads(content)

        intent = data.get("intent", "Unknown")
        summary = data.get("summary", "Unknown")
        risk = data.get("risk", "Unknown")

        if risk not in ["Low", "Medium", "High"]:
            risk = "Unknown"

        return intent, summary, risk

    except Exception as e:
        print("AI extraction failed:", e)
        return "Unknown", "Unknown", "Unknown"

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

    deadline = extract_deadline(text)
    intent, summary, risk = ai_extract_fields(text)

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

    print("Extracted length:", len(text))

    if len(text.strip()) == 0:
        return jsonify({
            "summary": "The PDF is not text-extractable.",
            "intent": "Unknown",
            "deadline": "Not found",
            "risk": "Unknown"
        })

    deadline = extract_deadline(text)
    intent, summary, risk = ai_extract_fields(text)

    return jsonify({
        "summary": summary,
        "intent": intent,
        "deadline": deadline,
        "risk": risk
    })

if __name__ == "__main__":
    app.run(debug=True)
"""
"""from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2
import re

app = Flask(__name__)
CORS(app)

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
        intent = "Recovery of unpaid rent"
        summary = "The notice demands payment of pending rent amounts."

    elif "loan" in text_lower or "emi" in text_lower or "bank" in text_lower:
        intent = "Loan repayment demand"
        summary = "The notice demands repayment of a loan or dues."

    elif "termination" in text_lower:
        intent = "Termination of agreement"
        summary = "The notice informs termination of an existing agreement."

    elif "eviction" in text_lower:
        intent = "Eviction notice"
        summary = "The notice warns about eviction from the premises."

    elif "breach" in text_lower:
        intent = "Breach of contract"
        summary = "The notice alleges breach of contractual terms."

    
    if "legal action" in text_lower or "court" in text_lower or "suit" in text_lower:
        risk = "High"
    elif "failure to comply" in text_lower or "shall be liable" in text_lower:
        risk = "Medium"
    elif "notice" in text_lower:
        risk = "Low"

    return intent, summary, risk

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
"""