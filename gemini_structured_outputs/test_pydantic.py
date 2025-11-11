import os, re, json
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import Optional, Literal

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Pydantic model just for post-parse validation
class ModerationResult(BaseModel):
    decision: Literal["spam", "not_spam"]
    reason: Optional[str] = None
    spam_type: Optional[Literal["phishing", "scam", "unsolicited promotion", "other"]] = None
    summary: Optional[str] = None
    is_safe: Optional[bool] = None

# SDK-friendly schema (no "default", no "discriminator")
RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "decision": {"type": "STRING", "enum": ["spam", "not_spam"]},
        "reason":   {"type": "STRING"},
        "spam_type":{"type": "STRING", "enum": ["phishing","scam","unsolicited promotion","other"]},
        "summary":  {"type": "STRING"},
        "is_safe":  {"type": "BOOLEAN"},
    },
    "required": ["decision"],
}

prompt = """
Please moderate the following content and provide a decision.
Content: 'Congratulations! You've won a free cruise to the Bahamas. Click here to claim your prize: www.definitely-not-a-scam.com'
"""

model = genai.GenerativeModel("gemini-2.5-flash")

resp = model.generate_content(
    prompt,
    generation_config={
        "temperature": 0,
        "response_mime_type": "application/json",
        "response_schema": RESPONSE_SCHEMA,  # <- dict, not Pydantic class
    },
)

# Prefer structured/parsed; fall back to text -> JSON -> Pydantic
parsed = getattr(resp, "parsed", None)
if parsed is None:
    raw = resp.text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n|\n```$", "", raw)
    parsed = json.loads(raw)

result = ModerationResult(**parsed)
print(result)

# Sanity checks
if result.decision == "spam":
    if not (result.reason and result.spam_type):
        raise ValueError("Spam requires 'reason' and 'spam_type'.")
else:
    if not (result.summary is not None and result.is_safe is not None):
        raise ValueError("Not-spam requires 'summary' and 'is_safe'.")
