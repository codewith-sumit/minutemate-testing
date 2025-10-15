from google import genai
from google.genai import types
import os
import json

import re



# The summarize_with_gemini function will now accept the model as an argument.
def summarize_with_gemini(transcript_text, gemini_model): # Add gemini_model as an argument
    prompt = f"""
You are a meeting assistant. Return a **valid JSON('you must transcribe in Hinglish if the meeting is in the mix of languages') only**, structured like this — no explanation or extra text:
.
{{
  "transcript": "<transcript should be in Hinglish(roman english for indians) if the meeting is in the mix of languages like Hindi, English, Punjabi, etc.>",
  "summary": "<summary here>",
  "action_items": [
    {{
      "who": "person name",
      "what": "task to do",
      "when": "timeline or deadline"
    }}
  ]
}},when language is in mix of languages, then always must write transcribe in Hinglish only.

Transcript:
{transcript_text}
"""
    try:
        response = gemini_model.generate_content(prompt) # Use the passed gemini_model
        response_text = response.text.strip()

        # Force only JSON response
        data = json.loads(response_text)
        return (
            data.get("transcript", "").strip(),
            data.get("summary", "").strip(),
            data.get("action_items", [])
        )
    except Exception as e:
        print("Gemini Error:", e)
        return transcript_text[:200], "", []

