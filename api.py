import os
import sys
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import jwt
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
import json
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from config import (
    PROFILE_PATH, GENERATED_DIR, UPLOADS_DIR,
    DEFAULT_LLM_PROVIDER, SAFE_MODE, SMTP_HOST, SMTP_USER, SENDER_NAME,
    HUNTER_API_KEY, APOLLO_API_KEY, update_env_file
)
from ingestion.persona_builder import PersonaBuilder
from ingestion.cv_parser import CVParser
from hunter.live_scraper import LiveJobHunter
from hunter.hr_finder import HRFinder
from matcher.jd_analyzer import JobDescriptionAnalyzer
from generators.resume_tailorer import ResumeTailorer
from generators.cover_letter_gen import CoverLetterGenerator
from generators.pdf_builder import PDFResumeBuilder
from generators.reviewer_agent import ReviewerAgent
from generators.interview_engine import InterviewEngine
from outreach.email_sender import EmailDispatcher
from outreach.tracker import ApplicationTracker

app = FastAPI(title="NexusHunt AI API", version="2.4")

# Enable CORS with specific origin controls (never allow * with credentials)
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
else:
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8005",
        "http://127.0.0.1:8005",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Models
class JobSearchRequest(BaseModel):
    keyword: str = "Python Developer"
    region: str = "GULF"
    max_results: int = 15

class RoleHRSearchRequest(BaseModel):
    role: str = "Python Developer"
    region: str = "GULF"
    limit: int = 10

class CompanyHRSearchRequest(BaseModel):
    company: str
    domain: Optional[str] = None
    region: str = "GULF"

class TailorRequest(BaseModel):
    job_title: str
    company: str
    location: str
    jd_text: str
    user_id: Optional[str] = "default"

class PDFGenRequest(BaseModel):
    tailored_resume: Dict[str, Any]

class InterviewGenerateRequest(BaseModel):
    job_title: str
    company: str
    location: Optional[str] = "Global / Remote"
    description: Optional[str] = ""
    candidate_id: Optional[str] = None

class InterviewEvaluateRequest(BaseModel):
    question: str
    question_type: str = "Behavioral (STAR)"
    candidate_answer: str
    job_title: str = "Software Engineer"
    company: str = "Company"

class SkillGapRequest(BaseModel):
    job_title: str
    company: str
    jd_text: Optional[str] = ""

class ATSPlainTextRequest(BaseModel):
    tailored_resume: Dict[str, Any]

class CVAnalyzeRequest(BaseModel):
    raw_text: Optional[str] = None
    user_id: Optional[str] = None

class CVJobHuntRequest(BaseModel):
    cv_analysis: Dict[str, Any]
    region: str = "ALL"
    min_match: int = 70
    limit: int = 60

class OutreachDraftRequest(BaseModel):
    job_title: str
    company: str
    hr_name: Optional[str] = "Hiring Team"
    hr_email: str
    tailored_content: Optional[str] = None
    user_id: Optional[str] = "default"

class SendEmailRequest(BaseModel):
    to_email: str
    subject: str
    body: str
    company: str
    job_title: str
    location: str = "Gulf / Remote"
    portal_link: Optional[str] = None
    cv_path: Optional[str] = None
    cover_letter_path: Optional[str] = None
    dry_run: bool = True
    user_id: Optional[str] = "default"

class StatusUpdateRequest(BaseModel):
    application_id: int
    new_status: str
    user_id: Optional[str] = "default"

class UserSettingsRequest(BaseModel):
    user_id: str = "default"
    smtp_host: Optional[str] = "smtp.gmail.com"
    smtp_port: Optional[int] = 587
    smtp_user: Optional[str] = ""
    smtp_password: Optional[str] = ""
    sender_name: Optional[str] = ""

class PortalAddRequest(BaseModel):
    name: str
    portal_url: str
    region: str = "GULF"
    country: str = "United Arab Emirates"
    industry: str = "Engineering & Technology"
    ats_type: str = "Direct Portal"
    hr_email: Optional[str] = ""
    notes: Optional[str] = ""

class SettingsUpdateRequest(BaseModel):
    settings: Dict[str, str]

class LinkedInParseRequest(BaseModel):
    linkedin_url: str = ""
    raw_text: Optional[str] = ""

class GitHubParseRequest(BaseModel):
    url_or_username: str

class WebsiteParseRequest(BaseModel):
    website_url: str

class SynthesizeProfileRequest(BaseModel):
    cv_sources: Optional[List[Dict[str, Any]]] = []
    chat_sources: Optional[List[Dict[str, Any]]] = []
    github_data: Optional[Dict[str, Any]] = None
    linkedin_data: Optional[Dict[str, Any]] = None
    website_data: Optional[Dict[str, Any]] = None


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = None
    access_token: Optional[str] = None
    client_id: Optional[str] = None

class SwitchUserRequest(BaseModel):
    user_id: str

def is_production_mode() -> bool:
    env = (os.getenv("APP_ENV") or os.getenv("ENVIRONMENT") or "").lower().strip()
    return env in ["production", "prod"]

DEFAULT_DEV_JWT_SECRET = "nexushunt-development-jwt-auth-secret-key-2026-secure-32chars"
_raw_jwt = os.getenv("JWT_SECRET", "").strip()
if is_production_mode() and (not _raw_jwt or _raw_jwt == DEFAULT_DEV_JWT_SECRET):
    raise RuntimeError("CRITICAL SECURITY ERROR: A custom JWT_SECRET environment variable must be set in production mode.")
JWT_SECRET = _raw_jwt or DEFAULT_DEV_JWT_SECRET
JWT_ALGORITHM = "HS256"

