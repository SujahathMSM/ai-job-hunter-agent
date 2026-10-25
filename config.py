import os
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Automatically load environment variables from .env file if it exists
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH, override=True)
else:
    load_dotenv()

def update_env_file(updates: Dict[str, str]):
    """Persists key-value settings directly into the local .env file."""
    existing = {}
    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    existing[k.strip()] = v.strip()
    existing.update(updates)
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write("# Environment Configuration for AI Job Hunter Agent\n")
        for k, v in existing.items():
            if v:  # Only write non-empty
                f.write(f"{k}={v}\n")

DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
GENERATED_DIR = DATA_DIR / "generated_cvs"
DRAFTS_DIR = DATA_DIR / "drafts"
DB_PATH = DATA_DIR / "applications.db"
PROFILE_PATH = DATA_DIR / "master_persona.json"

for folder in [DATA_DIR, UPLOADS_DIR, GENERATED_DIR, DRAFTS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# Target Regions Configuration
# 1. Gulf Countries (GCC)
GULF_COUNTRIES: List[str] = [
    "United Arab Emirates", "UAE", "Dubai", "Abu Dhabi", "Sharjah",
    "Saudi Arabia", "KSA", "Riyadh", "Jeddah", "Dammam", "Khobar", "NEOM",
    "Qatar", "Doha",
    "Oman", "Muscat", "Sohar",
    "Kuwait", "Kuwait City",
    "Bahrain", "Manama"
]

# 2. Easily Migratable / High-Opportunity Countries from Sri Lanka
MIGRATABLE_COUNTRIES: List[str] = [
    "Singapore",
    "Malaysia", "Kuala Lumpur",
    "Maldives", "Male",
    "United Kingdom", "UK", "London",
    "Germany", "Berlin", "Munich", "Frankfurt",
    "Australia", "Sydney", "Melbourne", "Brisbane", "Perth",
    "New Zealand", "Auckland", "Wellington",
    "Canada", "Toronto", "Vancouver",
    "Ireland", "Dublin",
    "Netherlands", "Amsterdam"
]

# 3. STRICT EXCLUSION LIST (Hard rule: Zero tolerance)
EXCLUDED_COUNTRIES: List[str] = [
    "Israel", "Tel Aviv", "Jerusalem", "Haifa", "Beer Sheva", "IL"
]

# 4. Structured Regional Scraping Hubs with Localized Indeed Country Domains
EXPANDED_LOCATION_TARGETS = {
    "GULF": [
        {"city": "Dubai", "country": "united arab emirates", "display": "Dubai, UAE"},
        {"city": "Riyadh", "country": "saudi arabia", "display": "Riyadh, Saudi Arabia"},
        {"city": "Abu Dhabi", "country": "united arab emirates", "display": "Abu Dhabi, UAE"},
        {"city": "Doha", "country": "qatar", "display": "Doha, Qatar"},
        {"city": "Jeddah", "country": "saudi arabia", "display": "Jeddah, Saudi Arabia"},
        {"city": "Muscat", "country": "oman", "display": "Muscat, Oman"},
        {"city": "Sharjah", "country": "united arab emirates", "display": "Sharjah, UAE"},
        {"city": "Manama", "country": "bahrain", "display": "Manama, Bahrain"},
        {"city": "Kuwait City", "country": "kuwait", "display": "Kuwait City, Kuwait"},
        {"city": "Dammam", "country": "saudi arabia", "display": "Dammam, Saudi Arabia"},
    ],
    "MIGRATABLE": [
        {"city": "Singapore", "country": "singapore", "display": "Singapore"},
        {"city": "London", "country": "uk", "display": "London, UK"},
        {"city": "Berlin", "country": "germany", "display": "Berlin, Germany"},
        {"city": "Munich", "country": "germany", "display": "Munich, Germany"},
        {"city": "Amsterdam", "country": "netherlands", "display": "Amsterdam, Netherlands"},
        {"city": "Dublin", "country": "ireland", "display": "Dublin, Ireland"},
        {"city": "Sydney", "country": "australia", "display": "Sydney, Australia"},
        {"city": "Melbourne", "country": "australia", "display": "Melbourne, Australia"},
        {"city": "Toronto", "country": "canada", "display": "Toronto, Canada"},
        {"city": "Vancouver", "country": "canada", "display": "Vancouver, Canada"},
        {"city": "Manchester", "country": "uk", "display": "Manchester, UK"},
    ],
    "ALL": [
        {"city": "Dubai", "country": "united arab emirates", "display": "Dubai, UAE"},
        {"city": "Riyadh", "country": "saudi arabia", "display": "Riyadh, Saudi Arabia"},
        {"city": "Singapore", "country": "singapore", "display": "Singapore"},
        {"city": "London", "country": "uk", "display": "London, UK"},
        {"city": "Abu Dhabi", "country": "united arab emirates", "display": "Abu Dhabi, UAE"},
        {"city": "Berlin", "country": "germany", "display": "Berlin, Germany"},
        {"city": "Doha", "country": "qatar", "display": "Doha, Qatar"},
        {"city": "Sydney", "country": "australia", "display": "Sydney, Australia"},
        {"city": "Amsterdam", "country": "netherlands", "display": "Amsterdam, Netherlands"},
        {"city": "Toronto", "country": "canada", "display": "Toronto, Canada"},
        {"city": "Jeddah", "country": "saudi arabia", "display": "Jeddah, Saudi Arabia"},
        {"city": "Dublin", "country": "ireland", "display": "Dublin, Ireland"},
        {"city": "Muscat", "country": "oman", "display": "Muscat, Oman"},
    ]
}

# Engineering Disciplines & Broad Keywords
ENGINEERING_KEYWORDS: List[str] = [
    "engineer", "engineering", "software", "mechanical", "electrical", "civil",
    "systems", "devops", "cloud", "data", "electronics", "mechatronics",
    "automation", "embedded", "qa", "quality", "solutions architect",
    "site reliability", "sre", "hardware", "firmware", "ai", "machine learning",
    "project engineer", "technical lead", "engineering manager", "consultant"
]

# Default LLM Settings
DEFAULT_LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # "gemini", "openai", "claude", "local"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# External Job Search & HR Finding APIs (Optional Free Tiers)
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY", "")
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY", "")

# Default Email / SMTP Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # App Password
SENDER_NAME = os.getenv("SENDER_NAME", "Engineering Candidate")
REPLY_TO = os.getenv("REPLY_TO", "")
SAFE_MODE = os.getenv("SAFE_MODE", "True").lower() in ("true", "1", "yes")  # Review before real sending
