from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Backend running"

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()

    return jsonify({
        "summary": "Analysis not implemented yet",
        "intent": "Unknown",
        "deadline": "Not found",
        "risk": "Unknown"
    })

if __name__ == "__main__":
    app.run(debug=True)