def validate_safe_user_file_path(path_str: str, user_id: str) -> Path:
    """Validates that a file attachment strictly belongs to the user and prevents path traversal."""
    if not path_str or not path_str.strip():
        raise HTTPException(status_code=400, detail="File path cannot be empty.")
    if "\0" in path_str or ".." in path_str:
        raise HTTPException(status_code=403, detail="Forbidden: Path traversal is prohibited.")

    target = Path(path_str).resolve()
    # Explicitly disallow system files
    if target.name.lower() in [".env", "applications.db", "master_persona.json", "config.py", "api.py"] or target.suffix.lower() in [".env", ".db", ".py", ".key", ".pem"]:
        raise HTTPException(status_code=403, detail="Forbidden: Access to system configuration files is strictly prohibited.")

    user_upload_dir = (UPLOADS_DIR / user_id).resolve()
    user_gen_dir = (GENERATED_DIR / user_id).resolve()
    global_upload_dir = UPLOADS_DIR.resolve()
    global_gen_dir = GENERATED_DIR.resolve()

    allowed = (
        str(target).startswith(str(user_upload_dir)) or
        str(target).startswith(str(user_gen_dir)) or
        (str(target).startswith(str(global_upload_dir)) and (user_id in ["default", "admin"] or user_id in target.name)) or
        (str(target).startswith(str(global_gen_dir)) and (user_id in ["default", "admin"] or user_id in target.name))
    )
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden: You do not have permission to attach or view this file.")
    if not target.exists():
        raise HTTPException(status_code=404, detail="The requested file was not found on the server.")
    return target

def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(days=14)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user_id(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    user_id: Optional[str] = None
) -> str:
    # 1. Primary: Cryptographically verified JWT token
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ")[1].strip()
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("sub"):
                return payload["sub"]
        except Exception:
            if is_production_mode():
                raise HTTPException(status_code=401, detail="Session expired or invalid. Please sign in again.")

    # 2. In production, unauthenticated clients cannot spoof or read another candidate's private data
    if is_production_mode():
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please sign in to access candidate profile and records."
        )

    # 3. Development Fallback (Local Dev Only)
    if x_user_id:
        return x_user_id.strip()
    if user_id:
        return user_id.strip()
    return "default"


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "NexusHunt AI", "version": "2.4"}


