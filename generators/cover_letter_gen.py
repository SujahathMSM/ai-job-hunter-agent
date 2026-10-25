from datetime import datetime
from typing import Dict, Any
from generators.llm_client import LLMClient

class CoverLetterGenerator:
    """Generates impressive, persuasive cover letters tailored to target job descriptions,
    highlighting engineering domain strengths, measurable impacts, and international relocation readiness."""

    def __init__(self, master_profile: Dict[str, Any]):
        self.profile = master_profile
        self.llm = LLMClient()

    def generate(self, job_title: str, company: str, location: str, jd_text: str) -> str:
        identity = self.profile.get("identity", {})
        full_name = identity.get("full_name", "M.S. MOHAMED SUJAHATH")

        # Collect rich skill profile from core_skills_categorized
        skills_list = []
        for cat in self.profile.get("core_skills_categorized", []):
            skills_list.append(f"{cat.get('category')}: {cat.get('skills')}")
        skills_summary = " | ".join(skills_list) if skills_list else "Python, FastAPI, PostgreSQL, Docker, AWS, PyTorch, Systems Architecture"

        current_date = datetime.now().strftime("%B %d, %Y")

        clean_jd = jd_text.strip() if jd_text and jd_text.strip().lower() not in ["none", "nan", "null"] else ""
        if len(clean_jd) < 80:
            clean_jd = f"High-impact opening for {job_title} at {company} in {location}. Requires strong engineering foundations, system architecture, API design, production delivery, and domain execution."

        prompt = f"""
Write an impressive, persuasive executive cover letter for:
Candidate: {full_name}
Target Role: {job_title}
Target Company: {company}
Location: {location}
Candidate Qualifications & Background:
- Degree: BScEngHons, University of Moratuwa (Premier Engineering Institution in Sri Lanka)
- Production Experience: Software Engineer building high-reliability Python/FastAPI microservices, distributed data flows, edge-to-cloud systems, and automated evaluation pipelines (reducing polling failures from 80% to 0%, cutting startup times by 90%).
- Technical Skills: {skills_summary}
- Relocation Readiness: Based in Sri Lanka, 100% prepared for immediate international relocation to {location} (no visa or onboarding delays).

Target Job Context:
{clean_jd[:1400]}

TONE & CRITERIA:
- Highly professional, persuasive, technically credible, and articulate.
- Express sharp, enthusiastic commitment to delivering immediate engineering value to {company}.
- Highlight how candidate's deep production backend engineering rigor (FastAPI, high throughput, zero failure tolerance) directly bridges with {job_title} demands (e.g. building reliable, production-grade agentic workflows, RAG pipelines, or scalable microservices rather than fragile prototypes).
- Explicitly state complete readiness for immediate international relocation to {location}.
- Include a strong, polite call to action for an interview.
- CRITICAL FORMATTING:
  * Do NOT output any candidate address, email, phone, date, or subject line at the start.
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

        # Premium Fallback Cover Letter Template
        return f"""{current_date}

Hiring Team & Human Resources
{company}
{location}

Subject: Application for {job_title} - {full_name}

Dear Hiring Team,

I am writing to express my strong enthusiasm and formal application for the {job_title} position at {company}. With a rigorous foundation in engineering principles, hands-on technical execution, and complex problem-solving, I have developed a proven track record of architecting reliable systems and delivering measurable operational results.

Having closely reviewed your requirements for the {job_title} role, I was particularly drawn to {company}'s engineering initiatives. My core competencies in {skills_summary} align directly with the high standards your team demands. In my previous engineering endeavors, I have consistently focused on optimizing technical workflows, eliminating system bottlenecks, and translating ambiguous technical specifications into scalable, high-performance solutions.

Currently based in Sri Lanka, I have structured my personal and professional affairs to enable an immediate, seamless international relocation to {location}. I am fully prepared for international relocation, adaptable to multicultural working environments, and eager to contribute on-site or in hybrid capacities across {location}.

I welcome the opportunity to discuss how my technical expertise and proactive engineering mindset can support {company}'s strategic goals. Thank you for your time, consideration, and review of the attached resume.

Sincerely,

{full_name}
{identity.get('email', '')} | {identity.get('phone', '')}
{identity.get('linkedin', '')}
"""
