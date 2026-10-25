import os
import json
from typing import Optional, Dict, Any, List
import requests
from config import GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY

import os
import json
import time
from typing import Optional, Dict, Any, List
import requests
from config import GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY

class LLMClient:
    """Unified LLM client supporting Google Gemini, OpenAI, Claude, and offline intelligent fallback
    with automatic provider failover and retry logic."""

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
        if self.gemini_key:
            return {"active": True, "provider": "Google Gemini", "key_set": True}
        if self.openai_key:
            return {"active": True, "provider": "OpenAI", "key_set": True}
        if self.anthropic_key:
            return {"active": True, "provider": "Anthropic Claude", "key_set": True}
        return {"active": False, "provider": "Offline Rule-based Heuristic", "key_set": False}

    def generate(self, prompt: str, system_prompt: str = "You are an elite executive career strategist and technical CV/Cover Letter writer.") -> str:
        # Determine sequence of providers to try based on preference
        providers = []
        if self.provider == "openai":
            providers = [("openai", self.openai_key), ("gemini", self.gemini_key), ("anthropic", self.anthropic_key)]
        elif self.provider == "anthropic":
            providers = [("anthropic", self.anthropic_key), ("gemini", self.gemini_key), ("openai", self.openai_key)]
        else:
            providers = [("gemini", self.gemini_key), ("openai", self.openai_key), ("anthropic", self.anthropic_key)]

        for prov_name, key in providers:
            if not key:
                continue

            if prov_name == "gemini":
                text = self._call_gemini(prompt, system_prompt, key)
                if text:
                    return text
            elif prov_name == "openai":
                text = self._call_openai(prompt, system_prompt, key)
                if text:
                    return text
            elif prov_name == "anthropic":
                text = self._call_anthropic(prompt, system_prompt, key)
                if text:
                    return text

        # Fallback to local heuristic
        print("[LLM Notice] No live LLM output received; using intelligent local engine.")
        return ""

    def _call_gemini(self, prompt: str, system_prompt: str, api_key: str) -> str:
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
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            for attempt in range(2):
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
                    elif res.status_code in [429, 503]:
                        time.sleep(1.5 * (attempt + 1))
                        continue
                    elif res.status_code == 404:
                        break  # Model not found, try next model
                    else:
                        print(f"[LLM Warning] Gemini {model_name} returned {res.status_code}: {res.text[:120]}")
                        break
                except Exception as e:
                    print(f"[LLM Error] Error contacting {model_name}: {e}")
                    time.sleep(1)
        return ""

    def _call_openai(self, prompt: str, system_prompt: str, api_key: str) -> str:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
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
                return text.strip()
        except Exception as e:
            print(f"[LLM Error] OpenAI API call failed: {e}")
        return ""

    def _call_anthropic(self, prompt: str, system_prompt: str, api_key: str) -> str:
        try:
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            payload = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 3000,
                "system": system_prompt,
                "messages": [{"role": "user", "content": prompt}]
            }
            resp = requests.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("content", [])
                if content and "text" in content[0]:
                    return content[0]["text"].strip()
        except Exception as e:
            print(f"[LLM Error] Anthropic API call failed: {e}")
        return ""