# --- AUTHENTICATION & MULTI-USER SESSIONS ---
@app.post("/api/auth/register")
def register(req: RegisterRequest):
    if not req.email or "@" not in req.email:
        raise HTTPException(status_code=400, detail="A valid email is required.")
    if not req.password or len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    if not req.full_name or len(req.full_name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Full name is required.")

    tracker = ApplicationTracker()
    try:
        user = tracker.create_user(
            email=req.email,
            password=req.password,
            full_name=req.full_name
        )
        token = create_access_token(user["id"], user["email"])
        return {
            "status": "success",
            "message": "Candidate account created successfully.",
            "user": user,
            "token": token
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login")
def login(req: LoginRequest):
    tracker = ApplicationTracker()
    user = tracker.authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    
    token = create_access_token(user["id"], user["email"])
    return {
        "status": "success",
        "message": "Logged in successfully.",
        "user": user,
        "token": token
    }

@app.get("/api/auth/me")
def get_current_user(current_user_id: str = Depends(get_current_user_id)):
    tracker = ApplicationTracker()
    user = tracker.get_user_by_id(current_user_id)
    if not user:
        user = tracker.get_user_by_id("default") or {
            "id": "default",
            "email": "sujahathmhmd@gmail.com",
            "full_name": "M.S. Mohamed Sujahath",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    return {"user": user}

@app.get("/api/auth/users")
def list_available_users():
    if is_production_mode():
        raise HTTPException(
            status_code=403,
            detail="Candidate directory listing is strictly disabled in production for candidate privacy."
        )
    tracker = ApplicationTracker()
    return {"users": tracker.list_users()}

@app.post("/api/auth/switch")
def switch_user(req: SwitchUserRequest):
    if is_production_mode():
        raise HTTPException(
            status_code=403,
            detail="Arbitrary candidate switching is strictly disabled in production. Please sign in with your credentials."
        )
    tracker = ApplicationTracker()
    user = tracker.get_user_by_id(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Candidate account not found.")
    token = create_access_token(user["id"], user["email"])
    return {
        "status": "success",
        "user": user,
        "token": token
    }

@app.get("/api/auth/google/config")
def get_google_auth_config():
    return {
        "google_client_id": os.getenv("GOOGLE_CLIENT_ID", "")
    }

@app.post("/api/auth/google")
def google_auth(req: GoogleAuthRequest):
    if not req.credential and not req.access_token:
        raise HTTPException(status_code=400, detail="Google credential or access token is required.")

    email = None
    full_name = None
    google_id = None

    # A. OAuth2 Access Token flow from popup
    if req.access_token:
        try:
            import urllib.request, json
            req_info = urllib.request.Request(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {req.access_token}"}
            )
            with urllib.request.urlopen(req_info, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                email = data.get("email")
                full_name = data.get("name") or (email.split("@")[0] if email else "Google Candidate")
                google_id = data.get("sub")
        except Exception as e:
            print(f"[Google Userinfo Fetch Error]: {e}")
            raise HTTPException(status_code=401, detail=f"Google token verification failed: {str(e)}")

    # B. ID Token credential flow
    elif req.credential:
        cred = req.credential.strip()
        google_client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip() or req.client_id
        allow_mock = os.getenv("ALLOW_MOCK_AUTH", "false").lower() == "true" and not is_production_mode()

        if cred.startswith("demo_google_"):
            if not allow_mock:
                raise HTTPException(
                    status_code=401,
                    detail="Mock Google sign-in is disabled. Please provide an authentic Google OAuth2 credential."
                )
            parts = cred.replace("demo_google_", "").split(":")
            email = parts[0] if parts and parts[0] else "candidate.google@gmail.com"
            full_name = parts[1] if len(parts) > 1 and parts[1] else "Google Candidate"
            google_id = "google_demo_" + email.replace("@", "_").replace(".", "_")
        else:
            if is_production_mode() and not google_client_id:
                raise HTTPException(
                    status_code=500,
                    detail="GOOGLE_CLIENT_ID must be configured on the server to verify Google sign-in."
                )
            verified = False
            try:
                from google.oauth2 import id_token
                from google.auth.transport import requests as google_requests
                
                idinfo = id_token.verify_oauth2_token(
                    cred,
                    google_requests.Request(),
                    audience=google_client_id if google_client_id else None
                )
                if google_client_id and idinfo.get("aud") != google_client_id:
                    raise HTTPException(status_code=401, detail="Google token audience mismatch.")
                email = idinfo.get("email")
                full_name = idinfo.get("name") or (email.split("@")[0] if email else "Google Candidate")
                google_id = idinfo.get("sub")
                verified = True
            except Exception as e:
                # Secondary fallback: Google tokeninfo endpoint with strict audience check
                try:
                    import urllib.request, json
                    url = f"https://oauth2.googleapis.com/tokeninfo?id_token={cred}"
                    with urllib.request.urlopen(url, timeout=8) as response:
                        data = json.loads(response.read().decode())
                        token_aud = data.get("aud")
                        if google_client_id and token_aud != google_client_id:
                            raise HTTPException(status_code=401, detail="Google token audience does not match configured client.")
                        email = data.get("email")
                        full_name = data.get("name") or (email.split("@")[0] if email else "Google Candidate")
                        google_id = data.get("sub")
                        verified = True
                except Exception as e2:
                    print(f"[Google Auth Verification Error]: {e} / {e2}")
                    raise HTTPException(status_code=401, detail="Google token verification failed. Please check credentials.")

    if not email:
        raise HTTPException(status_code=400, detail="Could not retrieve email from Google account.")

    tracker = ApplicationTracker()
    user = tracker.get_or_create_google_user(email=email, full_name=full_name or email.split("@")[0], google_id=google_id or "")
    token = create_access_token(user["id"], user["email"])

    return {
        "status": "success",
        "message": f"Signed in as {full_name} ({email}) via Google.",
        "user": user,
        "token": token
    }


# --- PROFILE & CV INTAKE ---
@app.get("/api/profile")
def get_profile(user_id: str = Depends(get_current_user_id)):
    pb = PersonaBuilder(user_id=user_id)
    return pb.profile

@app.post("/api/profile")
def update_profile(profile_data: Dict[str, Any], user_id: str = Depends(get_current_user_id)):
    pb = PersonaBuilder(user_id=user_id)
    pb.update_profile(profile_data)
    return {"status": "success", "profile": pb.profile}

@app.post("/api/profile/upload-cv")
async def upload_cv(file: UploadFile = File(...), user_id: str = Depends(get_current_user_id)):
    clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', Path(file.filename or "cv.pdf").name)
    save_path = UPLOADS_DIR / clean_name
    with open(save_path, "wb") as f:
        f.write(await file.read())
    
    parser = CVParser()
    extracted = parser.parse_cv(save_path)
    if not extracted:
        raise HTTPException(status_code=400, detail="Could not extract text from CV.")
    
    pb = PersonaBuilder(user_id=user_id)
    updated = pb.build_from_sources(cv_data_list=[extracted], chat_insights=[])
    pb.update_profile(updated)
    return {"status": "success", "extracted": extracted, "profile": pb.profile}

@app.post("/api/profile/upload-multiple-cvs")
async def upload_multiple_cvs(files: List[UploadFile] = File(...), user_id: str = Depends(get_current_user_id)):
    from ingestion.intake_engine import IntakeEngine
    engine = IntakeEngine(user_id=user_id)
    saved_paths = []
    for idx, f in enumerate(files):
        clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', Path(f.filename or f"cv_{idx}.pdf").name)
        save_path = UPLOADS_DIR / clean_name
        with open(save_path, "wb") as out:
            out.write(await f.read())
        saved_paths.append(save_path)
    
    parsed = engine.parse_multiple_cvs(saved_paths)
    return {"status": "success", "count": len(parsed), "cvs": parsed}

@app.post("/api/profile/upload-chat-history")
async def upload_chat_history(files: List[UploadFile] = File(...), user_id: str = Depends(get_current_user_id)):
    from ingestion.intake_engine import IntakeEngine
    engine = IntakeEngine(user_id=user_id)
    all_insights = []
    for idx, f in enumerate(files):
        clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', Path(f.filename or f"chat_{idx}.json").name)
        save_path = UPLOADS_DIR / clean_name
        with open(save_path, "wb") as out:
            out.write(await f.read())
        insights = engine.parse_chat_history_file(save_path)
        all_insights.extend(insights)
    return {"status": "success", "count": len(all_insights), "insights": all_insights}

@app.post("/api/profile/parse-github")
def parse_github(req: GitHubParseRequest, user_id: str = Depends(get_current_user_id)):
    from ingestion.intake_engine import IntakeEngine
    engine = IntakeEngine(user_id=user_id)
    data = engine.parse_github_profile(req.url_or_username)
    return {"status": "success", "github": data}

@app.post("/api/profile/parse-linkedin")
def parse_linkedin(req: LinkedInParseRequest, user_id: str = Depends(get_current_user_id)):
    from ingestion.intake_engine import IntakeEngine
    engine = IntakeEngine(user_id=user_id)
    data = engine.parse_linkedin_text_or_url(req.linkedin_url, req.raw_text or "")
    return {"status": "success", "linkedin": data, "profile": engine.persona_builder.profile}

@app.post("/api/profile/upload-linkedin-pdf")
async def upload_linkedin_pdf(file: UploadFile = File(...), user_id: str = Depends(get_current_user_id)):
    from ingestion.intake_engine import IntakeEngine
    engine = IntakeEngine(user_id=user_id)
    clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', Path(file.filename or "export.pdf").name)
    save_path = UPLOADS_DIR / f"linkedin_{clean_name}"
    with open(save_path, "wb") as out:
        out.write(await file.read())
    data = engine.parse_linkedin_pdf(save_path)
    return {"status": "success", "linkedin": data, "profile": engine.persona_builder.profile}

@app.post("/api/profile/parse-website")
def parse_website(req: WebsiteParseRequest, user_id: str = Depends(get_current_user_id)):
    from ingestion.intake_engine import IntakeEngine
    engine = IntakeEngine(user_id=user_id)
    data = engine.scrape_personal_website(req.website_url)
    return {"status": "success", "website": data}

@app.post("/api/profile/synthesize")
def synthesize_profile(req: SynthesizeProfileRequest, user_id: str = Depends(get_current_user_id)):
    from ingestion.intake_engine import IntakeEngine
    engine = IntakeEngine(user_id=user_id)
    updated = engine.synthesize_master_profile(
        cv_data_list=req.cv_sources or [],
        chat_insights=req.chat_sources or [],
        github_data=req.github_data,
        linkedin_data=req.linkedin_data,
        website_data=req.website_data
    )
    return {"status": "success", "profile": updated}

@app.get("/api/profile/download-europass-cv")
@app.get("/api/cv/download-europass")
def download_default_europass_cv(user_id: str = Depends(get_current_user_id)):
    pb = PersonaBuilder(user_id=user_id)
    builder = PDFResumeBuilder()
    clean_user = re.sub(r'[^a-zA-Z0-9_-]', '_', user_id)
    out_file = GENERATED_DIR / f"Europass_CV_{clean_user}.pdf"
    builder.build_resume_pdf(pb.profile, out_file)
    if not os.path.exists(out_file):
        raise HTTPException(status_code=500, detail="Failed to compile Europass CV PDF.")
    return FileResponse(
        out_file,
        media_type="application/pdf",
        filename=f"Europass_CV_{re.sub(r'[^a-zA-Z0-9_.-]', '_', pb.profile.get('identity', {}).get('full_name', 'Candidate'))}.pdf"
    )


# --- LIVE JOB HUNTER ---
@app.post("/api/jobs/search")
def search_jobs(req: JobSearchRequest):
    hunter = LiveJobHunter()
    jobs = hunter.search_live(
        keyword=req.keyword,
        region_filter=req.region,
        max_results=req.max_results
    )
    
    pb = PersonaBuilder()
    analyzer = JobDescriptionAnalyzer(pb.profile)
    scored_jobs = []
    for j in jobs:
        analysis = analyzer.analyze(
            job_title=j.get("job_title", ""),
            company=j.get("company", ""),
            location=j.get("location", ""),
            jd_text=j.get("description", "")
        )
        j["fit_analysis"] = analysis
        scored_jobs.append(j)
    
    scored_jobs.sort(key=lambda x: x.get("fit_analysis", {}).get("match_score", 0), reverse=True)
    return {"count": len(scored_jobs), "jobs": scored_jobs}

@app.get("/api/jobs/stream")
def stream_jobs(keyword: str = "Python Developer", region: str = "GULF", max_results: int = 30):
    def event_stream():
        yield ": ping\n\n"
        hunter = LiveJobHunter()
        pb = PersonaBuilder()
        analyzer = JobDescriptionAnalyzer(pb.profile)
        for j in hunter.stream_live(
            keyword=keyword,
            region_filter=region,
            max_results=max_results
        ):
            analysis = analyzer.analyze(
                job_title=j.get("job_title", ""),
                company=j.get("company", ""),
                location=j.get("location", ""),
                jd_text=j.get("full_description") or j.get("description", "")
            )
            j["fit_analysis"] = analysis
            yield f"data: {json.dumps(j)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no",
        }
    )

# --- GLOBAL REMOTE JOBS (WORLDWIDE ONLY) ---
@app.get("/api/jobs/remote")
def get_global_remote_jobs(
    keyword: str = "Python",
    worldwide_only: bool = True,
    limit: int = 60,
    source: str = "ALL"
):
    """Fetches verified 100% remote jobs from keyless public JSON feeds (RemoteOK, Remotive, 
    Jobicy, Himalayas, Arbeitnow, WWR RSS) and Direct Company ATS (Greenhouse/Ashby/Lever).
    Enforces worldwide openness and strict Israel exclusion."""
    try:
        from hunter.remote_hunter import GlobalRemoteHunter
        hunter = GlobalRemoteHunter()
        jobs = hunter.search_all_remote(
            keyword=keyword,
            worldwide_only=worldwide_only,
            limit=limit,
            source_filter=source
        )
        return {"status": "success", "count": len(jobs), "jobs": jobs}
    except Exception as e:
        print(f"[Remote Jobs Hunter Error]: {e}")
        return {"status": "error", "message": str(e), "count": 0, "jobs": []}


# --- DUBAI & UAE CAREER HUNTER (HIGH-MATCH & OVERQUALIFIED ROLES) ---
@app.get("/api/jobs/dubai")
def get_dubai_jobs(keyword: str = "", category: str = "ALL", limit: int = 40):
    """Fetches high-fit Dubai & UAE corporate job postings across Business Analyst, 
    IT Support, Document Controller, Software Engineering, and Operations roles."""
    try:
        from hunter.dubai_hunter import DubaiJobHunter
        hunter = DubaiJobHunter()
        jobs = hunter.search_dubai_jobs(keyword=keyword, category=category, max_results=limit)
        return {"status": "success", "count": len(jobs), "jobs": jobs}
    except Exception as e:
        print(f"[Dubai Jobs Hunter Error]: {e}")
        return {"status": "error", "message": str(e), "count": 0, "jobs": []}

@app.get("/api/jobs/dubai/stream")
def stream_dubai_jobs(keyword: str = "", category: str = "ALL", limit: int = 40):
    def event_stream():
        yield ": ping\n\n"
        from hunter.dubai_hunter import DubaiJobHunter
        hunter = DubaiJobHunter()
        jobs = hunter.search_dubai_jobs(keyword=keyword, category=category, max_results=limit)
        for j in jobs:
            yield f"data: {json.dumps(j)}\n\n"
            time.sleep(0.03)
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no",
        }
    )


# --- UNIVERSAL CV MATCHER & GLOBAL HUNTER ---
@app.post("/api/cv-hunter/analyze")
def analyze_cv(
    req: Optional[CVAnalyzeRequest] = None,
    current_user_id: str = Depends(get_current_user_id)
):
    """Deeply parses and analyzes ANY CV text or candidate profile to extract target roles,
    competencies, and global search vectors."""
    try:
        from hunter.universal_cv_hunter import UniversalCVHunter
        hunter = UniversalCVHunter()
        text_to_analyze = req.raw_text if req and req.raw_text else ""
        if not text_to_analyze:
            uid = current_user_id if is_production_mode() else (req.user_id if req and req.user_id else current_user_id)
            pb = PersonaBuilder(user_id=uid)
            text_to_analyze = json.dumps(pb.profile, indent=2)
        analysis = hunter.parse_and_analyze_cv(text_to_analyze)
        return analysis
    except Exception as e:
        print(f"[Universal CV Analyze Error]: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cv-hunter/upload")
async def upload_and_analyze_cv(
    file: UploadFile = File(...),
    current_user_id: str = Depends(get_current_user_id)
):
    """Uploads ANY CV file (PDF, DOCX, TXT), parses it carefully, and immediately hunts matching jobs worldwide."""
    try:
        from hunter.universal_cv_hunter import UniversalCVHunter
        hunter = UniversalCVHunter()
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', file.filename or "cv.pdf")
        temp_path = UPLOADS_DIR / f"cv_match_{int(time.time())}_{safe_name}"
        contents = await file.read()
        with open(temp_path, "wb") as f:
            f.write(contents)

        analysis = hunter.parse_and_analyze_cv(str(temp_path))
        jobs = hunter.hunt_matching_jobs(analysis, region="ALL", min_match=65, limit=50)
        return {
            "status": "success",
            "filename": file.filename,
            "analysis": analysis,
            "jobs": jobs,
            "count": len(jobs)
        }
    except Exception as e:
        print(f"[Universal CV Upload & Match Error]: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cv-hunter/search")
def search_jobs_for_cv(req: CVJobHuntRequest):
    """Hunts live matching jobs worldwide using the extracted CV analysis parameters."""
    try:
        from hunter.universal_cv_hunter import UniversalCVHunter
        hunter = UniversalCVHunter()
        jobs = hunter.hunt_matching_jobs(
            cv_analysis=req.cv_analysis,
            region=req.region,
            min_match=req.min_match,
            limit=req.limit
        )
        return {
            "status": "success",
            "count": len(jobs),
            "region": req.region,
            "jobs": jobs
        }
    except Exception as e:
        print(f"[Universal CV Job Search Error]: {e}")
        return {"status": "error", "message": str(e), "count": 0, "jobs": []}


# --- GLOBAL RECRUITER & HR FINDER ---
@app.get("/api/hr/by-role/stream")
def stream_hr_by_role(role: str = "Python Developer", region: str = "GULF", limit: int = 25):
    def event_stream():
        yield ": ping\n\n"
        for comp in HRFinder.stream_companies_and_hr_by_role(role=role, region=region, max_companies=limit):
            yield f"data: {json.dumps(comp)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no",
        }
    )

