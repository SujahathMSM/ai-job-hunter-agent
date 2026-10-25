import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
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

class PDFGenRequest(BaseModel):
    tailored_resume: Dict[str, Any]

class OutreachDraftRequest(BaseModel):
    job_title: str
    company: str
    hr_name: Optional[str] = "Hiring Team"
    hr_email: str
    tailored_content: Optional[str] = None

class SendEmailRequest(BaseModel):
    to_email: str
    subject: str
    body: str
    company: str
    job_title: str
    location: str = "Gulf / Remote"
    portal_link: Optional[str] = None
    cv_path: Optional[str] = None
    dry_run: bool = True

class StatusUpdateRequest(BaseModel):
    application_id: int
    new_status: str

class SettingsUpdateRequest(BaseModel):
    settings: Dict[str, str]


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "NexusHunt AI", "version": "2.4"}


# --- PROFILE & CV INTAKE ---
@app.get("/api/profile")
def get_profile():
    pb = PersonaBuilder()
    return pb.profile

@app.post("/api/profile")
def update_profile(profile_data: Dict[str, Any]):
    pb = PersonaBuilder()
    pb.update_profile(profile_data)
    return {"status": "success", "profile": pb.profile}

@app.post("/api/profile/upload-cv")
async def upload_cv(file: UploadFile = File(...)):
    save_path = UPLOADS_DIR / file.filename
    with open(save_path, "wb") as f:
        f.write(await file.read())
    
    parser = CVParser()
    extracted = parser.parse_cv(save_path)
    if not extracted:
        raise HTTPException(status_code=400, detail="Could not extract text from CV.")
    
    pb = PersonaBuilder()
    updated = pb.build_from_sources(cv_data_list=[extracted], chat_insights=[])
    pb.update_profile(updated)
    return {"status": "success", "extracted": extracted, "profile": pb.profile}


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
def stream_jobs(keyword: str = "Python Developer", region: str = "GULF", max_results: int = 15):
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
                jd_text=j.get("description", "")
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


# --- GLOBAL RECRUITER & HR FINDER ---
@app.get("/api/hr/by-role/stream")
def stream_hr_by_role(role: str = "Python Developer", region: str = "GULF", limit: int = 10):
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
    pb = PersonaBuilder()
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


# --- OUTREACH & EMAIL DISPATCHER ---
@app.post("/api/outreach/draft")
def draft_outreach(req: OutreachDraftRequest):
    pb = PersonaBuilder()
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
        company=req.company,
        job_title=req.job_title,
        location=req.location,
        portal_link=req.portal_link,
        dry_run=req.dry_run
    )
    return result


# --- APPLICATION TRACKER ---
@app.get("/api/tracker/applications")
def list_applications():
    tracker = ApplicationTracker()
    apps = tracker.list_applications(limit=100)
    metrics = tracker.get_metrics()
    return {"metrics": metrics, "applications": apps}

@app.post("/api/tracker/update-status")
def update_application_status(req: StatusUpdateRequest):
    tracker = ApplicationTracker()
    ok = tracker.update_status(req.application_id, req.new_status)
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
