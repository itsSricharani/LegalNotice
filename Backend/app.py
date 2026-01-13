from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2
import re
import os
import requests
import json

app = Flask(__name__)
CORS(app)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

@app.route("/")
def home():
    return "Backend running (AI + rule-based fallback mode)"


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
        summary = "The notice demands payment of pending rent or lease dues."

    elif "electricity" in text_lower or "bill" in text_lower or "outstanding" in text_lower:
        intent = "Payment of pending dues"
        summary = "The notice demands payment of outstanding dues or bills."

    elif "loan" in text_lower or "emi" in text_lower or "bank" in text_lower:
        intent = "Loan repayment demand"
        summary = "The notice demands repayment of a loan or instalments."

    elif "breach" in text_lower or "terminat" in text_lower:
        intent = "Contract or agreement violation"
        summary = "The notice refers to a breach or violation of agreed terms."

    elif "non-compliance" in text_lower or "penalty" in text_lower or "statutory" in text_lower:
        intent = "Compliance violation"
        summary = "The notice highlights a regulatory or statutory compliance issue."

    if "legal action" in text_lower or "court" in text_lower or "proceedings" in text_lower:
        risk = "High"
    elif "failure to comply" in text_lower:
        risk = "Medium"
    else:
        risk = "Low"

    return intent, summary, risk


def ai_analysis(text):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "arcee-ai/trinity-mini:free",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a legal notice analyzer.\n"
                    "Return ONLY valid JSON with these keys:\n"
                    "summary, intent, deadline, risk\n\n"
                    "Rules:\n"
                    "- Infer deadlines even if approximate (e.g. 'about 15 days').\n"
                    "- Risk must be Low, Medium, or High.\n"
                    "- Keep language simple.\n"
                    "- No explanations. JSON only."
                )
            },
            {
                "role": "user",
                "content": text
            }
        ]
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=15
    )

    response.raise_for_status()
    result = response.json()

    raw_content = result["choices"][0]["message"]["content"]

    # LOG FOR DEBUGGING
    print("AI RAW RESPONSE:\n", raw_content)

    parsed = json.loads(raw_content)

    return {
        "summary": parsed.get("summary", "Unknown"),
        "intent": parsed.get("intent", "Unknown"),
        "deadline": parsed.get("deadline", "Not found"),
        "risk": parsed.get("risk", "Unknown")
    }



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

    # TRY AI FIRST
    if OPENROUTER_API_KEY:
        try:
            ai_result = ai_analysis(text)
            #return jsonify(ai_result)
            #ai_result["source"] = "AI"
            return jsonify(ai_result)

        except Exception as e:
            print("AI failed, falling back:", e)

    # FALLBACK TO RULE-BASED
    deadline = extract_deadline(text)
    intent, summary, risk = rule_based_analysis(text)

    return jsonify({
        "summary": summary,
        "intent": intent,
        "deadline": deadline,
        "risk": risk,
        
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

    if OPENROUTER_API_KEY:
        try:
            ai_result = ai_analysis(text)
            return jsonify(ai_result)
        except Exception as e:
            print("AI failed, falling back:", e)

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