@app.post("/api/hr/by-role")
def find_hr_by_role(req: RoleHRSearchRequest):
    results = HRFinder.find_companies_and_hr_by_role(
        role=req.role,
        region=req.region,
        max_companies=req.limit
    )
    return {"role": req.role, "region": req.region, "count": len(results), "companies": results}

@app.post("/api/hr/by-company")
def find_hr_by_company(req: CompanyHRSearchRequest):
    results = HRFinder.search_global_hr(
        company_name=req.company,
        domain=req.domain,
        region=req.region
    )
    return results


# --- AI CV & COVER LETTER TAILOR ---
@app.post("/api/cv/tailor")
def tailor_cv(req: TailorRequest, current_user_id: str = Depends(get_current_user_id)):
    user_id = current_user_id if is_production_mode() else (req.user_id or current_user_id)
    pb = PersonaBuilder(user_id=user_id)
    tailorer = ResumeTailorer(pb.profile)
    cl_gen = CoverLetterGenerator(pb.profile)
    
    tailored_resume = tailorer.generate_tailored_resume(
        job_title=req.job_title,
        company=req.company,
        location=req.location,
        jd_text=req.jd_text
    )
    
    cover_letter = cl_gen.generate(
        job_title=req.job_title,
        company=req.company,
        location=req.location,
        jd_text=req.jd_text
    )

    # Stage 2: Reviewer Agent Anti-Hallucination Audit Gate
    reviewer = ReviewerAgent(pb.profile)
    audit_report = reviewer.audit_and_verify(
        tailored_resume=tailored_resume,
        cover_letter=cover_letter,
        job_title=req.job_title,
        company=req.company,
        jd_text=req.jd_text
    )

    # Calculate Skill Gap & 24-Hour Quick-Study Roadmap
    skill_gap = reviewer.analyze_skill_gap(
        job_title=req.job_title,
        company=req.company,
        jd_text=req.jd_text
    )

    safe_comp = re.sub(r'[^a-zA-Z0-9_-]', '_', req.company).strip('_') or "Company"
    clean_uid = re.sub(r'[^a-zA-Z0-9_-]', '_', user_id)
    try:
        pdf_gen = PDFResumeBuilder()
        cv_out = GENERATED_DIR / f"Europass_CV_{clean_uid}_{safe_comp}.pdf"
        ats_out = GENERATED_DIR / f"Clean_ATS_CV_{clean_uid}_{safe_comp}.pdf"
        cl_out = GENERATED_DIR / f"Cover_Letter_{clean_uid}_{safe_comp}.pdf"
        pdf_gen.build_resume_pdf(tailored_resume, cv_out)
        pdf_gen.build_ats_clean_pdf(tailored_resume, ats_out)
        pdf_gen.build_cover_letter_pdf(cover_letter, pb.profile, cl_out)
    except Exception as e:
        print(f"[Tailor Pre-build Error]: {e}")
    
    return {
        "tailored_resume": tailored_resume,
        "cover_letter": cover_letter,
        "reviewer_audit": audit_report,
        "skill_gap": skill_gap
    }

