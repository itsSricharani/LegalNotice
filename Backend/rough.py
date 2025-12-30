from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import PyPDF2
from openai import OpenAI
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/")
def home():
    return "Backend running"

# ---------- RULE-BASED LOGIC ----------
def rule_based_analysis(text):
    text_lower = text.lower()

    summary_fallback = "This notice asks you to take some action mentioned in the notice."
    intent = "Unknown"
    deadline = "Not found"
    risk = "Unknown"

    if "rent" in text_lower:
        intent = "Recover unpaid rent"
        summary_fallback = "This notice is asking for payment of pending rent."

    deadline_match = re.search(r'within\s+(\d+)\s+days', text_lower)
    if deadline_match:
        deadline = f"Within {deadline_match.group(1)} days"

    if "legal action" in text_lower or "court" in text_lower or "suit" in text_lower:
        risk = "High"
    elif "action may be taken" in text_lower or "action might be taken" in text_lower:
        risk = "Medium"
    elif "notice" in text_lower:
        risk = "Low"


    return summary_fallback, intent, deadline, risk

# ---------- AI SUMMARY ----------
def ai_summary(text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Explain the following legal notice in simple language for a common person. "
                        "Do not give legal advice. Do not add information. "
                        "Only explain what it means."
                    )
                },
                {"role": "user", "content": text}
            ],
            max_tokens=120
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None

# ---------- TEXT ANALYSIS ----------
@app.route("/analyze", methods=["POST"])
def analyze_text():
    data = request.get_json()
    text = data.get("text", "").strip()

    if not text or len(text) < 20:
        return jsonify({
            "summary": "Insufficient information to analyze notice.",
            "risk": "Unknown"
        })

    fallback_summary, intent, deadline, risk = rule_based_analysis(text)

    ai_result = ai_summary(text)
    final_summary = ai_result if ai_result else fallback_summary

    return jsonify({
        "summary": final_summary,
        "intent": intent,
        "deadline": deadline,
        "risk": risk
    })

# ---------- PDF ANALYSIS ----------
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

    if not text or len(text) < 20:
        return jsonify({
            "summary": "Insufficient information to analyze notice.",
            "intent": "Unknown",
            "deadline": "Not found",
            "risk": "Unknown"
        })
    

    fallback_summary, intent, deadline, risk = rule_based_analysis(text)

    ai_result = ai_summary(text)
    final_summary = ai_result if ai_result else fallback_summary

    return jsonify({
        "summary": final_summary,
        "intent": intent,
        "deadline": deadline,
        "risk": risk
    })

if __name__ == "__main__":
    app.run(debug=True)
