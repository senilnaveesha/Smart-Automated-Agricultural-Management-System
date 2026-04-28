import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "mistral:7b-instruct-q4_0"


def build_prompt(data):
    disease_summary = data.get("disease_summary")
    disease_summary_block = ""

    if disease_summary:
        disease_counts = disease_summary.get("disease_counts", {})
        disease_lines = "\n".join(
            [f"- {k}: {v}" for k, v in disease_counts.items()]
        ) if disease_counts else "- None"

        detected_diseases = disease_summary.get("detected_diseases", [])
        detected_display = ", ".join(detected_diseases) if detected_diseases else "None"

        disease_summary_block = f"""

FIELD DISEASE SCAN SUMMARY:
- Total scanned points: {disease_summary.get('total_points')}
- Healthy count: {disease_summary.get('healthy_count')}
- Diseased count: {disease_summary.get('diseased_count')}
- Healthy percent: {disease_summary.get('healthy_percent')}%
- Diseased percent: {disease_summary.get('diseased_percent')}%
- Overall field health: {disease_summary.get('overall_field_health')}
- Most common disease: {disease_summary.get('most_common_disease')}
- Detected diseases: {detected_display}

DETECTED DISEASE TYPE COUNTS:
{disease_lines}
"""

    return f"""
You are an agricultural AI advisor for a smart tea farming system.

You must choose exactly one mode:

1. "chat"
Use this for greetings, identity questions, capability questions, or general conversation.

2. "analysis"
Use this for farming advice, crop decisions, watering, temperature stress, rain impact, disease interpretation, or current field condition questions.

Important rules:
- Respond with ONLY valid JSON.
- Do not use markdown.
- Do not add text before or after the JSON.
- If mode is "chat", fill only:
  - mode
  - response
- If mode is "analysis", fill:
  - mode
  - problem
  - explanation
  - recommended_actions
  - urgency
- In analysis mode, use the sensor values and disease scan summary when available.
- In analysis mode, mention numbers when relevant.
- In analysis mode, mention detected disease names when relevant.
- Do not claim a threshold was crossed if it was not.
- Keep recommendations practical for a farmer.

Decision guidance:
- If soil moisture > 70%: avoid watering
- If soil moisture < 30%: recommend watering
- If temperature > 32°C: mention heat stress risk
- If temperature < 15°C: mention cold stress risk
- If rain is "Yes": consider reduced watering need
- If disease is not "None" or scan summary shows disease presence: mention disease concern in analysis mode

Return one of these JSON formats only:

For chat:
{{
  "mode": "chat",
  "response": ""
}}

For analysis:
{{
  "mode": "analysis",
  "problem": "",
  "explanation": "",
  "recommended_actions": [],
  "urgency": "Low"
}}

REAL SENSOR DATA:
- Soil Moisture: {data.get('soil')}%
- Temperature: {data.get('temp')}°C
- Rain: {data.get('rain')}
- Crop: {data.get('crop')}
- Disease: {data.get('disease', 'None')}

{disease_summary_block}

User Question:
{data.get('user_query')}
""".strip()


def clean_response_text(text: str) -> str:
    text = text.strip()

    if text.startswith("```json"):
        text = text[len("```json"):].strip()
    elif text.startswith("```"):
        text = text[len("```"):].strip()

    if text.endswith("```"):
        text = text[:-3].strip()

    return text


def extract_json(text):
    try:
        cleaned = clean_response_text(text)
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1

        if start == -1 or end == 0:
            return None

        json_str = cleaned[start:end]
        return json.loads(json_str)
    except Exception:
        return None


def normalize_ai_result(parsed: dict) -> dict:
    mode = str(parsed.get("mode", "analysis")).strip().lower()

    if mode == "chat":
        return {
            "mode": "chat",
            "response": str(parsed.get("response", "")).strip()
        }

    recommended_actions = parsed.get("recommended_actions", [])
    if isinstance(recommended_actions, list):
        recommended_actions = [
            str(action).strip()
            for action in recommended_actions
            if str(action).strip()
        ]
    else:
        recommended_actions = [str(recommended_actions).strip()] if str(recommended_actions).strip() else []

    urgency = str(parsed.get("urgency", "Low")).strip()
    if urgency.lower() not in {"low", "medium", "high"}:
        urgency = "Low"
    else:
        urgency = urgency.capitalize()

    return {
        "mode": "analysis",
        "problem": str(parsed.get("problem", "")).strip(),
        "explanation": str(parsed.get("explanation", "")).strip(),
        "recommended_actions": recommended_actions,
        "urgency": urgency,
    }


def fallback_response(data, raw_text=""):
    user_query = str(data.get("user_query", "")).strip().lower()

    chat_keywords = {
        "hi", "hello", "hey", "who are you", "what are you",
        "what can you do", "help", "good morning", "good evening"
    }

    if user_query in chat_keywords or any(
        phrase in user_query for phrase in ["who are you", "what can you do"]
    ):
        return {
            "mode": "chat",
            "response": (
                "I am your offline agricultural AI advisor. I can help interpret "
                "soil moisture, temperature, rain conditions, crop status, and disease scan results "
                "to support decisions for your tea field."
            )
        }

    cleaned = clean_response_text(raw_text).strip()
    if cleaned:
        return {
            "mode": "chat",
            "response": cleaned
        }

    return {
        "mode": "chat",
        "response": (
            "I could not generate a structured farm analysis for that question, "
            "but I am ready to help with crop and field advice."
        )
    }


def get_ai_response(data):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": build_prompt(data),
                "stream": False
            },
            timeout=60
        )

        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}: {response.text}"}

        result = response.json()

        if "response" not in result:
            return {"error": "Invalid Ollama response: missing 'response' field"}

        raw = result["response"]
        parsed = extract_json(raw)

        if parsed:
            normalized = normalize_ai_result(parsed)

            if normalized["mode"] == "analysis":
                if (
                    not normalized["problem"]
                    and not normalized["explanation"]
                    and not normalized["recommended_actions"]
                ):
                    return fallback_response(data, raw)

            if normalized["mode"] == "chat" and not normalized["response"]:
                return fallback_response(data, raw)

            return normalized

        return fallback_response(data, raw)

    except requests.exceptions.RequestException as e:
        return {"error": f"Connection error: {str(e)}"}

    except Exception as e:
        return {"error": str(e)}