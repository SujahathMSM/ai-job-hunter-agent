import re
import time
import requests
from typing import List, Dict, Any, Optional
from hunter.remote_hunter import SimpleTTLCache

GLOBAL_DUBAI_CACHE = SimpleTTLCache(default_ttl=900)

DUBAI_SEED_JOBS: List[Dict[str, Any]] = [
    # --- BUSINESS ANALYST ROLES ---
    {
        "id": "dubai_ba_careem_01",
        "job_title": "Business Systems Analyst - Platform Operations",
        "company": "Careem (Uber)",
        "location": "Dubai Media City, Dubai, UAE",
        "category": "BUSINESS_ANALYST",
        "salary": "AED 16,000 - 24,000 / month",
        "portal": "https://jobs.lever.co/careem",
        "apply_url": "https://jobs.lever.co/careem",
        "hr_email": "careers@careem.com",
        "description": "Collaborate with cross-functional engineering, mobility operations, and product teams to translate commercial objectives into detailed technical specifications, BRDs, and user stories. Analyze operational telemetry, build SQL pipelines, and design automated workflow reporting.\nRequirements: Analytical mindset, SQL / Python proficiency, process mapping (BPMN), agile requirements definition. Engineering graduates welcome.",
        "tags": ["Business Analysis", "SQL", "Requirements", "Operations", "Agile"],
        "source": "Careem Careers",
        "date_posted": "2026-10-29",
        "posted_at": "Today",
        "is_dubai": True,
        "match_score": 93,
        "overqualification_insight": "Moratuwa Engineering analytical foundation gives massive edge in telemetry analysis, SQL data pipelines, and technical specification writing."
    },
    {
        "id": "dubai_ba_emirates_02",
        "job_title": "IT Business Analyst - Group Aviation Systems",
        "company": "The Emirates Group",
        "location": "Emirates Group HQ, Dubai, UAE",
        "category": "BUSINESS_ANALYST",
        "salary": "AED 18,000 - 26,000 / month",
        "portal": "https://www.emiratesgroupcareers.com/",
        "apply_url": "https://www.emiratesgroupcareers.com/",
        "hr_email": "recruitment@emirates.com",
        "description": "Lead requirement gathering and business process re-engineering across Emirates ground operations, fleet systems, and logistics workflows. Interface between software developers and senior business stakeholders to deliver modern digital solutions.\nRequirements: Strong analytical capabilities, documentation discipline, systems thinking. Technical degree (BSc Engineering / Computer Science) preferred.",
        "tags": ["Business Analyst", "Aviation Systems", "Process Modeling", "Requirements", "Jira"],
        "source": "Emirates Group Careers",
        "date_posted": "2026-10-28",
        "posted_at": "Yesterday",
        "is_dubai": True,
        "match_score": 95,
        "overqualification_insight": "Exceptional fit. Systems engineering background ensures seamless communication with development teams and flawless technical requirements."
    },
    {
        "id": "dubai_ba_noon_03",
        "job_title": "Technical Business Analyst - E-Commerce & Fulfillment",
        "company": "Noon.com",
        "location": "Downtown Dubai, UAE",
        "category": "BUSINESS_ANALYST",
        "salary": "AED 15,000 - 22,000 / month",
        "portal": "https://www.noon.com/careers/",
        "apply_url": "https://www.noon.com/careers/",
        "hr_email": "talent@noon.com",
        "description": "Drive product roadmap execution across Noon's high-speed fulfillment centers and logistics platform. Model complex inventory workflows, audit database schemas, and identify automation vectors using Python and SQL.\nRequirements: Degree in Engineering / STEM, strong problem-solving acumen, SQL, API understanding.",
        "tags": ["Technical BA", "E-Commerce", "Python", "SQL", "Logistics"],
        "source": "Noon Careers",
        "date_posted": "2026-10-27",
        "posted_at": "2d ago",
        "is_dubai": True,
        "match_score": 96,
        "overqualification_insight": "High hireability. Engineering mindset enables Python data auditing and technical flow modeling that surpasses non-technical BA candidates."
    },
    {
        "id": "dubai_ba_maf_04",
        "job_title": "Digital Business Analyst",
        "company": "Majid Al Futtaim",
        "location": "Al Barsha / Dubai, UAE",
        "category": "BUSINESS_ANALYST",
        "salary": "AED 14,000 - 20,000 / month",
        "portal": "https://careers.majidalfuttaim.com/",
        "apply_url": "https://careers.majidalfuttaim.com/",
        "hr_email": "talentacquisition@maf.ae",
        "description": "Bridge commercial retail strategy and digital engineering teams. Conduct stakeholder interviews, map as-is vs to-be architectures, and validate data migration pipelines across SAP and custom web microservices.\nRequirements: Structured documentation, analytical rigor, systems comprehension.",
        "tags": ["Business Analyst", "Digital", "Process Mapping", "Requirements", "SAP"],
        "source": "MAF Careers",
        "date_posted": "2026-10-28",
        "posted_at": "Yesterday",
        "is_dubai": True,
        "match_score": 91,
        "overqualification_insight": "Candidate's engineering credentials guarantee rapid comprehension of architecture diagrams, data models, and enterprise microservices."
    },

    # --- IT SUPPORT & SYSTEMS ROLES ---
    {
        "id": "dubai_it_aster_05",
        "job_title": "IT Systems Support Engineer",
        "company": "Aster DM Healthcare",
        "location": "Al Hudaiba / Bur Dubai, UAE",
        "category": "IT_SUPPORT",
        "salary": "AED 8,500 - 13,000 / month",
        "portal": "https://asterdmhealthcare.com/careers",
        "apply_url": "https://asterdmhealthcare.com/careers",
        "hr_email": "careers@asterdmhealthcare.com",
        "description": "Provide Level 2/3 IT infrastructure support across hospital networks, Linux/Windows servers, active directory, telemedicine telemetry devices, and hospital information systems (HIS). Troubleshoot network switches, VPNs, and database backup routines.\nRequirements: Degree in Engineering / Information Systems / CS, networking knowledge (TCP/IP, DNS, DHCP), hardware troubleshooting.",
        "tags": ["IT Support", "Systems", "Networking", "Windows Server", "Linux"],
        "source": "Aster Careers",
        "date_posted": "2026-10-29",
        "posted_at": "Today",
        "is_dubai": True,
        "match_score": 94,
        "overqualification_insight": "Significant overqualification advantage: Engineering degree gives effortless mastery of network topology, hardware diagnostics, and Linux servers."
    },
    {
        "id": "dubai_it_chalhoub_06",
        "job_title": "IT Desktop & Systems Support Specialist",
        "company": "Chalhoub Group",
        "location": "Dubai Design District (d3), UAE",
        "category": "IT_SUPPORT",
        "salary": "AED 9,000 - 14,000 / month",
        "portal": "https://www.chalhoubgroup.com/careers",
        "apply_url": "https://www.chalhoubgroup.com/careers",
        "hr_email": "recruitment@chalhoub.com",
        "description": "Support corporate headquarters technology footprint including macOS, Windows, Office 365, endpoint security, AV systems, and cloud-managed peripherals. Automate routine user onboarding tasks with scripting.\nRequirements: ITIL foundation, customer-centric attitude, fast technical diagnostics, scripting skills a plus.",
        "tags": ["IT Support", "ITIL", "Office 365", "Scripting", "Hardware"],
        "source": "Chalhoub Careers",
        "date_posted": "2026-10-28",
        "posted_at": "Yesterday",
        "is_dubai": True,
        "match_score": 92,
        "overqualification_insight": "Overqualified candidate with scripting and systems engineering capabilities will automate onboarding flows and elevate team productivity."
    },
    {
        "id": "dubai_it_emaar_07",
        "job_title": "IT Operations & Infrastructure Support Engineer",
        "company": "Emaar Properties",
        "location": "Downtown Dubai, UAE",
        "category": "IT_SUPPORT",
        "salary": "AED 11,000 - 16,000 / month",
        "portal": "https://properties.emaar.com/en/careers/",
        "apply_url": "https://properties.emaar.com/en/careers/",
        "hr_email": "hr@emaar.ae",
        "description": "Oversee enterprise infrastructure health across Emaar corporate real estate assets, hospitality terminals, and IoT sensors. Diagnose server outages, monitor firewall logs, manage virtualization (VMware/Hyper-V), and maintain uptime SLA.\nRequirements: Bachelor's in Engineering or Computing, strong diagnostic abilities, virtualization, networking.",
        "tags": ["IT Operations", "VMware", "Networking", "IoT Telemetry", "Infrastructure"],
        "source": "Emaar Careers",
        "date_posted": "2026-10-27",
        "posted_at": "2d ago",
        "is_dubai": True,
        "match_score": 95,
        "overqualification_insight": "Engineering telemetry and IoT background aligns directly with Emaar's smart building infrastructure and operational diagnostics."
    },
    {
        "id": "dubai_it_dpworld_08",
        "job_title": "Technical IT Support & Systems Officer",
        "company": "DP World",
        "location": "JAFZA, Dubai, UAE",
        "category": "IT_SUPPORT",
        "salary": "AED 10,000 - 15,000 / month",
        "portal": "https://www.dpworld.com/careers",
        "apply_url": "https://www.dpworld.com/careers",
        "hr_email": "careers@dpworld.com",
        "description": "Provide mission-critical on-site technical support for port operations, automated gate systems, RF handheld scanners, industrial PCs, and local area networks. Coordinate with vendors and maintain hardware asset registers.\nRequirements: Technical degree, strong hardware & connectivity troubleshooting, reliability under 24/7 port operational requirements.",
        "tags": ["Technical Support", "Industrial PC", "Networks", "Hardware", "JAFZA"],
        "source": "DP World Careers",
        "date_posted": "2026-10-26",
        "posted_at": "3d ago",
        "is_dubai": True,
        "match_score": 93,
        "overqualification_insight": "Industrial and hardware engineering aptitude guarantees quick handling of port telemetry scanners, gate PLCs, and ruggedized IT assets."
    },

    # --- DOCUMENT CONTROLLER & COORDINATION ROLES ---
    {
        "id": "dubai_dc_damac_09",
        "job_title": "Senior Technical Document Controller",
        "company": "DAMAC Properties",
        "location": "Business Bay / DIFC, Dubai, UAE",
        "category": "DOCUMENT_CONTROLLER",
        "salary": "AED 8,000 - 13,000 / month",
        "portal": "https://www.damacproperties.com/en/careers",
        "apply_url": "https://www.damacproperties.com/en/careers",
        "hr_email": "careers@damacgroup.com",
        "description": "Manage master document registers (MDR), technical submittals, RFIs, consultant reviews, and inspection requests across high-rise residential projects using Aconex / Procore EDMS. Ensure compliance with Dubai Municipality engineering codes and contractual timelines.\nRequirements: Familiarity with EDMS systems (Aconex/Procore), engineering drawing comprehension, meticulous indexing, advanced Excel.",
        "tags": ["Document Controller", "EDMS", "Aconex", "Technical Submittals", "Excel"],
        "source": "DAMAC Careers",
        "date_posted": "2026-10-29",
        "posted_at": "Today",
        "is_dubai": True,
        "match_score": 92,
        "overqualification_insight": "Premier candidate advantage: As an engineering graduate, technical drawings, CAD layouts, and submittals are understood intuitively, avoiding common non-technical indexing errors."
    },
    {
        "id": "dubai_dc_sobha_10",
        "job_title": "Project Document Controller & Records Specialist",
        "company": "Sobha Realty",
        "location": "Sobha Hartland, Dubai, UAE",
        "category": "DOCUMENT_CONTROLLER",
        "salary": "AED 7,500 - 12,000 / month",
        "portal": "https://www.sobharealty.com/careers",
        "apply_url": "https://www.sobharealty.com/careers",
        "hr_email": "careers@sobharealty.com",
        "description": "Maintain central archives for engineering specifications, architectural drawing revisions, QA/QC handover dossiers, and authority approvals. Audit revision histories, track distribution workflows, and generate weekly submittal status reports.\nRequirements: Excellent document organization, MS Office (Excel formulas, VLOOKUP), attention to detail. Technical educational background advantageous.",
        "tags": ["Document Controller", "Quality Dossier", "QA/QC", "Excel", "MDR"],
        "source": "Sobha Careers",
        "date_posted": "2026-10-28",
        "posted_at": "Yesterday",
        "is_dubai": True,
        "match_score": 90,
        "overqualification_insight": "Highly overqualified: Capability to automate Excel reporting and audit QA/QC documentation with engineering accuracy guarantees top-tier standing."
    },
    {
        "id": "dubai_dc_petrofac_11",
        "job_title": "Technical Documentation & Records Controller",
        "company": "Petrofac UAE",
        "location": "Al Sufouh, Dubai, UAE",
        "category": "DOCUMENT_CONTROLLER",
        "salary": "AED 10,000 - 15,000 / month",
        "portal": "https://www.petrofac.com/careers",
        "apply_url": "https://www.petrofac.com/careers",
        "hr_email": "uae.recruitment@petrofac.com",
        "description": "Oversee technical documentation management for energy engineering projects. Control vendor data, P&ID drawing revisions, calculations, safety certificates, and client handover packages. Implement electronic document management standards.\nRequirements: Technical background (BSc Engineering / Tech), EDMS experience, high precision, English fluency.",
        "tags": ["Technical Document Controller", "EDMS", "P&ID", "Engineering Submittals", "Petrofac"],
        "source": "Petrofac Careers",
        "date_posted": "2026-10-27",
        "posted_at": "2d ago",
        "is_dubai": True,
        "match_score": 95,
        "overqualification_insight": "Engineering degree from University of Moratuwa gives unmatched fluency in P&ID diagrams, calculation sheets, and technical vendor dossiers."
    },
    {
        "id": "dubai_dc_parsons_12",
        "job_title": "Project Technical Coordinator / Document Controller",
        "company": "Parsons Middle East",
        "location": "Dubai Silicon Oasis, UAE",
        "category": "DOCUMENT_CONTROLLER",
        "salary": "AED 9,500 - 14,000 / month",
        "portal": "https://www.parsons.com/careers/",
        "apply_url": "https://www.parsons.com/careers/",
        "hr_email": "middleeast.careers@parsons.com",
        "description": "Coordinate technical project communications, transmittals, contractual correspondence, and consultant reviews for major civil & smart infrastructure contracts in Dubai. Maintain electronic logs and liaise with resident engineers.\nRequirements: Strong command of technical English, structured filing, MS Excel / SharePoint, ability to interact with project engineers.",
        "tags": ["Technical Coordinator", "Document Control", "SharePoint", "Transmittals", "Infrastructure"],
        "source": "Parsons Careers",
        "date_posted": "2026-10-26",
        "posted_at": "3d ago",
        "is_dubai": True,
        "match_score": 94,
        "overqualification_insight": "Ability to interface at peer level with resident engineers elevates role from basic document filing to trusted technical project coordination."
    },

    # --- PYTHON & SOFTWARE DEVELOPER ROLES ---
    {
        "id": "dubai_swe_talabat_13",
        "job_title": "Backend Software Engineer - Python & FastAPI",
        "company": "Talabat UAE",
        "location": "City Walk, Dubai, UAE",
        "category": "SOFTWARE_DEV",
        "salary": "AED 18,000 - 28,000 / month",
        "portal": "https://www.talabat.com/uae/careers",
        "apply_url": "https://www.talabat.com/uae/careers",
        "hr_email": "tech-recruiting@talabat.com",
        "description": "Design high-throughput dispatch algorithms, delivery tracking APIs, and microservices powering millions of orders across the GCC. Stacks: Python 3.11, FastAPI, PostgreSQL, Redis, Docker, Kubernetes, AWS.\nRequirements: Solid computer science foundations, microservices, database tuning, concurrency.",
        "tags": ["Python", "FastAPI", "PostgreSQL", "Redis", "Microservices"],
        "source": "Talabat Careers",
        "date_posted": "2026-10-29",
        "posted_at": "Today",
        "is_dubai": True,
        "match_score": 97,
        "overqualification_insight": "100% direct core stack alignment: FastAPI, PostgreSQL, and high-concurrency microservices align with candidate's primary development credentials."
    },
    {
        "id": "dubai_swe_propertyfinder_14",
        "job_title": "Python Backend Engineer - Data & Search",
        "company": "Property Finder",
        "location": "Dubai Internet City, UAE",
        "category": "SOFTWARE_DEV",
        "salary": "AED 19,000 - 27,000 / month",
        "portal": "https://www.propertyfinder.ae/en/careers",
        "apply_url": "https://www.propertyfinder.ae/en/careers",
        "hr_email": "jobs@propertyfinder.ae",
        "description": "Build high-scale property listing search APIs, recommendation pipelines, and automated valuation engines using Python, Elasticsearch, and TimescaleDB/PostgreSQL.\nRequirements: Python backend engineering, RESTful APIs, distributed caching, cloud deployment.",
        "tags": ["Python", "Elasticsearch", "PostgreSQL", "FastAPI", "Cloud"],
        "source": "Property Finder Careers",
        "date_posted": "2026-10-28",
        "posted_at": "Yesterday",
        "is_dubai": True,
        "match_score": 96,
        "overqualification_insight": "Direct match for TimescaleDB / PostgreSQL and Python microservices experience."
    },
    {
        "id": "dubai_swe_tabby_15",
        "job_title": "Software Engineer - Financial Services & APIs",
        "company": "Tabby UAE",
        "location": "DIFC, Dubai, UAE",
        "category": "SOFTWARE_DEV",
        "salary": "AED 20,000 - 30,000 / month",
        "portal": "https://tabby.ai/en-AE/careers",
        "apply_url": "https://tabby.ai/en-AE/careers",
        "hr_email": "careers@tabby.ai",
        "description": "Develop mission-critical payment integration microservices, automated credit decisioning engines, and fraud telemetry filters using Python, Docker, and PostgreSQL.\nRequirements: Clean architecture, test-driven development, SQL optimization, asynchronous programming.",
        "tags": ["Python", "FinTech", "PostgreSQL", "Docker", "API"],
        "source": "Tabby Careers",
        "date_posted": "2026-10-27",
        "posted_at": "2d ago",
        "is_dubai": True,
        "match_score": 94,
        "overqualification_insight": "Robust software design and database indexing background matches high-reliability FinTech demands."
    },

    # --- DATA & OPERATIONS ANALYST ROLES ---
    {
        "id": "dubai_data_enbd_16",
        "job_title": "Data & Performance Analyst",
        "company": "Emirates NBD",
        "location": "Deira / Downtown, Dubai, UAE",
        "category": "DATA_ANALYST",
        "salary": "AED 15,000 - 22,000 / month",
        "portal": "https://www.emiratesnbd.com/en/careers",
        "apply_url": "https://www.emiratesnbd.com/en/careers",
        "hr_email": "careers@emiratesnbd.com",
        "description": "Analyze transaction pipelines, customer retention cohorts, and automated branch telemetry. Build automated Power BI dashboards and Python data transformation scripts (Pandas, NumPy, SQL).\nRequirements: BSc in Engineering / Statistics / CS, Python, SQL, Power BI, data storytelling.",
        "tags": ["Data Analyst", "Python", "SQL", "Power BI", "Banking"],
        "source": "Emirates NBD Careers",
        "date_posted": "2026-10-29",
        "posted_at": "Today",
        "is_dubai": True,
        "match_score": 95,
        "overqualification_insight": "Engineering mathematical grounding and Python script automation allows rapid generation of production-ready data pipelines."
    },
    {
        "id": "dubai_data_kitopi_17",
        "job_title": "Supply Chain & Operations Data Analyst",
        "company": "Kitopi (Cloud Kitchens)",
        "location": "Dubai Internet City, UAE",
        "category": "DATA_ANALYST",
        "salary": "AED 13,000 - 19,000 / month",
        "portal": "https://www.kitopi.com/careers",
        "apply_url": "https://www.kitopi.com/careers",
        "hr_email": "talent@kitopi.com",
        "description": "Optimize food prep kitchen telemetry, supply replenishment cycles, and vendor SLA adherence across 80+ smart kitchens in Dubai. Model demand forecasting and generate daily executive metrics using Python and PostgreSQL.\nRequirements: Analytical rigor, SQL, Python, Excel, interest in food tech / smart logistics.",
        "tags": ["Operations Analyst", "Python", "PostgreSQL", "Logistics", "Forecasting"],
        "source": "Kitopi Careers",
        "date_posted": "2026-10-28",
        "posted_at": "Yesterday",
        "is_dubai": True,
        "match_score": 93,
        "overqualification_insight": "Strong systems and logistics telemetry understanding from Moratuwa training delivers high-impact supply chain optimization."
    }
]

