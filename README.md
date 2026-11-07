# 🎯 NexusHunt AI - Autonomous Career & Job Matching Agent

An end-to-end autonomous AI career agent and global job hunter engineered for technical professionals seeking worldwide remote and international opportunities (GCC / Gulf, Europe, UK, Australasia, and the Americas).

The agent ingests your existing CVs, chat histories (ChatGPT, Claude, Gemini), and LinkedIn profile to deeply understand your technical background, problem-solving mindset, and personal voice. It then identifies matching engineering jobs, tailors ATS-optimized CVs & Cover Letters, compiles publication-quality PDFs, and generates structured outreach packages.

---

## 🌍 Geographic Strategy & Strict Policies

### 1. Gulf Countries (GCC Focus)
- **United Arab Emirates (UAE)**: Dubai, Abu Dhabi, Sharjah
- **Saudi Arabia (KSA)**: Riyadh, Jeddah, Dammam, NEOM Mega-Projects
- **Qatar**: Doha, Lusail
- **Oman, Kuwait, & Bahrain**

### 2. High-Opportunity & Migratable Pathways
- **Southeast Asia**: Singapore, Malaysia
- **Europe & UK**: United Kingdom (Skilled Worker), Germany (Opportunity Card / EU Blue Card), Netherlands, Ireland
- **Australasia**: Australia, New Zealand
- **North America**: Canada, USA (Worldwide Remote)

### 3. Strict Exclusion Rule (Hardcoded Zero-Tolerance)
- **Prohibited Regions**: Any job posting located in or affiliated with Israel is automatically identified and rejected by the filtering engine with zero exceptions.

---

## 🏗️ Architecture & Modules

```
ai-job-hunter-agent/
├── api.py                      # FastAPI Backend Server (REST & Streaming SSE)
├── start.bat                   # Unified Launcher for Backend + Frontend
├── config.py                   # Configuration, target regions & strict exclusion rules
├── ingestion/
│   ├── cv_parser.py            # Parses PDF, DOCX, TXT CVs & extracts chronology
│   ├── chat_parser.py          # Mines ChatGPT, Claude & Gemini exports for real depth
│   ├── linkedin_parser.py      # Parses LinkedIn Profile PDF or archive CSVs
│   ├── intake_engine.py        # Multi-source intelligence fusion engine
│   └── persona_builder.py      # Synthesizes unified Master Professional Persona
├── matcher/
│   ├── geo_rules.py            # Validates Gulf & migration regions; enforces blocklists
│   └── jd_analyzer.py          # ATS keyword overlap, discipline match & gap scoring
├── generators/
│   ├── llm_client.py           # Multi-provider client (Gemini, OpenAI, Claude, or offline fallback)
│   ├── resume_tailorer.py      # STAR-aligned, ATS-optimized CV content generator with Fact-Locking
│   ├── cover_letter_gen.py     # High-impact personalized cover letter generator
│   └── pdf_builder.py          # ReportLab ATS-compliant PDF compiler
├── hunter/
│   ├── live_scraper.py         # Multi-board live aggregator and web URL scraper
│   ├── universal_cv_hunter.py  # Deep CV semantic matching engine for any profession worldwide
│   ├── remote_hunter.py        # Worldwide remote job discovery engine
│   ├── dubai_hunter.py         # Gulf and UAE career radar
│   └── hr_finder.py            # HR & talent acquisition email extractor
├── outreach/
│   ├── email_sender.py         # Outbound SMTP dispatcher with Safe Review Mode (.eml drafts)
│   └── tracker.py              # SQLite database tracking status, follow-ups & outcomes
└── frontend/                   # Modern Next.js 14 Web Command Center (Tailwind CSS, TypeScript)
```

---

## 🚀 Quick Start Guide

### 1. Unified Launcher (Windows)
Double-click `start.bat` or run:
```powershell
.\start.bat
```
This automatically launches:
- **FastAPI Backend** at `http://127.0.0.1:8005`
- **Next.js Frontend** at `http://localhost:3000`

### 2. Manual Startup

**Backend:**
```bash
python -m pip install -r requirements.txt
python -m uvicorn api:app --port 8005 --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### 3. Run Test Suite
```bash
pytest
```

---

## 🛡️ Email Outreach & Safety Review Mode

- **Safe Review Mode (Default: ON)**: When enabled, applications are saved as full RFC822 `.eml` email draft packages in `data/drafts/` with your tailored CV and Cover Letter PDFs attached. You can inspect the email before sending.
- **Live SMTP Mode**: When you are ready to send directly from your email account, toggle Safe Mode off, configure your SMTP credentials in Settings (e.g. Gmail address and Google App Password), and the agent delivers emails to HR mailboxes.
