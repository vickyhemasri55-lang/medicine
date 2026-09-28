import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types

import chatbot_config as config

load_dotenv()

app = Flask(__name__)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def build_contents(messages):
    contents = []
    for message in messages[-config.MAX_HISTORY_MESSAGES:]:
        text = str(message.get("text", "")).strip()
        if not text:
            continue
        role = "model" if message.get("role") == "bot" else "user"
        contents.append(types.Content(role=role, parts=[types.Part(text=text)]))
    return contents


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    contents = build_contents(data.get("messages", []))

    if not contents or contents[-1].role != "user":
        return jsonify({"error": "Please send a message."}), 400

    try:
        response = client.models.generate_content(
            model=config.MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=config.SYSTEM_PROMPT,
                temperature=config.TEMPERATURE,
            ),
        )
        return jsonify({"reply": response.text or config.REFUSAL_MESSAGE})
    except Exception:
        app.logger.exception("Gemini request failed")
        return jsonify({"error": "The server could not reach the model. Please try again."}), 500


if __name__ == "__main__":
    app.run(debug=True)
