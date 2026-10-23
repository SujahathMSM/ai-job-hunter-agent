import os
import json
from typing import Optional, Dict, Any, List
import requests
from config import GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY

class LLMClient:
    """Unified LLM client supporting Google Gemini, OpenAI, Claude, and offline intelligent fallback."""

    # Models to try in order of availability and speed
    GEMINI_MODELS = [
        "gemini-flash-lite-latest",
        "gemini-3.8-flash",
        "gemini-flash-latest",
        "gemini-3.5-flash"
    ]

    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or os.getenv("LLM_PROVIDER", "gemini").lower()
        self.gemini_key = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", GEMINI_API_KEY))
        self.openai_key = os.getenv("OPENAI_API_KEY", OPENAI_API_KEY)
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY", ANTHROPIC_API_KEY)

    def is_active(self) -> Dict[str, Any]:
        """Checks if an active LLM provider and API key are configured."""
        if self.provider == "gemini" and self.gemini_key:
            return {"active": True, "provider": "Google Gemini", "key_set": True}
        if self.provider == "openai" and self.openai_key:
            return {"active": True, "provider": "OpenAI", "key_set": True}
        if self.provider == "anthropic" and self.anthropic_key:
            return {"active": True, "provider": "Anthropic Claude", "key_set": True}
        return {"active": False, "provider": "Offline Rule-based Heuristic", "key_set": False}

    def generate(self, prompt: str, system_prompt: str = "You are an elite executive career strategist and technical CV/Cover Letter writer.") -> str:
        # 1. Try Gemini if configured
        if self.provider == "gemini" and self.gemini_key:
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": f"{system_prompt}\n\n{prompt}"}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.4,
                    "maxOutputTokens": 3000
                }
            }

            for model_name in self.GEMINI_MODELS:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.gemini_key}"
                try:
                    res = requests.post(url, json=payload, headers=headers, timeout=30)
                    if res.status_code == 200:
                        data = res.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                text = parts[0].get("text", "").strip()
                                if text:
                                    print(f"[LLM SUCCESS] Model '{model_name}' generated {len(text)} characters.")
                                    return text
                    elif res.status_code in [404, 503]:
                        # Try next model in fallback list
                        continue
                    else:
                        print(f"[LLM Warning] Gemini {model_name} returned {res.status_code}: {res.text[:150]}")
                except Exception as e:
                    print(f"[LLM Error] Error contacting {model_name}: {e}")

        # 2. Try OpenAI if key is provided
        if self.provider == "openai" and self.openai_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=self.openai_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4
                )
                text = response.choices[0].message.content or ""
                if text:
                    print(f"[LLM SUCCESS] OpenAI generated {len(text)} characters.")
                    return text
            except Exception as e:
                print(f"[LLM Error] OpenAI API call failed: {e}")

        # 3. Fallback
        print("[LLM Notice] No live LLM output received; using intelligent local engine.")
        return ""