@app.post("/api/cv/generate-pdf")
def generate_pdf(req: PDFGenRequest):
    import time
    pdf_gen = PDFResumeBuilder()
    out_file = GENERATED_DIR / f"Europass_CV_{int(time.time())}.pdf"
    pdf_gen.build_resume_pdf(
        resume_data=req.tailored_resume,
        output_path=out_file
    )
    if not os.path.exists(out_file):
        raise HTTPException(status_code=500, detail="PDF generation failed.")
    return FileResponse(
        out_file,
        media_type="application/pdf",
        filename=os.path.basename(out_file)
    )

@app.post("/api/cv/generate-ats-pdf")
def generate_ats_pdf(req: PDFGenRequest):
    import time
    pdf_gen = PDFResumeBuilder()
    out_file = GENERATED_DIR / f"Clean_ATS_CV_{int(time.time())}.pdf"
    pdf_gen.build_ats_clean_pdf(
        resume_data=req.tailored_resume,
        output_path=out_file
    )
    if not os.path.exists(out_file):
        raise HTTPException(status_code=500, detail="ATS PDF generation failed.")
    return FileResponse(
        out_file,
        media_type="application/pdf",
        filename=os.path.basename(out_file)
    )

@app.post("/api/cv/ats-plaintext")
def get_ats_plaintext(req: ATSPlainTextRequest):
    pdf_gen = PDFResumeBuilder()
    plaintext = pdf_gen.generate_ats_plaintext(req.tailored_resume)
    return {"plaintext": plaintext}

