# 🎯 AI Autonomous Job Hunter & Application Agent

An end-to-end autonomous AI bot engineered for **Engineers** seeking international relocation. The agent ingests your existing CVs, chat histories (ChatGPT, Claude, Gemini), and LinkedIn profile to deeply understand your technical background, problem-solving mindset, and personal voice. It then identifies engineering jobs, tailors ATS-optimized CVs & Cover Letters, compiles publication-quality PDFs, and dispatches applications directly to HR mailboxes.

---

## 🌍 Geographic Strategy & Strict Policies

### 1. Gulf Countries (GCC Focus)
- **United Arab Emirates (UAE)**: Dubai, Abu Dhabi, Sharjah
- **Saudi Arabia (KSA)**: Riyadh, Jeddah, Dammam, NEOM Mega-Projects
- **Qatar**: Doha, Lusail
- **Oman**: Muscat, Sohar
- **Kuwait & Bahrain**

### 2. High-Opportunity & Migratable Pathways from Sri Lanka
- **Southeast Asia**: Singapore (Employment Pass), Malaysia (Tech Pass), Maldives
- **Europe & UK**: United Kingdom (Skilled Worker Visa), Germany (Opportunity Card / Chancenkarte & EU Blue Card for Engineers)
- **Australasia**: Australia (Subclass 189/190/491 & CDR Engineers Australia), New Zealand (Green List)
- **North America**: Canada (Express Entry STEM)

### 3. Strict Exclusion Rule (Hard Coded Zero-Tolerance)
- **Israel**: **Strictly Excluded.** Any job posting located in or affiliated with Israel is automatically identified and rejected by the filtering engine with zero exceptions.

---

## 🏗️ Architecture & Modules

```
ai-job-hunter-agent/
├── app.py                      # Interactive Streamlit Web Command Center
├── cli.py                      # Headless CLI for terminal / automation runs
├── config.py                   # Configuration, target regions & strict exclusion rules
├── test_agent.py               # Comprehensive unit test suite
├── ingestion/
│   ├── cv_parser.py            # Parses PDF, DOCX, TXT CVs & extracts chronology
│   ├── chat_parser.py          # Mines ChatGPT, Claude & Gemini exports for real engineering depth
│   ├── linkedin_parser.py      # Parses LinkedIn Profile PDF or archive CSVs
│   └── persona_builder.py      # Synthesizes unified Master Professional Persona
├── matcher/
│   ├── geo_rules.py            # Validates Gulf & migration regions; enforces Israel blocklist
│   └── jd_analyzer.py          # ATS keyword overlap, discipline match & gap scoring
├── generators/
│   ├── llm_client.py           # Multi-provider client (Gemini, OpenAI, Claude, or offline fallback)
│   ├── resume_tailorer.py      # STAR-aligned, ATS-optimized CV content generator
│   ├── cover_letter_gen.py     # High-impact personalized cover letter generator
│   └── pdf_builder.py          # ReportLab ATS-compliant PDF compiler
├── hunter/
│   ├── job_search.py           # Gulf & Global job aggregator and web URL scraper
│   └── hr_finder.py            # HR & talent acquisition email extractor
├── outreach/
│   ├── email_sender.py         # Outbound SMTP dispatcher with Safe Review Mode (.eml drafts)
│   └── tracker.py              # SQLite database tracking status, follow-ups & outcomes
└── data/                       # Storage for uploads, generated PDFs, drafts, and database
```

---

## 🚀 Quick Start Guide

### 1. Run the Visual Web Dashboard
From PowerShell or terminal:
```powershell
cd "C:\Users\Blue Brand Battery\.gemini\antigravity\scratch\ai-job-hunter-agent"
streamlit run app.py
```
This opens the Command Center in your browser at `http://localhost:8501`.

### 2. Run Headless via CLI
```powershell
# Search Gulf engineering jobs:
python cli.py search --region GULF

# Search all migratable pathways:
python cli.py search --region MIGRATABLE

# Tailor and generate application draft:
python cli.py apply --title "Systems Engineer" --company "Careem" --location "Dubai, UAE" --email "careers@careem.com"

# View tracked applications in SQLite:
python cli.py list
```

### 3. Run Test Suite
```powershell
python test_agent.py
```

---

## 📥 How to Export Your Data for the Agent

1. **ChatGPT**:
   - Go to `chatgpt.com` > Click your Profile > **Settings** > **Data controls** > **Export data**.
   - Download the zip and upload `conversations.json` into Tab 1 of the app.
2. **Claude**:
   - Go to `claude.ai` > Account Settings > Export Data, or save your technical conversation transcripts as text/JSON.
3. **Gemini**:
   - Export your Google Gemini logs via Google Takeout or save chat transcripts.
4. **LinkedIn**:
   - Go to your LinkedIn Profile > Click **More** > **Save to PDF**.
   - Or go to Settings & Privacy > Data Privacy > Get a copy of your data (CSVs).
5. **CVs**:
   - Upload any previous versions of your CV in PDF, Word (`.docx`), or plain text.

---

## 🛡️ Email Outreach & Safety Review Mode

- **Safe Review Mode (Default: ON)**: When enabled, applications are saved as full RFC822 `.eml` email draft packages in `data/drafts/` with your tailored CV and Cover Letter PDFs attached. You can inspect the email before sending.
- **Live SMTP Mode**: When you are ready to send directly from your email account, toggle Safe Mode off in the sidebar, enter your SMTP details in Settings (e.g. Gmail address and Google App Password), and the agent will deliver emails directly to HR mailboxes.
