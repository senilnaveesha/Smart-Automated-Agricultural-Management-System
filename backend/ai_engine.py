import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "mistral:7b-instruct-q4_0"


# 🧠 Build Prompt
def build_prompt(data):
    return f"""
You are an agricultural AI advisor.

You MUST use the provided sensor data in your reasoning.

STRICT RULES:
- ALWAYS mention the sensor values in your answer
- ALWAYS explain WHY you made the decision
- NEVER give general advice without using numbers
- Base every answer on the data below

Decision Rules:
- If soil moisture > 70% → Do NOT water
- If soil moisture < 30% → Recommend watering
- If temperature > 32°C → Mention heat stress
- If temperature < 15°C → Mention cold stress

If the user asks about current conditions:
→ Return exact values clearly

Respond ONLY in JSON:

{{
  "mode": "analysis",
  "problem": "",
  "explanation": "",
  "recommended_actions": [],
  "urgency": "Low/Medium/High"
}}

REAL SENSOR DATA:
- Soil Moisture: {data.get('soil')}%
- Temperature: {data.get('temp')}°C
- Rain: {data.get('rain')}
- Crop: {data.get('crop')}

User Question:
{data.get('user_query')}
"""


# 🧹 Extract JSON safely
def extract_json(text):
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        json_str = text[start:end]
        return json.loads(json_str)
    except Exception:
        return None


# 🚀 Main AI function
def get_ai_response(data):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": build_prompt(data),
                "stream": False
            },
            timeout=30  # 🔥 prevent hanging
        )

        # 🔍 Check HTTP response
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}"}

        result = response.json()

        # 🔥 Safety check
        if "response" not in result:
            return {"error": "Invalid Ollama response"}

        raw = result["response"]

        parsed = extract_json(raw)

        if not parsed:
            return {
                "error": "Invalid AI JSON",
                "raw": raw
            }

        # ✅ Ensure safe defaults (VERY IMPORTANT)
        parsed.setdefault("mode", "analysis")
        parsed.setdefault("response", "")
        parsed.setdefault("problem", "")
        parsed.setdefault("recommended_actions", [])
        parsed.setdefault("urgency", "Low")

        # 🔥 Fix crash (convert everything to string)
        if isinstance(parsed["recommended_actions"], list):
            parsed["recommended_actions"] = [
                str(action) for action in parsed["recommended_actions"]
            ]
        else:
            parsed["recommended_actions"] = [str(parsed["recommended_actions"])]

        return parsed

    except requests.exceptions.RequestException as e:
        return {"error": f"Connection error: {str(e)}"}

    except Exception as e:
        return {"error": str(e)}