@app.post("/api/tailor/skill-gap")
def get_skill_gap(req: SkillGapRequest, current_user_id: str = Depends(get_current_user_id)):
    pb = PersonaBuilder(user_id=current_user_id)
    reviewer = ReviewerAgent(pb.profile)
    gap = reviewer.analyze_skill_gap(
        job_title=req.job_title,
        company=req.company,
        jd_text=req.jd_text or ""
    )
    return gap

@app.post("/api/interview/generate")
def generate_interview_prep(req: InterviewGenerateRequest, current_user_id: str = Depends(get_current_user_id)):
    user_id = current_user_id if is_production_mode() else (req.candidate_id or current_user_id)
    pb = PersonaBuilder(user_id=user_id)
    engine = InterviewEngine(pb.profile)
    pack = engine.generate_interview_pack(
        job_title=req.job_title,
        company=req.company,
        location=req.location or "Global / Remote",
        jd_text=req.description or ""
    )
    return pack

@app.post("/api/interview/evaluate")
def evaluate_interview_answer(req: InterviewEvaluateRequest, current_user_id: str = Depends(get_current_user_id)):
    user_id = current_user_id
    pb = PersonaBuilder(user_id=user_id)
    engine = InterviewEngine(pb.profile)
    evaluation = engine.evaluate_candidate_answer(
        question=req.question,
        question_type=req.question_type,
        candidate_answer=req.candidate_answer,
        job_title=req.job_title,
        company=req.company
    )
    return evaluation

