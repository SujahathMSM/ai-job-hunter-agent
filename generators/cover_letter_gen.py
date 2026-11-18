from datetime import datetime
from typing import Dict, Any
from generators.llm_client import LLMClient
from generators.style_checker import STYLE_RULES_FOR_PROMPT

class CoverLetterGenerator:
    """Generates impressive, persuasive cover letters tailored to target job descriptions,
    highlighting authentic engineering strengths, measurable impacts, and international relocation readiness."""

    def __init__(self, master_profile: Dict[str, Any]):
        self.profile = master_profile
        self.llm = LLMClient()

    def generate(self, job_title: str, company: str, location: str, jd_text: str, feedback: str = "") -> str:
        identity = self.profile.get("identity", {})
        full_name = identity.get("full_name", "Candidate")
        current_loc = identity.get("current_location", "Remote")
        reloc_pref = identity.get("relocation_status", "Available for relocation and remote engagement")
        education = self.profile.get("education", [])

        # Collect candidate's real skill profile
        skills_list = []
        for cat in self.profile.get("core_skills_categorized", []):
            skills_list.append(f"{cat.get('category')}: {cat.get('skills')}")
        skills_summary = " | ".join(skills_list) if skills_list else ", ".join(self.profile.get("technical_stack", [])[:10])

        edu_line = f"{education[0].get('degree', 'Engineering Degree')} from {education[0].get('institution', 'Accredited Institution')}" if education else "Engineering & Technical Background"

        current_date = datetime.now().strftime("%B %d, %Y")

        clean_jd = jd_text.strip() if jd_text and jd_text.strip().lower() not in ["none", "nan", "null"] else ""
        if len(clean_jd) < 80:
            clean_jd = f"High-impact opening for {job_title} at {company} in {location}. Requires strong engineering foundations, system architecture, API design, production delivery, and domain execution."

        prompt = f"""
Write a cover letter (under 300 words) for:
Candidate: {full_name}
Target Role: {job_title}
Target Company: {company}
Target Location: {location}

Candidate Authentic Background:
- Education: {edu_line}
- Professional Profile: {self.profile.get('summary', 'Experienced systems engineer')}
- Core Technical Competencies: {skills_summary}
- Current Location & Status: Based in {current_loc}. Relocation status: {reloc_pref}.

Target Job Requirements & Context:
{clean_jd[:1400]}

TONE & CRITERIA:
- Sound like a real person writing to a real hiring manager: specific, direct, a little informal is fine.
- Open with why this company or role, not a generic statement of interest.
- Connect 2-3 of the candidate's actual experiences or projects to the role's requirements. Use only facts from the background above.
- Mention availability for on-site, hybrid, or remote work in {location}.
- End with a short, polite request for an interview.

{STYLE_RULES_FOR_PROMPT}
- FORMATTING RULES:
  * Do NOT output candidate address, email, phone, date, or subject line at the start.
  * Start directly with the salutation: "Dear {company} Hiring Team," or "Dear Hiring Committee,".
  * Do NOT use markdown artifacts like `###` or `---` or `**Subject:**`.
  * NEVER use placeholder brackets like `[Date]`, `[Email Address]`, `[Phone]`, `[Your Name]`.
  * Conclude with:
    Sincerely,
    {full_name}
"""
        if feedback:
            prompt += f"\n\nREVIEWER FEEDBACK ON YOUR PREVIOUS DRAFT (MUST FIX):\n{feedback}\n"
        llm_text = self.llm.generate(prompt)
        if llm_text and len(llm_text.strip()) > 200:
            return llm_text.strip()

        # Deterministic Fallback Cover Letter Template
        return f"""{current_date}

Hiring Team & Human Resources
{company}
{location}

Subject: Application for {job_title} - {full_name}

Dear Hiring Team,

I'd like to apply for the {job_title} role at {company}. I've read through what the role involves, and it lines up closely with the work I've been doing.

The skills I use day to day are {skills_summary}. I'd be glad to walk you through how I've applied them and what I'd focus on in my first few months on your team.

I'm currently based in {current_loc} and can work on-site, hybrid or remotely for a role in {location}.

My CV is attached. I'd welcome a conversation about the role whenever suits you.

Sincerely,

{full_name}
{identity.get('email', '')} | {identity.get('phone', '')}
{identity.get('linkedin', '')}
"""
