"""Drafter -> Reviewer -> Revise loop.

Stage 1 (Drafter): ResumeTailorer + CoverLetterGenerator produce a draft.
Stage 2 (Reviewer): deterministic FactChecker finds unsupported claims and
AI-sounding wording (stock phrases, buzzword stacks, repeated bullet openers).
Stage 3 (Revise): flagged claims are sent back to the Drafter as feedback, up to
`max_revisions` times. Unverified skills are stripped deterministically.
Finally the ReviewerAgent issues the audit report (rule checks + LLM review).
"""
from typing import Any, Dict, List, Tuple

from generators.cover_letter_gen import CoverLetterGenerator
from generators.fact_checker import FactChecker, format_feedback
from generators.resume_tailorer import ResumeTailorer
from generators.reviewer_agent import ReviewerAgent

MAX_REVISIONS = 2


def run_drafter_reviewer(
    profile: Dict[str, Any],
    job_title: str,
    company: str,
    location: str,
    jd_text: str,
    max_revisions: int = MAX_REVISIONS,
) -> Tuple[Dict[str, Any], str, Dict[str, Any], ReviewerAgent]:
    tailorer = ResumeTailorer(profile)
    cl_gen = CoverLetterGenerator(profile)
    reviewer = ReviewerAgent(profile)
    checker = FactChecker(profile)

    prior_flags: List[Dict[str, str]] = []
    prior_style: List[Dict[str, str]] = []

    def draft(feedback: str = "") -> Tuple[Dict[str, Any], str]:
        resume = tailorer.generate_tailored_resume(job_title, company, location, jd_text, feedback=feedback)
        letter = cl_gen.generate(job_title, company, location, jd_text, feedback=feedback)
        # Skills are plain lists, so unverified ones are removed in code rather than via the LLM
        for item in checker.strip_unverified_skills(resume):
            prior_flags.append({"type": "unverified_tool", "claim": item, "section": "skills",
                                "detail": "Removed: not found in your profile."})
        return resume, letter

    resume, letter = draft()
    result = checker.check(resume, letter)
    rounds = 0

    def issue_keys(res: Dict[str, Any]) -> set:
        return {(f["type"], f["claim"].lower()) for f in res["flags"] + res["style_flags"]}

    while (result["flags"] or result["style_flags"]) and rounds < max_revisions:
        prior_flags.extend(f for f in result["flags"] if f not in prior_flags)
        prior_style.extend(f for f in result["style_flags"] if f not in prior_style)
        previous = issue_keys(result)
        resume, letter = draft(feedback=format_feedback(result["flags"], result["style_flags"]))
        rounds += 1
        result = checker.check(resume, letter)
        # Stop early if the Drafter made no progress (e.g. LLM unavailable, same output)
        if issue_keys(result) == previous:
            break

    audit = reviewer.audit_and_verify(
        tailored_resume=resume,
        cover_letter=letter,
        job_title=job_title,
        company=company,
        jd_text=jd_text,
        prior_flags=prior_flags,
        prior_style_flags=prior_style,
        revision_rounds=rounds,
    )
    return resume, letter, audit, reviewer