@app.get("/api/documents/preview")
def preview_document(
    type: str = "cv",
    company: str = "Company",
    job_title: str = "Software Engineer",
    custom_file: Optional[str] = None,
    user_id: str = Depends(get_current_user_id)
):
    """Returns or generates on the fly the Europass CV or Cover Letter PDF for preview.
    Supports previewing user-uploaded custom manual documents."""
    try:
        GENERATED_DIR.mkdir(parents=True, exist_ok=True)
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

        # 1. Custom uploaded document preview
        if custom_file:
            if "\0" in custom_file or ".." in custom_file or "/" in custom_file or "\\" in custom_file:
                raise HTTPException(status_code=403, detail="Forbidden: Invalid filename.")

            safe_name = os.path.basename(custom_file)
            user_upload_dir = UPLOADS_DIR / user_id
            target = user_upload_dir / safe_name
            if not target.exists():
                legacy_target = UPLOADS_DIR / safe_name
                if legacy_target.exists() and (user_id in ["default", "admin"] or safe_name.startswith(f"manual_{user_id}_")):
                    target = legacy_target
                else:
                    target = GENERATED_DIR / safe_name

            if target.exists():
                is_owned = (
                    str(target.resolve()).startswith(str(user_upload_dir.resolve())) or
                    user_id in target.name or
                    user_id in ["default", "admin"]
                )
                if not is_owned:
                    raise HTTPException(status_code=403, detail="Forbidden: You do not have permission to view this document.")

                media_type = "application/pdf" if target.suffix.lower() == ".pdf" else "application/octet-stream"
                return FileResponse(
                    target,
                    media_type=media_type,
                    headers={"Content-Disposition": f"inline; filename={target.name}"}
                )
            else:
                raise HTTPException(status_code=404, detail="Requested preview file not found.")

        # 2. Standard generated document preview
        safe_comp = re.sub(r'[^a-zA-Z0-9_-]', '_', company).strip('_') or "Company"
        clean_uid = re.sub(r'[^a-zA-Z0-9_-]', '_', user_id)
        pb = PersonaBuilder(user_id=user_id)
        pdf_gen = PDFResumeBuilder()

        if type == "cv":
            out_file = GENERATED_DIR / f"Europass_CV_{clean_uid}_{safe_comp}.pdf"
            # Always build fresh from current persona profile so profile edits appear immediately
            pdf_gen.build_resume_pdf(pb.profile, out_file)
            return FileResponse(
                out_file,
                media_type="application/pdf",
                headers={"Content-Disposition": f"inline; filename={out_file.name}"}
            )
        else:
            out_file = GENERATED_DIR / f"Cover_Letter_{clean_uid}_{safe_comp}.pdf"
            cl_gen = CoverLetterGenerator(pb.profile)
            cl_text = cl_gen.generate(
                job_title=job_title,
                company=company,
                location="International / Remote",
                jd_text=""
            )
            pdf_gen.build_cover_letter_pdf(cl_text, pb.profile, out_file)
            return FileResponse(
                out_file,
                media_type="application/pdf",
                headers={"Content-Disposition": f"inline; filename={out_file.name}"}
            )
    except Exception as e:
        print(f"[Document Preview Generation Error]: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compile PDF document: {str(e)}")

@app.post("/api/outreach/upload-attachment")
async def upload_outreach_attachment(
    file: UploadFile = File(...),
    doc_type: str = Form("cv"),  # "cv" or "cover_letter"
    user_id: str = Depends(get_current_user_id)
):
    """Saves candidate's manual CV or Cover Letter to replace generated documents."""
    try:
        clean_uid = re.sub(r'[^a-zA-Z0-9_-]', '_', user_id)[:20]
        user_upload_dir = UPLOADS_DIR / clean_uid
        user_upload_dir.mkdir(parents=True, exist_ok=True)

        raw_name = file.filename or f"custom_{doc_type}.pdf"
        clean_ext = Path(raw_name).suffix or ".pdf"
        clean_base = re.sub(r'[^a-zA-Z0-9_-]', '_', Path(raw_name).stem)[:40]

        saved_filename = f"manual_{clean_uid}_{doc_type}_{int(time.time())}_{clean_base}{clean_ext}"
        saved_path = user_upload_dir / saved_filename

        content = await file.read()
        with open(saved_path, "wb") as f:
            f.write(content)

        file_size_kb = round(len(content) / 1024, 1)

        return {
            "status": "success",
            "doc_type": doc_type,
            "filename": raw_name,
            "saved_filename": saved_filename,
            "saved_path": str(saved_path.resolve()),
            "file_size_kb": file_size_kb,
            "preview_url": f"/api/documents/preview?custom_file={saved_filename}"
        }
    except Exception as e:
        print(f"[Outreach Attachment Upload Error]: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload {doc_type}: {str(e)}")


# --- OUTREACH & EMAIL DISPATCHER ---
@app.post("/api/outreach/draft")
def draft_outreach(req: OutreachDraftRequest, current_user_id: str = Depends(get_current_user_id)):
    user_id = current_user_id if is_production_mode() else (req.user_id or current_user_id)
    pb = PersonaBuilder(user_id=user_id)
    cl_gen = CoverLetterGenerator(pb.profile)
    subject, body = cl_gen.generate_recruiter_email(
        job_title=req.job_title,
        company=req.company,
        hr_name=req.hr_name or "Hiring Team",
        specific_hook=req.tailored_content or ""
    )
    return {"subject": subject, "body": body, "to_email": req.hr_email}

