from datetime import datetime
from typing import Dict, Any
from generators.llm_client import LLMClient

class CoverLetterGenerator:
    """Generates impressive, persuasive cover letters tailored to target job descriptions,
    highlighting authentic engineering strengths, measurable impacts, and international relocation readiness."""

    def __init__(self, master_profile: Dict[str, Any]):
        self.profile = master_profile
        self.llm = LLMClient()

    def generate(self, job_title: str, company: str, location: str, jd_text: str) -> str:
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
Write an impressive, persuasive executive cover letter for:
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
- Highly professional, persuasive, technically credible, and articulate.
- Express sharp, enthusiastic commitment to delivering immediate engineering value to {company}.
- Highlight candidate's genuine technical strengths and reliability in relation to {job_title} requirements.
- Express readiness for on-site, hybrid, or remote delivery in {location}.
- Include a strong, polite call to action for an interview.
- FORMATTING RULES:
  * Do NOT output candidate address, email, phone, date, or subject line at the start.
  * Start directly with the salutation: "Dear {company} Hiring Team," or "Dear Hiring Committee,".
  * Do NOT use markdown artifacts like `###` or `---` or `**Subject:**`.
  * NEVER use placeholder brackets like `[Date]`, `[Email Address]`, `[Phone]`, `[Your Name]`.
  * Conclude with:
    Sincerely,
    {full_name}
"""
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

I am writing to express my strong enthusiasm and formal application for the {job_title} position at {company}. With a solid foundation in engineering principles, hands-on technical execution, and structured problem-solving, I have developed a proven track record of architecting reliable systems and delivering measurable operational results.

Having closely reviewed your requirements for the {job_title} role, I was particularly drawn to {company}'s engineering initiatives. My core competencies in {skills_summary} align directly with the high standards your team demands. In my previous work, I have consistently focused on optimizing technical workflows, eliminating system bottlenecks, and translating ambiguous technical specifications into scalable, high-performance solutions.

Currently based in {current_loc}, I have structured my professional affairs to support seamless delivery for opportunities in {location}. I am adaptable to multicultural working environments and eager to contribute effectively to your engineering goals.

I welcome the opportunity to discuss how my technical expertise and proactive engineering mindset can support {company}'s strategic goals. Thank you for your time, consideration, and review of the attached resume.

Sincerely,

{full_name}
{identity.get('email', '')} | {identity.get('phone', '')}
{identity.get('linkedin', '')}
"""
