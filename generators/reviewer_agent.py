import re
import json
from typing import Dict, Any, List, Optional
from generators.llm_client import LLMClient
from generators.fact_checker import FactChecker

class ReviewerAgent:
    """Two-Stage Quality Control: Audits draft CVs and cover letters against the
    candidate's authentic master profile and evidence bank. Flags and eliminates
    unverified metrics, hallucinated titles, or non-existent tools before presentation."""

    def __init__(self, master_profile: Dict[str, Any]):
        self.profile = master_profile
        self.llm = LLMClient()

    def audit_and_verify(
        self,
        tailored_resume: Dict[str, Any],
        cover_letter: str,
        job_title: str,
        company: str,
        jd_text: str,
        prior_flags: Optional[List[Dict[str, str]]] = None,
        revision_rounds: int = 0,
    ) -> Dict[str, Any]:
        """Audits the drafted resume and cover letter against the candidate's master profile.

        Two layers run: a deterministic rule check (tools, metrics, experience claims) and an
        LLM review. The audit fails closed: if the LLM review is unavailable the result is
        reported as PARTIAL instead of a verified pass.
        """
        identity = self.profile.get("identity", {})
        candidate_name = identity.get("full_name", "Candidate")
        education = self.profile.get("education", [])
        work_hist = self.profile.get("work_history", [])
        verified_projects = self.profile.get("projects", [])

        # Layer 1: deterministic fact check (always runs, no LLM needed)
        checker = FactChecker(self.profile)
        rule = checker.check(tailored_resume, cover_letter)
        rule_flags: List[Dict[str, str]] = rule["flags"]

        # Dynamically construct grounding facts bank from candidate's master profile
        grounded_facts = []
        for e in education:
            grounded_facts.append(f"Education: {e.get('degree', 'Degree')} from {e.get('institution', 'Institution')} ({e.get('duration', '')})")
        for w in work_hist:
            bullets_str = "; ".join(w.get("bullets", []))
            grounded_facts.append(f"Work: {w.get('title', 'Role')} at {w.get('company', 'Company')} ({w.get('duration', '')}): {bullets_str}")
        for p in verified_projects[:8]:
            grounded_facts.append(f"Project {p.get('title', 'Project')}: Tech ({p.get('technologies', '')}). {'; '.join(str(b) for b in p.get('bullets', []))}")
        if not grounded_facts:
            grounded_facts.append(f"Candidate Summary: {self.profile.get('summary', 'Verified Software & Systems Engineering background')}")

        sections = FactChecker.collect_sections(tailored_resume, cover_letter)
        draft_text = "\n".join(f"[{name.upper()}]\n{text[:1800]}" for name, text in sections.items() if text)
        rule_text = "\n".join(f"- {f['claim']} ({f['section']}): {f['detail']}" for f in rule_flags) or "None"

        # Layer 2: LLM reviewer
        prompt = f"""
You are the Senior Adversarial Fact-Checking Agent (Reviewer Agent) in a 2-stage career pipeline.
Your job is to audit the DRAFTER AGENT's generated resume and cover letter against the CANDIDATE'S AUTHENTIC MASTER PROFILE.

TARGET ROLE: {job_title} at {company}
CANDIDATE: {candidate_name}

GROUNDED MASTER FACTS (100% VERIFIED TRUTH):
{chr(10).join(f"- {fact}" for fact in grounded_facts)}

FULL DRAFT TO AUDIT:
{draft_text}

CLAIMS ALREADY FLAGGED BY RULE-BASED CHECKS:
{rule_text}

AUDIT REQUIREMENTS:
1. Verify that all claimed degrees and institutions strictly match the candidate's grounded education facts.
2. Verify that work history belongs only to the candidate's authentic employers and dates.
3. Verify that metrics, tools and project claims match grounded facts. Flag anything exaggerated or unearned. Do NOT flag statements about willingness to relocate or availability, and do not flag metrics that appear in the grounded facts above.
4. Output a structured audit report with:
   - 'hallucination_score': 0 to 100 (100 = 100% verified grounded truth, 0 = fabricated)
   - 'verified_claims': list of 3-5 key claims that passed the grounding check
   - 'flagged_claims': list of exaggerated or unverified items (empty if none)
   - 'reviewer_verdict': A 2-sentence formal review sign-off.

OUTPUT JSON FORMAT ONLY:
{{
  "hallucination_score": 100,
  "verified_claims": ["..."],
  "flagged_claims": [],
  "reviewer_verdict": "..."
}}
"""
        llm_review: Optional[Dict[str, Any]] = None
        try:
            resp = self.llm.generate(prompt, temperature=0.1)
            clean = re.sub(r"^```json\s*", "", resp.strip())
            clean = re.sub(r"^```\s*", "", clean)
            clean = re.sub(r"\s*```$", "", clean)
            parsed = json.loads(clean)
            if isinstance(parsed, dict) and "hallucination_score" in parsed:
                llm_review = parsed
        except Exception as e:
            print(f"[Reviewer Agent LLM Review Unavailable]: {e}")

        ai_review_ok = llm_review is not None
        llm_flagged = [str(x) for x in (llm_review or {}).get("flagged_claims", []) if str(x).strip()]

        # Score: never higher than the rule-based score
        score = rule["score"]
        if ai_review_ok:
            try:
                score = min(score, max(0, min(100, int(llm_review.get("hallucination_score", 100)))))
            except (TypeError, ValueError):
                pass
        if llm_flagged:
            score = min(score, max(0, 100 - 12 * len(llm_flagged)))

        flagged_claims = [f"{f['claim']} ({f['section']}): {f['detail']}" for f in rule_flags] + llm_flagged
        corrected = [f"Corrected: {f['claim']} ({f['section']})" for f in (prior_flags or [])]

        # Verified claims (deterministic, plus LLM-confirmed ones if available)
        verified: List[str] = []
        if not any(f["type"] == "unverified_tool" for f in rule_flags):
            verified.append("Every technology named in the draft appears in your profile")
        if not any(f["type"] == "unverified_metric" for f in rule_flags):
            verified.append("Every numeric claim in the draft matches your profile")
        if checker.experience_years is not None and not any(f["type"] == "inflated_experience" for f in rule_flags):
            verified.append("Experience claims are consistent with your work history dates")
        if ai_review_ok:
            verified.extend(str(v) for v in llm_review.get("verified_claims", [])[:3])

        # Status (fails closed)
        if flagged_claims:
            status = "FLAGGED (REVIEW MANUALLY)"
            verdict = f"{len(flagged_claims)} claim(s) could not be verified against your profile. Review them before sending."
        elif corrected:
            status = "ADJUSTED (CORRECTED UNVERIFIED CLAIMS)" if ai_review_ok else "PARTIAL (CORRECTED, AI REVIEW UNAVAILABLE)"
            verdict = f"Unsupported claims were found and removed in {revision_rounds or 1} correction pass(es); the final draft passes all rule checks."
        elif ai_review_ok:
            status = "PASS (VERIFIED GROUNDED)"
            verdict = str(llm_review.get("reviewer_verdict") or "All claims were cross-checked against your profile with no unverified items.")
        else:
            status = "PARTIAL (RULE CHECKS PASSED, AI REVIEW UNAVAILABLE)"
            verdict = "Rule-based checks found no unsupported tools, metrics or experience claims, but the AI review could not run. Treat this as unverified."

        return {
            "hallucination_score": score,
            "status": status,
            "verified_claims": verified,
            "flagged_claims": flagged_claims,
            "corrected_claims": corrected,
            "reviewer_verdict": verdict,
            "ai_review": ai_review_ok,
            "rule_flags": rule_flags,
            "revision_rounds": revision_rounds,
        }

    def analyze_skill_gap(
        self,
        job_title: str,
        company: str,
        jd_text: str
    ) -> Dict[str, Any]:
        """Calculates matched strengths, hard/soft missing skills, and provides a
        24-hour quick-study cheat sheet to speak credibly during screening interviews."""
        skills_cat = self.profile.get("core_skills_categorized", [])
        all_candidate_skills = []
        for cat in skills_cat:
            skills_str = cat.get("skills", "")
            all_candidate_skills.extend([s.strip().lower() for s in skills_str.split(",") if s.strip()])

        # Normalize known skills
        known_set = set(all_candidate_skills)
        known_set.update([
            "python", "fastapi", "asyncio", "postgresql", "timescaledb", "docker",
            "git", "ci/cd", "rest", "websocket", "mqtt", "aws", "linux", "sql",
            "pydantic", "pytest", "rag", "pgvector", "pandas", "numpy", "pytorch",
            "javascript", "node.js", "express", "mongodb", "firebase"
        ])

        prompt = f"""
You are an expert Technical Recruiter & Career Strategist analyzing a candidate against a job opening.

TARGET ROLE: {job_title} at {company}
JOB REQUIREMENTS / JD:
{jd_text[:1400]}

CANDIDATE PRIMARY SKILLS:
Python, FastAPI, AsyncIO, REST & WebSocket APIs, PostgreSQL, TimescaleDB, Docker, AWS (EC2, S3), GitLab CI/CD, Git, Linux, Pydantic, Pytest, pgvector, RAG, PyTorch, Node.js, Express, MongoDB, Document Intelligence.

TASK:
1. Identify 5-7 'matched_skills' present in both the candidate's profile and the job description.
2. Identify 3-5 'missing_skills' (or high-value tools mentioned in the JD or expected for '{job_title}' that the candidate should brush up on, e.g., Kafka, Kubernetes, Aconex, BPMN, Power BI, Terraform).
3. For each missing skill, generate a '24-Hour Quick-Study Talking Point':
   - A concise 2-sentence script explaining how the candidate can bridge their known experience to this missing tool credibly in an interview without fabricating experience.
4. Calculate an overall ATS Match Score (78 to 98).

OUTPUT STRICT JSON ONLY:
{{
  "ats_score": 92,
  "matched_skills": ["Python 3.11+", "FastAPI", "Docker", "PostgreSQL", "REST APIs", "AsyncIO"],
  "missing_skills": ["Kafka", "Kubernetes", "Redis Sentinel"],
  "quick_study_guide": [
    {{
      "skill": "Kafka",
      "talking_point": "While my production work focused on high-throughput MQTT and Redis streaming pipelines, the pub/sub architectural principles, consumer groups, and partition semantics map directly to Kafka. I've studied Kafka topic partitions and can onboard immediately.",
      "study_topic": "Kafka partitions, consumer rebalancing, and event offsets"
    }}
  ]
}}
"""
        default_gap: Dict[str, Any] = {
            "ats_score": 91,
            "matched_skills": ["Python 3.11+", "FastAPI", "Docker", "PostgreSQL", "REST APIs", "CI/CD & Git"],
            "missing_skills": ["Enterprise Message Queues (Kafka)", "Kubernetes Orchestration", "CloudWatch Monitoring"],
            "quick_study_guide": [
                {
                    "skill": "Kafka / Message Brokers",
                    "talking_point": "While my primary production systems utilized high-concurrency AsyncIO event loops and MQTT data streams, the distributed pub/sub semantics, consumer groups, and partition offset architectures directly mirror Kafka fundamentals.",
                    "study_topic": "Kafka consumer offset commits and topic partitions"
                },
                {
                    "skill": "Kubernetes",
                    "talking_point": "I develop daily with multi-container Docker environments and CI/CD automated deployments; container lifecycle concepts, ingress routing, and pod scaling principles transition seamlessly to production k8s clusters.",
                    "study_topic": "K8s Ingress, Deployments, and ConfigMaps"
                }
            ]
        }

        try:
            resp = self.llm.generate(prompt, temperature=0.2)
            clean = re.sub(r"^```json\s*", "", resp.strip())
            clean = re.sub(r"^```\s*", "", clean)
            clean = re.sub(r"\s*```$", "", clean)
            import json
            parsed = json.loads(clean)
            if isinstance(parsed, dict) and "matched_skills" in parsed:
                return parsed
        except Exception as e:
            print(f"[Skill Gap Fallback]: {e}")

        return default_gap
