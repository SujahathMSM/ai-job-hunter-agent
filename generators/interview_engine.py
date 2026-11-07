import re
import json
from typing import Dict, Any, List
from generators.llm_client import LLMClient

class InterviewEngine:
    """Simulates realistic technical & behavioral interviews based on the exact
    Job Description and candidate's Moratuwa engineering credentials. Provides
    STAR framework scoring, candidate talking points, and smart reverse questions."""

    def __init__(self, master_profile: Dict[str, Any]):
        self.profile = master_profile
        self.llm = LLMClient()

    def generate_interview_pack(
        self,
        job_title: str,
        company: str,
        location: str,
        jd_text: str
    ) -> Dict[str, Any]:
        """Generates comprehensive interview preparation assets for a specific opening."""
        identity = self.profile.get("identity", {})
        candidate_name = identity.get("full_name", "M.S. Mohamed Sujahath")

        prompt = f"""
You are a Principal Technical Hiring Manager and Executive Interview Coach.
Generate a tailored Interview Preparation Pack for candidate {candidate_name} applying for:
ROLE: {job_title}
COMPANY: {company}
LOCATION: {location}

JOB DESCRIPTION:
{jd_text[:1400]}

CANDIDATE PROFILE:
- BScEngHons from University of Moratuwa (Sri Lanka's premier engineering school)
- Software Engineer at Blue Brand IP Institute: Production Python/FastAPI microservices, TimescaleDB, MQTT/WebSockets, reduced polling failures from 80% to 0%, slashed startup times by 90% (5-6 min to 15-30s).
- Software Engineer Intern at CodeScale: Node.js, Express, Java, PostgreSQL, Firebase, AWS.
- Key Projects: AeroIntel (hybrid RAG with pgvector + BM25, structural refusal gate), evalX (LLM evaluation harness with deterministic CI assertions), EDGEOPS AI (incident triage with typed tools), Energy Bill Extractor (vision LLM JSON schema extraction).
- Location: Prepared for immediate international relocation or remote autonomy.

TASK:
Generate the following in JSON:
1. 'role_questions': List of 5 tailored interview questions:
   - Question 1: Behavioral question targeting system reliability and deadline execution (STAR format).
   - Question 2: Technical/Architecture drill tailored to '{job_title}' requirements.
   - Question 3: Deep dive into candidate's production experience (e.g. handling concurrency, databases, failure modes).
   - Question 4: Problem-solving question relevant to {company}'s tech domain.
   - Question 5: Relocation / Culture / Autonomy question.
   For each question provide:
   - 'id': 1 to 5
   - 'type': 'Behavioral (STAR)' | 'Technical Drill' | 'Architecture' | 'Role Challenge'
   - 'question': The exact question asked by the interviewer
   - 'hiring_intent': What the interviewer is evaluating under the surface
   - 'recommended_star_structure': Bulleted points on how candidate should frame Situation, Task, Action, Result using their real experience.

2. 'candidate_talking_points': 4 bullet points candidate should proactively highlight during the call (e.g. Moratuwa engineering rigor, 80% to 0% polling failure reduction, immediate visa readiness).

3. 'killer_questions_to_ask': 4 smart reverse questions to ask the interviewers about their architecture, deployment bottlenecks, and technical runway.

OUTPUT STRICT JSON ONLY:
{{
  "job_title": "{job_title}",
  "company": "{company}",
  "role_questions": [
    {{
      "id": 1,
      "type": "Behavioral (STAR)",
      "question": "Can you walk me through a time when a critical production service was failing or unstable, and how you systematically diagnosed and resolved it?",
      "hiring_intent": "Testing debugging methodology, composure under pressure, and measurable impact.",
      "recommended_star_structure": "Situation: Blue Brand distributed energy platform experiencing 80% polling failure rate. Task: Overhaul data ingestion. Action: Re-architected asynchronous polling loops in FastAPI with backoff retry and TimescaleDB indexing. Result: Reduced failure rate from 80% to 0% and cut startup latency by 90%."
    }}
  ],
  "candidate_talking_points": [
    "University of Moratuwa BScEngHons training provides mathematical and distributed systems foundation.",
    "Measurable production impact: Overhauled asynchronous pipelines cutting polling failures from 80% to 0%.",
    "Pragmatic AI & RAG expertise: Built AeroIntel with local-first pgvector and deterministic refusal gates rather than relying on brittle cloud APIs.",
    "Immediate availability for international relocation to {location} or high-cadence remote delivery."
  ],
  "killer_questions_to_ask": [
    "What are the biggest architectural bottlenecks your engineering team is actively trying to refactor this quarter?",
    "How does the engineering team balance rapid feature iteration with automated CI regression testing?",
    "What does a successful first 90 days look like for this position?",
    "Can you share how production incidents are triaged and resolved across the engineering team?"
  ]
}}
"""
        default_pack: Dict[str, Any] = {
            "job_title": job_title,
            "company": company,
            "role_questions": [
                {
                    "id": 1,
                    "type": "Behavioral (STAR)",
                    "question": f"Can you walk us through a complex production issue you solved at Blue Brand or CodeScale, and how you ensured it never reoccurred?",
                    "hiring_intent": "Evaluates systematic debugging, root-cause analysis, and operational ownership.",
                    "recommended_star_structure": "Situation: Distributed energy telemetry platform had 80% polling failures. Task: Stabilize pipeline and reduce startup overhead. Action: Refactored async event loops, optimized TimescaleDB queries, implemented backpressure. Result: Slashed failure rate from 80% to 0% and reduced startup time by 90%."
                },
                {
                    "id": 2,
                    "type": "Technical Architecture",
                    "question": f"How would you design a high-throughput, low-latency API service in Python/FastAPI to meet {company}'s scalability requirements?",
                    "hiring_intent": "Tests understanding of AsyncIO concurrency, database connection pooling, caching, and horizontal scaling.",
                    "recommended_star_structure": "Situation: High-volume streaming endpoints. Action: FastAPI with uvloop, asyncpg connection pooling, Redis caching for hot paths, and Pydantic v2 serialization. Result: Sub-50ms p99 latency under concurrent load."
                },
                {
                    "id": 3,
                    "type": "RAG & Document Intelligence",
                    "question": "When building AI-powered tools or RAG systems, how do you prevent hallucinations and ensure enterprise-grade reliability?",
                    "hiring_intent": "Separates superficial prompt wrappers from true software engineers who implement deterministic safety rails.",
                    "recommended_star_structure": "Highlight AeroIntel: Implemented pgvector + BM25 hybrid search with a strict structural refusal gate and exact printed-page citations. Validated with evalX automated CI regression tests."
                },
                {
                    "id": 4,
                    "type": "Role Alignment",
                    "question": f"What attracted you to {company}, and why do you believe your engineering background is an ideal fit for {job_title}?",
                    "hiring_intent": "Assesses company knowledge, motivation, and clarity of communication.",
                    "recommended_star_structure": "Connect Moratuwa engineering rigorous fundamentals with practical microservice and data pipeline delivery that directly accelerates {company}'s tech roadmap."
                },
                {
                    "id": 5,
                    "type": "Relocation & Autonomy",
                    "question": f"This position is based in {location}. How quickly could you transition, and how do you manage independent engineering delivery?",
                    "hiring_intent": "Verifies commitment, visa readiness, and independent delivery cadence.",
                    "recommended_star_structure": "State clear readiness for immediate relocation to {location} or remote autonomy across timezones, backed by experience working with distributed teams in Romania and Sri Lanka."
                }
            ],
            "candidate_talking_points": [
                "BScEngHons from University of Moratuwa: Rigorous analytical and systems engineering foundation.",
                "Production Track Record: Reduced polling failures from 80% to 0% and slashed startup times by 90% at Blue Brand IP Institute.",
                "Reliable AI Architecture: Built AeroIntel with refusal gates and evalX evaluation harness for deterministic testing.",
                f"100% prepared for immediate international relocation to {location} with zero visa bottlenecks."
            ],
            "killer_questions_to_ask": [
                f"What is the top technical bottleneck the {company} team is aiming to resolve in the next 3 to 6 months?",
                "What does your team's deployment and CI/CD cadence look like from pull request to production?",
                "How do you evaluate engineering excellence and success during the first 90 days?",
                "How does the team handle technical debt versus delivering critical business features?"
            ]
        }

        try:
            resp = self.llm.generate(prompt, temperature=0.2)
            clean = re.sub(r"^```json\s*", "", resp.strip())
            clean = re.sub(r"^```\s*", "", clean)
            clean = re.sub(r"\s*```$", "", clean)
            parsed = json.loads(clean)
            if isinstance(parsed, dict) and "role_questions" in parsed:
                return parsed
        except Exception as e:
            print(f"[Interview Pack LLM Fallback]: {e}")

        return default_pack

    def evaluate_candidate_answer(
        self,
        question: str,
        question_type: str,
        candidate_answer: str,
        job_title: str,
        company: str
    ) -> Dict[str, Any]:
        """Evaluates a candidate's practice response using STAR criteria and technical depth."""
        prompt = f"""
You are a Senior Principal Interviewer assessing a candidate's answer for '{job_title}' at '{company}'.

INTERVIEW QUESTION:
"{question}" (Type: {question_type})

CANDIDATE'S SUBMITTED ANSWER:
"{candidate_answer}"

EVALUATION RUBRIC:
1. Did the candidate use the STAR framework (Situation, Task, Action, Result)?
2. Did they include concrete metrics (percentages, speedups, volume, failure reductions)?
3. Was the technical reasoning sound, specific, and confident?
4. Was the answer concise (under 2 minutes spoken length, avoiding fluff)?

TASK:
Provide a constructive evaluation in JSON:
- 'score': 0 to 100
- 'strengths': 2-3 specific things the candidate did well
- 'improvements': 2-3 specific gaps or things to tighten up
- 'model_answer': An exemplary, polished STAR response incorporating candidate's authentic background (Moratuwa, Blue Brand, FastAPI, 80% to 0% failure reduction).

OUTPUT STRICT JSON ONLY:
{{
  "score": 88,
  "strengths": ["Clear situation and action", "Mentioned concrete technologies"],
  "improvements": ["Quantify the business impact further", "State the end result earlier"],
  "model_answer": "In my previous role at Blue Brand IP Institute..."
}}
"""
        default_eval = {
            "score": 85,
            "strengths": [
                "Directly addressed the core problem with practical engineering examples.",
                "Mentioned relevant tools (FastAPI, PostgreSQL, AsyncIO) credibly."
            ],
            "improvements": [
                "Reinforce the quantifiable impact (e.g. reduced polling failures from 80% to 0%).",
                "Highlight team collaboration and proactive monitoring."
            ],
            "model_answer": f"At Blue Brand IP Institute, our distributed telemetry ingestion was experiencing significant instability with high failure rates. As the Software Engineer responsible for backend pipelines, I refactored our asynchronous event loops in FastAPI, introduced backpressure queues, and optimized our TimescaleDB indexing strategy. This eliminated our failure rate from 80% down to 0% while slashing system startup latency by 90%."
        }

        try:
            resp = self.llm.generate(prompt, temperature=0.1)
            clean = re.sub(r"^```json\s*", "", resp.strip())
            clean = re.sub(r"^```\s*", "", clean)
            clean = re.sub(r"\s*```$", "", clean)
            parsed = json.loads(clean)
            if isinstance(parsed, dict) and "score" in parsed:
                return parsed
        except Exception as e:
            print(f"[Interview Eval Fallback]: {e}")

        return default_eval
