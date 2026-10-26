import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import jwt
from fastapi import FastAPI, HTTPException, UploadFile, File, Header, Depends
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
from outreach.email_sender import EmailDispatcher
from outreach.tracker import ApplicationTracker

app = FastAPI(title="NexusHunt AI API", version="2.4")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    credential: str
    client_id: Optional[str] = None

class SwitchUserRequest(BaseModel):
    user_id: str

JWT_SECRET = os.getenv("JWT_SECRET", "nexushunt-production-jwt-auth-secret-key-2026-secure-32chars")
JWT_ALGORITHM = "HS256"

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
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ")[1].strip()
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("sub"):
                return payload["sub"]
        except Exception:
            pass
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
    tracker = ApplicationTracker()
    return {"users": tracker.list_users()}

@app.post("/api/auth/switch")
def switch_user(req: SwitchUserRequest):
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
    if not req.credential:
        raise HTTPException(status_code=400, detail="Google credential token is required.")

    cred = req.credential.strip()
    email = None
    full_name = None
    google_id = None

    # 1. Check for Demo / Sandbox Google Sign-In
    if cred.startswith("demo_google_"):
        parts = cred.replace("demo_google_", "").split(":")
        email = parts[0] if parts and parts[0] else "candidate.google@gmail.com"
        full_name = parts[1] if len(parts) > 1 and parts[1] else "Google Candidate"
        google_id = "google_demo_" + email.replace("@", "_").replace(".", "_")
    else:
        # 2. Live Google ID Token Verification
        try:
            from google.oauth2 import id_token
            from google.auth.transport import requests as google_requests
            
            target_aud = req.client_id or os.getenv("GOOGLE_CLIENT_ID") or None
            idinfo = id_token.verify_oauth2_token(
                cred,
                google_requests.Request(),
                audience=target_aud if target_aud else None
            )
            email = idinfo.get("email")
            full_name = idinfo.get("name") or (email.split("@")[0] if email else "Google Candidate")
            google_id = idinfo.get("sub")
        except Exception as e:
            try:
                import urllib.request, json
                url = f"https://oauth2.googleapis.com/tokeninfo?id_token={cred}"
                with urllib.request.urlopen(url, timeout=8) as response:
                    data = json.loads(response.read().decode())
                    email = data.get("email")
                    full_name = data.get("name") or (email.split("@")[0] if email else "Google Candidate")
                    google_id = data.get("sub")
            except Exception as e2:
                print(f"[Google Auth Verification Error]: {e} / {e2}")
                raise HTTPException(status_code=401, detail="Google token verification failed. Please check credentials.")

    if not email:
        raise HTTPException(status_code=400, detail="Could not retrieve email from Google token.")

    tracker = ApplicationTracker()
    user = tracker.get_or_create_google_user(email=email, full_name=full_name or email.split("@")[0], google_id=google_id or "")
    token = create_access_token(user["id"], user["email"])

    return {
        "status": "success",
        "message": "Signed in with Google successfully.",
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
async def upload_multiple_cvs(files: List[UploadFile] = File(...)):
    from ingestion.intake_engine import IntakeEngine
    engine = IntakeEngine()
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
async def upload_chat_history(files: List[UploadFile] = File(...)):
    from ingestion.intake_engine import IntakeEngine
    engine = IntakeEngine()
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
def parse_github(req: GitHubParseRequest):
    from ingestion.intake_engine import IntakeEngine
    engine = IntakeEngine()
    data = engine.parse_github_profile(req.url_or_username)
    return {"status": "success", "github": data}

@app.post("/api/profile/parse-linkedin")
def parse_linkedin(req: LinkedInParseRequest):
    from ingestion.intake_engine import IntakeEngine
    engine = IntakeEngine()
    data = engine.parse_linkedin_text_or_url(req.linkedin_url, req.raw_text or "")
    return {"status": "success", "linkedin": data, "profile": engine.persona_builder.profile}

@app.post("/api/profile/upload-linkedin-pdf")
async def upload_linkedin_pdf(file: UploadFile = File(...)):
    from ingestion.intake_engine import IntakeEngine
    engine = IntakeEngine()
    clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', Path(file.filename or "export.pdf").name)
    save_path = UPLOADS_DIR / f"linkedin_{clean_name}"
    with open(save_path, "wb") as out:
        out.write(await file.read())
    data = engine.parse_linkedin_pdf(save_path)
    return {"status": "success", "linkedin": data, "profile": engine.persona_builder.profile}

@app.post("/api/profile/parse-website")
def parse_website(req: WebsiteParseRequest):
    from ingestion.intake_engine import IntakeEngine
    engine = IntakeEngine()
    data = engine.scrape_personal_website(req.website_url)
    return {"status": "success", "website": data}

@app.post("/api/profile/synthesize")
def synthesize_profile(req: SynthesizeProfileRequest):
    from ingestion.intake_engine import IntakeEngine
    engine = IntakeEngine()
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
def tailor_cv(req: TailorRequest):
    user_id = req.user_id or "default"
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

    import re
    safe_comp = re.sub(r'[^a-zA-Z0-9_-]', '_', req.company).strip('_') or "Company"
    clean_uid = re.sub(r'[^a-zA-Z0-9_-]', '_', user_id)
    try:
        pdf_gen = PDFResumeBuilder()
        cv_out = GENERATED_DIR / f"Europass_CV_{clean_uid}_{safe_comp}.pdf"
        cl_out = GENERATED_DIR / f"Cover_Letter_{clean_uid}_{safe_comp}.pdf"
        pdf_gen.build_resume_pdf(tailored_resume, cv_out)
        pdf_gen.build_cover_letter_pdf(cover_letter, pb.profile, cl_out)
    except Exception as e:
        print(f"[Tailor Pre-build Error]: {e}")
    
    return {
        "tailored_resume": tailored_resume,
        "cover_letter": cover_letter
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

@app.get("/api/documents/preview")
def preview_document(type: str = "cv", company: str = "Company", job_title: str = "Software Engineer", user_id: str = Depends(get_current_user_id)):
    """Returns or generates on the fly the Europass CV or Cover Letter PDF for preview."""
    import re
    from pathlib import Path
    from generators.pdf_builder import PDFResumeBuilder
    from ingestion.persona_builder import PersonaBuilder
    
    try:
        GENERATED_DIR.mkdir(parents=True, exist_ok=True)
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
            # Always build fresh tailored cover letter for company and job title
            ident = pb.profile.get("identity", {})
            full_name = ident.get("full_name") or "M.S. Mohamed Sujahath"
            phone = ident.get("phone") or "+971 50 229 1865"
            email = ident.get("email") or "sujahathmhmd@gmail.com"
            linkedin = ident.get("linkedin") or "linkedin.com/in/mohamed-sujahath"
            github = ident.get("github") or "github.com/SujahathMSM"
            
            cl_text = (
                f"Dear {company} Hiring Team,\n\n"
                f"I am writing to express my enthusiastic interest in the {job_title} opening at {company}.\n\n"
                f"As a production-tested Backend Software Engineer with a BScEngHons from the University of Moratuwa "
                f"(Sri Lanka's premier engineering institution), I specialize in high-throughput microservices, "
                f"distributed data architectures, and PostgreSQL/TimescaleDB optimization.\n\n"
                f"In my current engineering role at Blue Brand IP Institute, I overhauled asynchronous data pipelines, "
                f"reducing polling failures from 80% to 0% and slashing system startup times by 90%.\n\n"
                f"I am based in Sri Lanka and 100% prepared for immediate international relocation with zero onboarding delay.\n\n"
                f"Please find my attached Europass CV for your review. I look forward to discussing how my experience will add value to {company}.\n\n"
                f"Sincerely,\n"
                f"{full_name}\n"
                f"{phone} | {email}\n"
                f"{linkedin} | {github}"
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


# --- OUTREACH & EMAIL DISPATCHER ---
@app.post("/api/outreach/draft")
def draft_outreach(req: OutreachDraftRequest):
    pb = PersonaBuilder(user_id=req.user_id or "default")
    cl_gen = CoverLetterGenerator(pb.profile)
    subject, body = cl_gen.generate_recruiter_email(
        job_title=req.job_title,
        company=req.company,
        hr_name=req.hr_name or "Hiring Team",
        specific_hook=req.tailored_content or ""
    )
    return {"subject": subject, "body": body, "to_email": req.hr_email}

@app.post("/api/outreach/send")
def send_outreach(req: SendEmailRequest):
    dispatcher = EmailDispatcher()
    result = dispatcher.dispatch(
        to_email=req.to_email,
        subject=req.subject,
        body_text=req.body,
        attachment_path=Path(req.cv_path) if req.cv_path else None,
        cover_letter_path=Path(req.cover_letter_path) if req.cover_letter_path else None,
        company=req.company,
        job_title=req.job_title,
        location=req.location,
        portal_link=req.portal_link,
        dry_run=req.dry_run,
        user_id=req.user_id or "default"
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
def update_application_status(req: StatusUpdateRequest):
    tracker = ApplicationTracker()
    ok = tracker.update_status(req.application_id, req.new_status, user_id=req.user_id or "default")
    return {"status": "success" if ok else "error"}


# --- CAREER PORTALS ---
@app.get("/api/portals")
def get_career_portals(region: Optional[str] = None, query: Optional[str] = None):
    from hunter.portals import CareerPortalManager
    mgr = CareerPortalManager()
    portals = mgr.list_portals(region=region, query=query)
    return {"portals": portals}

@app.post("/api/portals")
def add_career_portal(req: PortalAddRequest):
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
def delete_career_portal(portal_id: int):
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
def update_settings(req: SettingsUpdateRequest):
    update_env_file(req.settings)
    return {"status": "success", "updated": list(req.settings.keys())}

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
def save_user_settings(req: UserSettingsRequest):
    tracker = ApplicationTracker()
    existing = tracker.get_user_settings(req.user_id)
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
    tracker.save_user_settings(req.user_id, data)
    return {
        "status": "success",
        "user_id": req.user_id,
        "settings": {
            **data,
            "smtp_password": ("*" * 8) if pw_to_save else "",
            "has_password": bool(pw_to_save)
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