@app.post("/api/outreach/send")
def send_outreach(req: SendEmailRequest, current_user_id: str = Depends(get_current_user_id)):
    user_id = current_user_id if is_production_mode() else (req.user_id or current_user_id)

    # Security: Validate file attachments against user boundary & prevent path traversal
    cv_attachment = validate_safe_user_file_path(req.cv_path, user_id) if req.cv_path else None
    cl_attachment = validate_safe_user_file_path(req.cover_letter_path, user_id) if req.cover_letter_path else None

    # Security: Server-side SAFE_MODE enforcement
    effective_dry_run = True if SAFE_MODE else bool(req.dry_run)

    dispatcher = EmailDispatcher()
    result = dispatcher.dispatch(
        to_email=req.to_email,
        subject=req.subject,
        body_text=req.body,
        attachment_path=cv_attachment,
        cover_letter_path=cl_attachment,
        company=req.company,
        job_title=req.job_title,
        location=req.location,
        portal_link=req.portal_link,
        dry_run=effective_dry_run,
        user_id=user_id
    )
    return result


# --- APPLICATION TRACKER ---
@app.get("/api/tracker/applications")
def list_applications(user_id: str = Depends(get_current_user_id)):
    tracker = ApplicationTracker()
    apps = tracker.list_applications(limit=100, user_id=user_id)
    metrics = tracker.get_metrics(user_id=user_id)
    return {"metrics": metrics, "applications": apps}

@app.post("/api/tracker/update-status")
def update_application_status(req: StatusUpdateRequest, current_user_id: str = Depends(get_current_user_id)):
    user_id = current_user_id if is_production_mode() else (req.user_id or current_user_id)
    tracker = ApplicationTracker()
    ok = tracker.update_status(req.application_id, req.new_status, user_id=user_id)
    return {"status": "success" if ok else "error"}


# --- CAREER PORTALS ---
@app.get("/api/portals")
def get_career_portals(region: Optional[str] = None, query: Optional[str] = None):
    from hunter.portals import CareerPortalManager
    mgr = CareerPortalManager()
    portals = mgr.list_portals(region=region, query=query)
    return {"portals": portals}

@app.post("/api/portals")
def add_career_portal(req: PortalAddRequest, current_user_id: str = Depends(get_current_user_id)):
    from hunter.portals import CareerPortalManager
    mgr = CareerPortalManager()
    created = mgr.add_custom_portal(
        name=req.name,
        portal_url=req.portal_url,
        region=req.region,
        country=req.country,
        industry=req.industry,
        ats_type=req.ats_type,
        hr_email=req.hr_email or "",
        notes=req.notes or ""
    )
    return {"status": "success", "portal": created}

@app.delete("/api/portals/{portal_id}")
def delete_career_portal(portal_id: int, current_user_id: str = Depends(get_current_user_id)):
    from hunter.portals import CareerPortalManager
    mgr = CareerPortalManager()
    ok = mgr.delete_portal(portal_id)
    return {"status": "success" if ok else "error"}


# --- SETTINGS ---
@app.get("/api/settings")
def get_settings():
    return {
        "llm_provider": os.getenv("LLM_PROVIDER", DEFAULT_LLM_PROVIDER),
        "safe_mode": os.getenv("SAFE_MODE", str(SAFE_MODE)),
        "smtp_host": SMTP_HOST,
        "smtp_user": SMTP_USER,
        "sender_name": SENDER_NAME,
        "hunter_key_set": bool(HUNTER_API_KEY),
        "apollo_key_set": bool(APOLLO_API_KEY)
    }

@app.post("/api/settings")
def update_settings(req: SettingsUpdateRequest, current_user_id: str = Depends(get_current_user_id)):
    if is_production_mode():
        raise HTTPException(
            status_code=403,
            detail="Direct environment modifications are prohibited in production mode. Configure settings via server environment variables."
        )
    # Whitelist only safe non-sensitive configuration keys
    allowed_keys = {"LLM_PROVIDER", "SAFE_MODE"}
    safe_settings = {k: v for k, v in req.settings.items() if k in allowed_keys}
    if not safe_settings:
        raise HTTPException(status_code=400, detail="No permissible settings provided.")
    update_env_file(safe_settings)
    return {"status": "success", "updated": list(safe_settings.keys())}

@app.get("/api/settings/user")
def get_user_settings(user_id: str = Depends(get_current_user_id)):
    tracker = ApplicationTracker()
    settings = tracker.get_user_settings(user_id)
    has_pw = bool(settings.get("smtp_password"))
    masked_pw = ("*" * 8) if has_pw else ""
    return {
        "user_id": user_id,
        "smtp_host": settings.get("smtp_host", "smtp.gmail.com"),
        "smtp_port": settings.get("smtp_port", 587),
        "smtp_user": settings.get("smtp_user", ""),
        "smtp_password": masked_pw,
        "has_password": has_pw,
        "sender_name": settings.get("sender_name", "")
    }

@app.post("/api/settings/user")
def save_user_settings(req: UserSettingsRequest, current_user_id: str = Depends(get_current_user_id)):
    target_id = current_user_id if is_production_mode() else (req.user_id or current_user_id)
    tracker = ApplicationTracker()
    existing = tracker.get_user_settings(target_id)
    pw_to_save = (req.smtp_password or "").strip()
    if not pw_to_save or pw_to_save.startswith("****"):
        pw_to_save = existing.get("smtp_password", "")
    
    data = {
        "smtp_host": req.smtp_host or "smtp.gmail.com",
        "smtp_port": req.smtp_port or 587,
        "smtp_user": (req.smtp_user or "").strip(),
        "smtp_password": pw_to_save,
        "sender_name": (req.sender_name or "").strip()
    }
    tracker.save_user_settings(target_id, data)
    return {
        "status": "success",
        "user_id": target_id,
        "settings": {
            **data,
            "smtp_password": ("*" * 8) if pw_to_save else "",
            "has_password": bool(pw_to_save)
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT") or os.getenv("PORT") or 8005)
    uvicorn.run("api:app", host="127.0.0.1", port=port, reload=True)