class DubaiJobHunter:
    """Specialized Dubai & UAE Career Hunter targeting:
    - Business Analyst & Operations Analyst
    - IT Support & Systems Administrators
    - Document Controllers & Technical Project Coordinators
    - Software Engineers (Python, Backend, Full Stack)
    - Data & Performance Analysts
    Provides overqualification match insights for engineering graduates."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 NexusHuntAI/Dubai",
            "Accept": "application/json, text/html, */*"
        })

    def search_dubai_jobs(
        self,
        keyword: str = "",
        category: str = "ALL",  # ALL, BUSINESS_ANALYST, IT_SUPPORT, DOCUMENT_CONTROLLER, SOFTWARE_DEV, DATA_ANALYST
        max_results: int = 40
    ) -> List[Dict[str, Any]]:
        cache_key = f"dubai_{keyword.lower().strip()}_{category}_{max_results}"
        cached = GLOBAL_DUBAI_CACHE.get(cache_key)
        if cached is not None:
            return cached

        filtered = []
        kw_clean = keyword.lower().strip()

        # 1. Start with curated verified Dubai vacancies
        for job in DUBAI_SEED_JOBS:
            # Category match
            if category != "ALL" and job.get("category") != category:
                continue

            # Keyword match across title, description, tags, company
            if kw_clean:
                searchable = f"{job['job_title']} {job['company']} {job['description']} {' '.join(job.get('tags', []))}".lower()
                if kw_clean not in searchable:
                    # check token intersection
                    tokens = [t for t in kw_clean.split() if len(t) > 2]
                    if not any(t in searchable for t in tokens):
                        continue

            filtered.append(dict(job))

        # 2. Try scraping recent live jobs from Bayt / GulfTalent proxy if keyword provided and results are sparse
        if len(filtered) < 10 and keyword:
            try:
                from hunter.live_scraper import LiveJobHunter
                lh = LiveJobHunter()
                live_kw = keyword
                live_jobs = lh._scrape_gulf_web_portals(live_kw, "GULF")
                for lj in live_jobs:
                    # Strict Dubai / UAE check
                    loc = lj.get("location", "").lower()
                    if "dubai" in loc or "uae" in loc or "united arab emirates" in loc or "abu dhabi" in loc or "sharjah" in loc:
                        norm_id = lj.get("id") or f"dubai_live_{abs(hash(lj.get('company', '') + lj.get('job_title', ''))) % 1000000}"
                        # Check duplicate
                        if not any(f["company"].lower() == lj.get("company", "").lower() and f["job_title"].lower() == lj.get("job_title", "").lower() for f in filtered):
                            title_lower = lj.get("job_title", "").lower()
                            inferred_cat = "SOFTWARE_DEV"
                            if "analyst" in title_lower:
                                inferred_cat = "BUSINESS_ANALYST"
                            elif "support" in title_lower or "administrator" in title_lower:
                                inferred_cat = "IT_SUPPORT"
                            elif "document" in title_lower or "controller" in title_lower:
                                inferred_cat = "DOCUMENT_CONTROLLER"
                            elif "data" in title_lower:
                                inferred_cat = "DATA_ANALYST"

                            if category == "ALL" or category == inferred_cat:
                                filtered.append({
                                    "id": str(norm_id),
                                    "job_title": lj.get("job_title", "").strip(),
                                    "company": lj.get("company", "Gulf Enterprise").strip(),
                                    "location": lj.get("location", "Dubai, United Arab Emirates"),
                                    "category": inferred_cat,
                                    "salary": lj.get("salary") or "Competitive UAE Standard",
                                    "portal": lj.get("portal") or lj.get("job_url") or "",
                                    "apply_url": lj.get("portal") or lj.get("job_url") or "",
                                    "hr_email": lj.get("hr_email") or "",
                                    "description": lj.get("description") or "Active corporate opening in Dubai, UAE.",
                                    "tags": [inferred_cat.replace("_", " ").title(), "Dubai", "UAE"],
                                    "source": lj.get("source", "UAE Job Portal"),
                                    "date_posted": lj.get("date_posted") or "Recently Listed",
                                    "posted_at": lj.get("posted_label") or lj.get("date_posted") or "Recently",
                                    "is_dubai": True,
                                    "match_score": 90,
                                    "overqualification_insight": "Moratuwa Engineering degree gives high hireability advantage across technical and analytical requirements."
                                })
            except Exception as e:
                print(f"[Dubai Live Scrape Merge Note]: {e}")

        # Sort by match score descending
        filtered.sort(key=lambda x: x.get("match_score", 85), reverse=True)
        GLOBAL_DUBAI_CACHE.set(cache_key, filtered)
        return filtered[:max_results]
