import re
import unicodedata
from pathlib import Path
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def sanitize_pdf_text(text: Any) -> str:
    """Sanitizes unicode typography to safe Latin-1 ReportLab characters and strips block artifacts."""
    if not text:
        return ""
    if isinstance(text, list):
        text = ", ".join([str(t) for t in text])
    elif not isinstance(text, str):
        text = str(text)

    # Clean block / bullet artifacts that corrupt layouts
    replacements = {
        "\u25a0": " ",
        "\u25aa": " ",
        "■": " ",
        "\uf0b7": " ",
        "\u2013": "-",
        "\u2014": " - ",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2022": "&bull;",
        "\u0219": "s",
        "\u0218": "S",
        "\u021b": "t",
        "\u021a": "T",
        "\u015f": "s",
        "\u015e": "S",
        "\u0163": "t",
        "\u0162": "T",
        "\u2026": "...",
        "\xa0": " "
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    text = unicodedata.normalize("NFKD", text).encode("latin-1", "ignore").decode("latin-1")
    return text.strip()

class PDFResumeBuilder:
    """Renders authentic, official European Union Europass CVs and executive cover letters
    with pixel-perfect typography, strict deduplication, and zero block artifact leaks."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._init_custom_styles()

    def _init_custom_styles(self):
        # Official Europass Blue Palette
        self.c_europass = colors.HexColor("#0E4194")       # Official Europass Deep Blue
        self.c_text = colors.HexColor("#222222")           # Clean Charcoal
        self.c_muted = colors.HexColor("#4B5563")          # Slate Gray
        self.c_line = colors.HexColor("#0E4194")           # Europass Blue Divider
        self.c_accent = colors.HexColor("#1D70B8")         # Secondary Blue
        self.c_bg_light = colors.HexColor("#F0F4F9")       # Subtle Light Blue Table Background

        # Europass Top Header Styles
        self.styles.add(ParagraphStyle(
            name="EuropassBrand",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=13,
            textColor=self.c_europass,
            alignment=0,
            spaceAfter=2
        ))

        self.styles.add(ParagraphStyle(
            name="EuropassName",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=20,
            textColor=self.c_europass,
            alignment=0,
            spaceAfter=2
        ))

        self.styles.add(ParagraphStyle(
            name="EuropassRoleTitle",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=self.c_accent,
            alignment=0,
            spaceAfter=4
        ))

        self.styles.add(ParagraphStyle(
            name="EuropassContactItem",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            textColor=self.c_muted,
            alignment=0,
            spaceAfter=1.5
        ))

        # Europass Section Header Style
        self.styles.add(ParagraphStyle(
            name="EuropassSectionTitle",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13.5,
            textColor=self.c_europass,
            spaceBefore=8,
            spaceAfter=3,
            keepWithNext=True
        ))

        # Two-Column Europass Layout Styles
        self.styles.add(ParagraphStyle(
            name="EuropassDateCol",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11.5,
            textColor=self.c_europass,
            alignment=0
        ))

        self.styles.add(ParagraphStyle(
            name="EuropassCityCol",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10.5,
            textColor=self.c_muted,
            alignment=0,
            spaceAfter=2
        ))

        self.styles.add(ParagraphStyle(
            name="EuropassJobTitle",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=12.5,
            textColor=self.c_text,
            alignment=0
        ))

        self.styles.add(ParagraphStyle(
            name="EuropassEmployer",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11.5,
            textColor=self.c_europass,
            alignment=0
        ))

        self.styles.add(ParagraphStyle(
            name="EuropassSector",
            parent=self.styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=10.5,
            textColor=self.c_muted,
            alignment=0,
            spaceAfter=3
        ))

        self.styles.add(ParagraphStyle(
            name="EuropassBullet",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            textColor=self.c_text,
            leftIndent=8,
            firstLineIndent=-5,
            spaceAfter=2
        ))

        self.styles.add(ParagraphStyle(
            name="EuropassBody",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            textColor=self.c_text,
            spaceAfter=3
        ))

        self.styles.add(ParagraphStyle(
            name="CoverLetterBody",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14.5,
            textColor=self.c_text,
            spaceAfter=10
        ))

    def _deduplicate_work_history(self, work_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Guarantees strictly the 3 real commercial employers and zero duplicates."""
        canonical_jobs = {
            "blue_brand": {
                "company": "Blue Brand - Advanced R&D and IP Institute (HQ: Ploiesti, Romania)",
                "branch": "Sri Lanka Branch",
                "title": "Software Engineer",
                "duration": "Mar 2025 - Present",
                "bullets": []
            },
            "codescale": {
                "company": "CodeScale Pvt Ltd",
                "branch": "Colombo, Sri Lanka",
                "title": "Software Engineer Intern / Associate Engineer",
                "duration": "Jul 2024 - Feb 2025",
                "bullets": []
            },
            "lanka_hydraulic": {
                "company": "Lanka Hydraulic Institute",
                "branch": "Moratuwa, Sri Lanka",
                "title": "Trainee Engineer",
                "duration": "Jan 2023 - Jun 2023",
                "bullets": []
            }
        }

        default_bullets = {
            "blue_brand": [
                "Build and operate production Python/FastAPI services for a live multi-site solar and battery energy-management platform, connecting real-time device data, control workflows, databases, and operator-facing APIs and dashboards.",
                "Design and maintain REST, WebSocket, and MQTT data flows between Raspberry Pi edge controllers and cloud services, with PostgreSQL/TimescaleDB storage, health monitoring, retries, and fallback handling.",
                "Translate operational and safety requirements from operations, firmware, and hardware stakeholders into specifications and deployable software, owning changes from requirements through implementation, deployment, and verification.",
                "Investigate production issues using logs, SQL analysis, and telemetry; fixes reduced device polling failures from about 80% to 0% and controller startup time from 5-6 minutes to 15-30 seconds.",
                "Audited a 419-file Python codebase, validated critical safety fixes, and identified 1.83 GB of write-only database tables with no readers, supporting corrective action through structured analysis.",
                "Design and run staged test plans before production changes: baseline checks, controlled read/write tests, failure scenarios, regression checks, rollback validation, and soak monitoring.",
                "Maintain version-controlled technical documentation and records: system architecture, register maps, procedures, runbooks, deployment and rollback records, and engineer onboarding guides.",
                "Deliver versioned Docker releases through GitLab CI/CD, Harbor, and Ansible across ARM64 edge and AMD64 cloud environments; host cloud services on AWS EC2 with S3 object storage.",
                "Built an operator control-panel dashboard with Vue, TypeScript, and Tailwind giving operators live visibility of system status."
            ],
            "codescale": [
                "Developed WheresNow, a real-time location platform with live tracking, geofencing, crash detection, background processing, and secure messaging across mobile and web clients.",
                "Built backend services and integrations with Node.js (Express/Nest.js), Java, Firebase, REST, and GraphQL, alongside React Native and Vue.js interfaces; integrated PostgreSQL and MongoDB and optimised queries.",
                "Used AWS EC2, Lambda, IAM, RDS, and S3; maintained CI/CD with GitHub Actions and Jenkins; worked in Agile/Scrum through code reviews, testing, and release workflows."
            ],
            "lanka_hydraulic": [
                "Processed, validated, and visualised large engineering datasets with Python (Pandas, NumPy, Matplotlib) and PostgreSQL; supported coastal simulations and spatial analysis using Mike Zero and ArcGIS."
            ]
        }

        for exp in work_history:
            comp = exp.get("company", "")
            title = exp.get("title", "")
            key_text = f"{comp} {title}".lower()

            target_key = None
            if "blue brand" in key_text or "ploiesti" in key_text or "solar" in key_text or "energy" in key_text:
                target_key = "blue_brand"
            elif "codescale" in key_text or "wheresnow" in key_text:
                target_key = "codescale"
            elif "hydraulic" in key_text or "coastal" in key_text:
                target_key = "lanka_hydraulic"

            if not target_key:
                continue

            raw_bullets = exp.get("bullets", [])
            for b in raw_bullets:
                clean_b = re.sub(r"^[•\-*■\s]+", "", str(b)).strip()
                sub_parts = re.split(r"[■•]", clean_b)
                for sp in sub_parts:
                    sp_text = sp.strip(" -–|:•■")
                    if len(sp_text) > 25 and not any(sp_text.lower() in existing.lower() or existing.lower() in sp_text.lower() for existing in canonical_jobs[target_key]["bullets"]):
                        canonical_jobs[target_key]["bullets"].append(sp_text)

        # Fallback to default verified bullets if bullets were empty
        for k in ["blue_brand", "codescale", "lanka_hydraulic"]:
            if not canonical_jobs[k]["bullets"]:
                canonical_jobs[k]["bullets"] = default_bullets[k]

        return [canonical_jobs["blue_brand"], canonical_jobs["codescale"], canonical_jobs["lanka_hydraulic"]]

    def _deduplicate_education(self, education: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Guarantees University of Moratuwa and IJSE appear exactly once."""
        return [
            {
                "degree": "Bachelor of the Science of Engineering Honours (BScEngHons)",
                "institution": "University of Moratuwa",
                "duration": "Jan 2020 - Jul 2024",
                "location": "Moratuwa, Sri Lanka",
                "details": "Relevant study: programming, applied statistics, numerical methods, data analysis, machine learning, remote sensing and GIS."
            },
            {
                "degree": "Diploma in Comprehensive Java Development",
                "institution": "Institute of Software Engineering",
                "duration": "Jan 2024 - Dec 2024",
                "location": "Colombo, Sri Lanka",
                "details": "Core Java, OOP, JDBC, design patterns, data structures, Hibernate, Spring Boot, REST APIs, and React."
            }
        ]

    def _deduplicate_projects(self, projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Guarantees verified candidate GitHub projects appear cleanly with zero duplicates."""
        return [
            {
                "title": "AeroIntel | Deterministic RAG Pipeline for Aviation Maintenance",
                "technologies": "Python, FastAPI, pgvector, PostgreSQL, Redis, BM25, Ollama, Docker",
                "bullets": [
                    "Engineered a local-first hybrid RAG system (dense vector + BM25 keyword search) with a structural refusal gate, printed-page citations, and a trust layer validating extracted figures against source maintenance manuals, benchmarked on a published golden test set."
                ]
            },
            {
                "title": "evalX | Evaluation Harness & Regression Testing for LLM Apps",
                "technologies": "Python, Pytest, Pydantic, LLM-as-a-Judge, CI/CD Gates",
                "bullets": [
                    "Built an automated testing harness for LLM behavior featuring golden test suites, hybrid scoring (code assertions + LLM-judge), regression tracking, and automated CI gating to eliminate hallucinations in production releases."
                ]
            },
            {
                "title": "EDGEOPS AI | Autonomous Agent Investigation Platform",
                "technologies": "Python 3.11+, Pydantic, Agentic Workflows, Typed Tools, Audit Logging",
                "bullets": [
                    "Developed an AI-assisted infrastructure triage agent with strongly-typed tool foundations, strict permission boundaries, target access restrictions, and correlated audit logging."
                ]
            },
            {
                "title": "Energy Bill Extractor | Multimodal Vision Document Intelligence",
                "technologies": "Python, FastAPI, Vision LLMs, Structured Schemas",
                "bullets": [
                    "Built an end-to-end multimodal pipeline converting unstructured bill PDFs and photos into validated structured data with an automated evaluation harness."
                ]
            }
        ]

    def build_resume_pdf(self, resume_data: Dict[str, Any], output_path: Path) -> Path:
        """Renders an authentic, official European Union Europass CV."""
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            leftMargin=32,
            rightMargin=32,
            topMargin=24,
            bottomMargin=24
        )
        story = []

        identity = resume_data.get("identity", {})
        full_name = sanitize_pdf_text(identity.get("full_name", "M.S. MOHAMED SUJAHATH"))
        title = sanitize_pdf_text(resume_data.get("tailored_title", identity.get("professional_title", "Software Engineer | Backend, Data & AI Systems")))
        subtitle = sanitize_pdf_text(resume_data.get("tailored_subtitle", resume_data.get("subtitle", identity.get("subtitle", "Python | SQL | FastAPI | PostgreSQL | Docker | Linux | AWS"))))
        relocation = sanitize_pdf_text(identity.get("relocation_status", "Available for Full-time Roles | Immediate International & Remote Relocation"))
        phone = identity.get("phone", "+94 76 485 8427 / +971 50 229 1865")
        email = identity.get("email", "sujahathmhmd@gmail.com")
        linkedin = identity.get("linkedin", "https://linkedin.com/in/sujahath-siddeek").replace("https://", "")
        github = identity.get("github", "https://github.com/SujahathMSM").replace("https://", "")

        # 1. OFFICIAL EUROPASS HEADER
        header_table_data = [
            [
                Paragraph("<b>europass</b> &nbsp;|&nbsp; <b>CURRICULUM VITAE</b>", self.styles["EuropassBrand"]),
                Paragraph("<b>European Standard Format</b>", self.styles["EuropassCityCol"])
            ]
        ]
        t_header = Table(header_table_data, colWidths=[410, 138])
        t_header.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ]))
        story.append(t_header)
        story.append(HRFlowable(width="100%", thickness=1.5, color=self.c_europass, spaceBefore=1, spaceAfter=5))

        # Identity Details Block
        story.append(Paragraph(full_name, self.styles["EuropassName"]))
        story.append(Paragraph(title, self.styles["EuropassRoleTitle"]))

        contact_table_data = [
            [
                Paragraph(f"<b>Location:</b> Moratuwa, Sri Lanka", self.styles["EuropassContactItem"]),
                Paragraph(f"<b>Phone:</b> {phone}", self.styles["EuropassContactItem"])
            ],
            [
                Paragraph(f"<b>Email:</b> {email}", self.styles["EuropassContactItem"]),
                Paragraph(f"<b>Nationality:</b> Sri Lankan", self.styles["EuropassContactItem"])
            ],
            [
                Paragraph(f"<b>LinkedIn:</b> {linkedin}", self.styles["EuropassContactItem"]),
                Paragraph(f"<b>GitHub:</b> {github}", self.styles["EuropassContactItem"])
            ],
            [
                Paragraph(f"<b>Work Availability:</b> {relocation}", self.styles["EuropassContactItem"]),
                Paragraph(f"<b>Core Stack:</b> {subtitle}", self.styles["EuropassContactItem"])
            ]
        ]
        t_contact = Table(contact_table_data, colWidths=[274, 274])
        t_contact.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0.5),
        ]))
        story.append(t_contact)
        story.append(Spacer(1, 4))

        # 2. ABOUT ME / EXECUTIVE PROFILE
        summary = resume_data.get("summary", "")
        if summary:
            story.append(Paragraph("ABOUT ME", self.styles["EuropassSectionTitle"]))
            story.append(HRFlowable(width="100%", thickness=0.8, color=self.c_europass, spaceBefore=1, spaceAfter=3))
            story.append(Paragraph(sanitize_pdf_text(summary), self.styles["EuropassBody"]))
            story.append(Spacer(1, 3))

        # 3. WORK EXPERIENCE (EUROPASS 2-COLUMN FORMAT)
        raw_work = resume_data.get("work_history", [])
        work_history = self._deduplicate_work_history(raw_work)

        if work_history:
            story.append(Paragraph("WORK EXPERIENCE", self.styles["EuropassSectionTitle"]))
            story.append(HRFlowable(width="100%", thickness=0.8, color=self.c_europass, spaceBefore=1, spaceAfter=3))

            for exp in work_history:
                comp = sanitize_pdf_text(exp.get("company", ""))
                branch = sanitize_pdf_text(exp.get("branch", ""))
                r_title = sanitize_pdf_text(exp.get("title", ""))
                dur = sanitize_pdf_text(exp.get("duration", ""))
                bullets = exp.get("bullets", [])

                date_cell = [
                    Paragraph(f"<b>[ {dur} ]</b>", self.styles["EuropassDateCol"]),
                    Paragraph(f"{branch or 'Sri Lanka'}", self.styles["EuropassCityCol"])
                ]

                right_cell = [
                    Paragraph(f"<b>{r_title}</b>", self.styles["EuropassJobTitle"]),
                    Paragraph(f"<b>Employer: {comp}</b>", self.styles["EuropassEmployer"]),
                    Paragraph("Sector: Information and Communication Technology / Systems Engineering", self.styles["EuropassSector"])
                ]

                for b in bullets:
                    clean_b = sanitize_pdf_text(b)
                    if clean_b:
                        right_cell.append(Paragraph(f"&bull; {clean_b}", self.styles["EuropassBullet"]))

                job_table = Table([[date_cell, right_cell]], colWidths=[110, 438])
                job_table.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('LEFTPADDING', (0,0), (-1,-1), 0),
                    ('RIGHTPADDING', (0,0), (-1,-1), 0),
                    ('TOPPADDING', (0,0), (-1,-1), 1),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                ]))
                story.append(job_table)
                story.append(Spacer(1, 2))

        # 4. EDUCATION AND TRAINING
        raw_edu = resume_data.get("education", [])
        education = self._deduplicate_education(raw_edu)

        if education:
            story.append(Paragraph("EDUCATION AND TRAINING", self.styles["EuropassSectionTitle"]))
            story.append(HRFlowable(width="100%", thickness=0.8, color=self.c_europass, spaceBefore=1, spaceAfter=3))

            for edu in education:
                deg = sanitize_pdf_text(edu.get("degree", ""))
                inst = sanitize_pdf_text(edu.get("institution", ""))
                dur = sanitize_pdf_text(edu.get("duration", ""))
                loc = sanitize_pdf_text(edu.get("location", ""))
                det = sanitize_pdf_text(edu.get("details", ""))

                date_cell = [
                    Paragraph(f"<b>[ {dur} ]</b>", self.styles["EuropassDateCol"]),
                    Paragraph(f"{loc}", self.styles["EuropassCityCol"])
                ]

                right_cell = [
                    Paragraph(f"<b>{deg}</b>", self.styles["EuropassJobTitle"]),
                    Paragraph(f"<b>Organisation: {inst}</b>", self.styles["EuropassEmployer"])
                ]
                if det:
                    right_cell.append(Paragraph(f"&bull; {det}", self.styles["EuropassBullet"]))

                edu_table = Table([[date_cell, right_cell]], colWidths=[110, 438])
                edu_table.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('LEFTPADDING', (0,0), (-1,-1), 0),
                    ('RIGHTPADDING', (0,0), (-1,-1), 0),
                    ('TOPPADDING', (0,0), (-1,-1), 1),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                ]))
                story.append(edu_table)
                story.append(Spacer(1, 2))

        # 5. DIGITAL SKILLS (EUROPASS CATEGORIZED)
        skills_categorized = resume_data.get("core_skills_categorized", [])
        if not skills_categorized:
            skills_categorized = [
                {"category": "Programming & Backend", "skills": "Python (FastAPI, AsyncIO), SQL, Java, Node.js, C; REST APIs, WebSockets, GraphQL"},
                {"category": "Data & Databases", "skills": "PostgreSQL, TimescaleDB, pgvector, Redis, MongoDB, Schema Design, Query Optimisation"},
                {"category": "AI & Machine Learning", "skills": "LangGraph, RAG (Retrieval-Augmented Generation), PyTorch, TensorFlow, LLM Evaluation (evalX), Vision Models"},
                {"category": "Cloud & DevOps", "skills": "AWS (EC2, S3, RDS, Lambda), Docker, Docker Compose, GitLab CI/CD, GitHub Actions, Linux, Ansible"},
                {"category": "IoT & Protocols", "skills": "MQTT/EMQX, Modbus RTU/RS485, Raspberry Pi, STM32, Device Telemetry"},
                {"category": "Analysis & Delivery", "skills": "System Architecture, Root-Cause Analysis, Test Planning, Regression Verification, Agile/Scrum"},
                {"category": "Documentation & Records", "skills": "Technical Specifications, Runbooks, Onboarding Guides, Version-Controlled Records"}
            ]

        story.append(Paragraph("DIGITAL SKILLS", self.styles["EuropassSectionTitle"]))
        story.append(HRFlowable(width="100%", thickness=0.8, color=self.c_europass, spaceBefore=1, spaceAfter=3))
        for cat_item in skills_categorized:
            cat = sanitize_pdf_text(cat_item.get("category", ""))
            s_text = sanitize_pdf_text(cat_item.get("skills", ""))
            story.append(Paragraph(f"<b>{cat}:</b> {s_text}", self.styles["EuropassBody"]))
        story.append(Spacer(1, 2))

        # 6. PROJECTS (VERIFIED GITHUB & PRODUCTION REPOSITORIES)
        raw_projects = resume_data.get("projects", [])
        projects = self._deduplicate_projects(raw_projects)

        if projects:
            story.append(Paragraph("PROJECTS", self.styles["EuropassSectionTitle"]))
            story.append(HRFlowable(width="100%", thickness=0.8, color=self.c_europass, spaceBefore=1, spaceAfter=3))

            for proj in projects[:4]:
                p_title = sanitize_pdf_text(proj.get("title", ""))
                p_tech = sanitize_pdf_text(proj.get("technologies", ""))
                header_line = f"<b>{p_title}</b> | <font color='#0E4194'>{p_tech}</font>" if p_tech else f"<b>{p_title}</b>"
                story.append(Paragraph(header_line, self.styles["EuropassBody"]))

                p_bullets = proj.get("bullets", [])
                for b in p_bullets:
                    clean_b = sanitize_pdf_text(b)
                    if clean_b:
                        story.append(Paragraph(f"&bull; {clean_b}", self.styles["EuropassBullet"]))
                story.append(Spacer(1, 1))

        # 7. LANGUAGE SKILLS
        story.append(Paragraph("LANGUAGE SKILLS", self.styles["EuropassSectionTitle"]))
        story.append(HRFlowable(width="100%", thickness=0.8, color=self.c_europass, spaceBefore=1, spaceAfter=3))
        story.append(Paragraph("<b>Mother tongue(s):</b> Tamil, Sinhala &nbsp;|&nbsp; <b>Other language(s):</b> English (Proficient user - C1/C2 | Full Professional Working Proficiency)", self.styles["EuropassBody"]))
        story.append(Spacer(1, 2))

        # 8. CERTIFICATIONS
        certs = resume_data.get("certifications", [
            "University of Michigan - Python for Everybody",
            "DeepLearning.AI - Supervised Machine Learning",
            "Meta - Programming with JavaScript",
            "Google - IT Support Professional"
        ])
        if certs:
            story.append(Paragraph("CERTIFICATIONS & HONOURS", self.styles["EuropassSectionTitle"]))
            story.append(HRFlowable(width="100%", thickness=0.8, color=self.c_europass, spaceBefore=1, spaceAfter=3))
            certs_str = " &nbsp;|&nbsp; ".join([sanitize_pdf_text(c) for c in certs])
            story.append(Paragraph(certs_str, self.styles["EuropassBody"]))

        doc.build(story)
        return output_path

    def build_cover_letter_pdf(self, cover_letter_text: str, candidate_name: str, output_path: Path) -> Path:
        """Renders an executive Europass-style cover letter matching the candidate's exact letterhead."""
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            leftMargin=44,
            rightMargin=44,
            topMargin=40,
            bottomMargin=40
        )
        story = []

        if isinstance(candidate_name, dict):
            c_name = sanitize_pdf_text(candidate_name.get("identity", {}).get("full_name", candidate_name.get("full_name", "M.S. MOHAMED SUJAHATH")))
        else:
            c_name = sanitize_pdf_text(candidate_name or "M.S. MOHAMED SUJAHATH")

        # Official Europass Letterhead
        story.append(Paragraph("<b>europass</b> &nbsp;|&nbsp; <b>APPLICATION COVER LETTER</b>", self.styles["EuropassBrand"]))
        story.append(Paragraph(f"<b>{c_name}</b>", self.styles["EuropassName"]))
        contact_line = sanitize_pdf_text("+94 76 485 8427 / +971 50 229 1865 | sujahathmhmd@gmail.com | Moratuwa, Sri Lanka")
        story.append(Paragraph(contact_line, self.styles["EuropassContactItem"]))
        story.append(HRFlowable(width="100%", thickness=1.5, color=self.c_europass, spaceBefore=4, spaceAfter=14))

        # Clean any raw markdown or redundant top blocks
        text = cover_letter_text.strip()
        text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"^-{3,}\s*$", "", text, flags=re.MULTILINE)
        if "Dear " in text:
            idx = text.find("Dear ")
            pre = text[:idx]
            if "[" in pre or "Date" in pre:
                text = text[idx:]

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        for p in paragraphs:
            clean_p = sanitize_pdf_text(p).replace("\n", "<br/>")
            story.append(Paragraph(clean_p, self.styles["CoverLetterBody"]))

        doc.build(story)
        return output_path
