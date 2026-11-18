import os
import time
from typing import Optional, Dict, Any, List
import requests
from config import GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY

# CV and cover-letter generations run to a few thousand tokens and routinely take
# 20-60s, so read timeouts must be generous or every call silently falls back offline.
CONNECT_TIMEOUT_S = 5.0
READ_TIMEOUT_S = float(os.getenv("LLM_TIMEOUT_SECONDS", "120"))
MAX_OUTPUT_TOKENS = 8000
# Gemini returns 503/429 when overloaded; these are usually gone within seconds
RETRYABLE_STATUS = {429, 500, 503}
RETRY_BACKOFF_S = (2, 5)


class LLMClient:
    """Unified LLM client supporting Google Gemini, OpenAI, Claude, and offline intelligent fallback
    with automatic provider failover. Model names can be overridden per provider through
    GEMINI_MODEL, OPENAI_MODEL and ANTHROPIC_MODEL."""

    DEFAULT_GEMINI_MODELS = ["gemini-2.5-flash", "gemini-flash-lite-latest"]
    DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
    DEFAULT_ANTHROPIC_MODEL = "claude-opus-5-5"

    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or os.getenv("LLM_PROVIDER", "gemini").lower()
        self.gemini_key = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", GEMINI_API_KEY))
        self.openai_key = os.getenv("OPENAI_API_KEY", OPENAI_API_KEY)
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY", ANTHROPIC_API_KEY)
        self.last_error: str = ""

    @property
    def gemini_models(self) -> List[str]:
        configured = os.getenv("GEMINI_MODEL", "").strip()
        return [configured] if configured else list(self.DEFAULT_GEMINI_MODELS)

    def is_active(self) -> Dict[str, Any]:
        """Checks if an active LLM provider and API key are configured."""
        if self.gemini_key:
            return {"active": True, "provider": "Google Gemini", "key_set": True}
        if self.openai_key:
            return {"active": True, "provider": "OpenAI", "key_set": True}
        if self.anthropic_key:
            return {"active": True, "provider": "Anthropic Claude", "key_set": True}
        return {"active": False, "provider": "Offline Rule-based Heuristic", "key_set": False}

    def generate(
        self,
        prompt: str,
        system_prompt: str = "You are an elite executive career strategist and technical CV/Cover Letter writer.",
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        order = {
            "openai": ["openai", "gemini", "anthropic"],
            "anthropic": ["anthropic", "gemini", "openai"],
        }.get(self.provider, ["gemini", "openai", "anthropic"])
        keys = {"gemini": self.gemini_key, "openai": self.openai_key, "anthropic": self.anthropic_key}
        calls = {
            "gemini": lambda k: self._call_gemini(prompt, system_prompt, k, temperature=temperature),
            "openai": lambda k: self._call_openai(prompt, system_prompt, k),
            "anthropic": lambda k: self._call_anthropic(prompt, system_prompt, k),
        }

        self.last_error = ""
        for name in order:
            if not keys[name]:
                continue
            text = calls[name](keys[name])
            if text:
                return text

        if any(keys.values()):
            print(f"[LLM Notice] All configured providers failed ({self.last_error or 'no output'}); using local fallback.")
        else:
            print("[LLM Notice] No LLM API key configured; using local fallback.")
        return ""

    def _call_gemini(self, prompt: str, system_prompt: str, api_key: str, temperature: Optional[float] = None) -> str:
        # Key goes in a header, never the URL, so it can't leak into proxy or access logs.
        headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature if temperature is not None else 0.4,
                "maxOutputTokens": MAX_OUTPUT_TOKENS,
            },
        }

        for model_name in self.gemini_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
            for attempt, wait in enumerate((0, *RETRY_BACKOFF_S)):
                if wait:
                    time.sleep(wait)
                try:
                    res = requests.post(url, json=payload, headers=headers, timeout=(CONNECT_TIMEOUT_S, READ_TIMEOUT_S))
                except requests.RequestException as e:
                    self.last_error = f"Gemini {model_name}: {type(e).__name__}"
                    print(f"[LLM Error] {self.last_error}")
                    break
                if res.status_code == 404:
                    break  # Model not available for this key, try the next one
                if res.status_code in RETRYABLE_STATUS and attempt < len(RETRY_BACKOFF_S):
                    print(f"[LLM Notice] Gemini {model_name} busy (HTTP {res.status_code}); retrying in {RETRY_BACKOFF_S[attempt]}s")
                    continue
                if res.status_code != 200:
                    self.last_error = f"Gemini {model_name} HTTP {res.status_code}"
                    print(f"[LLM Warning] {self.last_error}: {res.text[:200]}")
                    break
                candidates = res.json().get("candidates", [])
                parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
                text = "".join(p.get("text", "") for p in parts).strip()
                if text:
                    print(f"[LLM SUCCESS] Gemini '{model_name}' generated {len(text)} characters.")
                    return text
                self.last_error = f"Gemini {model_name} returned no text"
                break
        return ""

    def _call_openai(self, prompt: str, system_prompt: str, api_key: str) -> str:
        try:
            from openai import OpenAI
        except ImportError:
            self.last_error = "openai package not installed"
            return ""
        try:
            client = OpenAI(api_key=api_key, timeout=READ_TIMEOUT_S)
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", self.DEFAULT_OPENAI_MODEL),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4
            )
            text = (response.choices[0].message.content or "").strip()
            if text:
                print(f"[LLM SUCCESS] OpenAI generated {len(text)} characters.")
            return text
        except Exception as e:
            self.last_error = f"OpenAI: {type(e).__name__}"
            print(f"[LLM Error] OpenAI API call failed: {e}")
        return ""

    def _call_anthropic(self, prompt: str, system_prompt: str, api_key: str) -> str:
        try:
            import anthropic
        except ImportError:
            self.last_error = "anthropic package not installed"
            return ""

        model = os.getenv("ANTHROPIC_MODEL", self.DEFAULT_ANTHROPIC_MODEL)
        client = anthropic.Anthropic(api_key=api_key, timeout=READ_TIMEOUT_S)
        try:
            # Server-side fallback: if the model declines on a policy check, the API
            # re-runs the request on a suitable model within the same call.
            response = client.beta.messages.create(
                model=model,
                max_tokens=MAX_OUTPUT_TOKENS,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
                output_config={"effort": "medium"},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except anthropic.NotFoundError:
            self.last_error = f"Anthropic model '{model}' not found"
            print(f"[LLM Error] {self.last_error}")
            return ""
        except anthropic.AuthenticationError:
            self.last_error = "Anthropic API key rejected"
            print(f"[LLM Error] {self.last_error}")
            return ""
        except anthropic.RateLimitError:
            self.last_error = "Anthropic rate limited"
            print(f"[LLM Error] {self.last_error}")
            return ""
        except anthropic.APIStatusError as e:
            self.last_error = f"Anthropic HTTP {e.status_code}"
            print(f"[LLM Error] {self.last_error}: {e.message}")
            return ""
        except anthropic.APIConnectionError as e:
            self.last_error = f"Anthropic connection error: {type(e).__name__}"
            print(f"[LLM Error] {self.last_error}")
            return ""

        if response.stop_reason == "refusal":
            self.last_error = "Anthropic declined the request"
            print(f"[LLM Warning] {self.last_error}")
            return ""
        text = "".join(b.text for b in response.content if b.type == "text").strip()
        if text:
            print(f"[LLM SUCCESS] Claude '{response.model}' generated {len(text)} characters.")
        return text
