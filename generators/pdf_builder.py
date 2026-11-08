import re
import unicodedata
from pathlib import Path
from typing import Dict, Any, List
from reportlab.lib.pagesizes import A4, letter
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

    def _default_canonical_work_history(self) -> List[Dict[str, Any]]:
        return []

    def _default_canonical_education(self) -> List[Dict[str, Any]]:
        return []

    def _default_canonical_projects(self) -> List[Dict[str, Any]]:
        return []

    def _deduplicate_work_history(self, work_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Cleans and deduplicates work history while preserving tailored bullets from LLM / Persona."""
        if not work_history:
            return self._default_canonical_work_history()

        deduped = []
        seen = set()

        for exp in work_history:
            comp = exp.get("company", "").strip()
            title = exp.get("title", "").strip()
            branch = exp.get("branch", "").strip()
            dur = exp.get("duration", "").strip()
            raw_bullets = exp.get("bullets", [])

            if not comp and not title:
                continue

            norm_key = f"{comp.lower()}_{title.lower()}"
            if norm_key in seen:
                continue
            seen.add(norm_key)

            clean_bullets = []
            for b in raw_bullets:
                clean_b = re.sub(r"^[•\-*■\s]+", "", str(b)).strip()
                sub_parts = re.split(r"[■•]", clean_b)
                for sp in sub_parts:
                    sp_text = sp.strip(" -–|:•■")
                    if len(sp_text) > 18 and not any(sp_text.lower() == existing.lower() for existing in clean_bullets):
                        clean_bullets.append(sp_text)

            deduped.append({
                "company": comp,
                "branch": branch,
                "title": title,
                "duration": dur,
                "bullets": clean_bullets
            })

        return deduped if deduped else self._default_canonical_work_history()

    def _deduplicate_education(self, education: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Cleans and deduplicates education entries while preserving structured data."""
        if not education:
            return self._default_canonical_education()

        deduped = []
        seen = set()

        for edu in education:
            deg = edu.get("degree", "").strip()
            inst = edu.get("institution", "").strip()
            dur = edu.get("duration", "").strip()
            loc = edu.get("location", "").strip()
            det = edu.get("details", "").strip()

            if not deg and not inst:
                continue

            norm_key = f"{deg.lower()}_{inst.lower()}"
            if norm_key in seen:
                continue
            seen.add(norm_key)

            deduped.append({
                "degree": deg,
                "institution": inst,
                "duration": dur,
                "location": loc,
                "details": det
            })

        return deduped if deduped else self._default_canonical_education()

    def _deduplicate_projects(self, projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Preserves tailored / selected projects while eliminating duplicates and artifacts."""
        if not projects:
            return self._default_canonical_projects()

        deduped = []
        seen = set()

        for proj in projects:
            title = proj.get("title", "").strip()
            tech = proj.get("technologies", "")
            bullets = proj.get("bullets", [])

            if not title:
                continue

            norm_key = title.lower()[:30]
            if norm_key in seen:
                continue
            seen.add(norm_key)

            clean_bullets = []
            for b in bullets:
                clean_b = re.sub(r"^[•\-*■\s]+", "", str(b)).strip()
                if len(clean_b) > 15:
                    clean_bullets.append(clean_b)

            deduped.append({
                "title": title,
                "technologies": ", ".join(tech) if isinstance(tech, list) else str(tech),
                "bullets": clean_bullets
            })

        return deduped[:4] if deduped else self._default_canonical_projects()

    def build_resume_pdf(self, resume_data: Dict[str, Any], output_path: Path) -> Path:
        """Renders an authentic, official European Union Europass CV in standard A4 format."""
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=30,
            rightMargin=30,
            topMargin=22,
            bottomMargin=22
        )
        story = []

        identity = resume_data.get("identity", {})
        full_name = sanitize_pdf_text(identity.get("full_name", "Candidate"))
        title = sanitize_pdf_text(resume_data.get("tailored_title", identity.get("professional_title", "Software Engineer | Backend, Data & AI Systems")))
        subtitle = sanitize_pdf_text(resume_data.get("tailored_subtitle", resume_data.get("subtitle", identity.get("subtitle", "Python | SQL | FastAPI | PostgreSQL | Docker | Linux | AWS"))))
        relocation = sanitize_pdf_text(identity.get("relocation_status", "Available for Full-time Roles | Immediate International & Remote Relocation"))
        phone = identity.get("phone", "")
        email = identity.get("email", "")
        linkedin = identity.get("linkedin", "").replace("https://", "")
        github = identity.get("github", "").replace("https://", "")
        location_str = identity.get("current_location", "Global / Remote")

        # 1. OFFICIAL EUROPASS HEADER
        header_table_data = [
            [
                Paragraph("<b>europass</b> &nbsp;|&nbsp; <b>CURRICULUM VITAE</b>", self.styles["EuropassBrand"]),
                Paragraph("<b>European Standard Format</b>", self.styles["EuropassCityCol"])
            ]
        ]
        t_header = Table(header_table_data, colWidths=[395, 140])
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
                Paragraph(f"<b>Location:</b> {location_str}", self.styles["EuropassContactItem"]),
                Paragraph(f"<b>Phone:</b> {phone}", self.styles["EuropassContactItem"])
            ],
            [
                Paragraph(f"<b>Email:</b> {email}", self.styles["EuropassContactItem"]),
                Paragraph(f"<b>Nationality:</b> {identity.get('nationality', 'Sri Lankan')}", self.styles["EuropassContactItem"])
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
        t_contact = Table(contact_table_data, colWidths=[267, 268])
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
        summary = resume_data.get("summary", "") or resume_data.get("tailored_summary", "")
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

                job_table = Table([[date_cell, right_cell]], colWidths=[105, 430])
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

                edu_table = Table([[date_cell, right_cell]], colWidths=[105, 430])
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

    def build_ats_clean_pdf(self, resume_data: Dict[str, Any], output_path: Path) -> Path:
        """Renders a pure, 100% ATS-compliant single-column text-layer PDF (LaTeX / Typst style).
        Strictly avoids non-standard tables or graphics to guarantee 100% parsing on Workday,
        Greenhouse, Taleo, and Lever."""
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=32,
            bottomMargin=32
        )
        story = []

        ident = resume_data.get("identity", {})
        c_name = sanitize_pdf_text(ident.get("full_name", "Candidate"))
        title = sanitize_pdf_text(resume_data.get("tailored_title", "Software Engineer"))
        
        c_phone = ident.get("phone", "")
        c_email = ident.get("email", "")
        c_loc = ident.get("current_location", "Global / Remote")
        c_li = ident.get("linkedin", "")
        c_gh = ident.get("github", "")

        # ATS Styles
        ats_name_style = ParagraphStyle(
            name="ATSName",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=19,
            textColor=colors.HexColor("#111827"),
            alignment=1,
            spaceAfter=2
        )
        ats_title_style = ParagraphStyle(
            name="ATSTitle",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#2563EB"),
            alignment=1,
            spaceAfter=4
        )
        ats_contact_style = ParagraphStyle(
            name="ATSContact",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#4B5563"),
            alignment=1,
            spaceAfter=8
        )
        ats_h1_style = ParagraphStyle(
            name="ATSH1",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#111827"),
            spaceBefore=8,
            spaceAfter=2,
            keepWithNext=True
        )
        ats_body_style = ParagraphStyle(
            name="ATSBody",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#1F2937"),
            spaceAfter=4
        )
        ats_bullet_style = ParagraphStyle(
            name="ATSBullet",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            leftIndent=12,
            firstLineIndent=-8,
            textColor=colors.HexColor("#1F2937"),
            spaceAfter=2
        )

        # Header Block
        story.append(Paragraph(f"<b>{c_name.upper()}</b>", ats_name_style))
        story.append(Paragraph(f"<b>{title.upper()}</b>", ats_title_style))
        contact_str = f"{c_email} | {c_phone} | {c_loc} | {c_li} | {c_gh}"
        story.append(Paragraph(sanitize_pdf_text(contact_str), ats_contact_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#111827"), spaceBefore=1, spaceAfter=6))

        # 1. PROFESSIONAL SUMMARY
        summary = resume_data.get("summary") or resume_data.get("tailored_summary", "")
        if summary:
            story.append(Paragraph("<b>PROFESSIONAL SUMMARY</b>", ats_h1_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#9CA3AF"), spaceBefore=1, spaceAfter=4))
            story.append(Paragraph(sanitize_pdf_text(summary), ats_body_style))

        # 2. CORE TECHNICAL SKILLS
        skills_cat = resume_data.get("core_skills_categorized", [])
        if skills_cat:
            story.append(Paragraph("<b>CORE TECHNICAL COMPETENCIES</b>", ats_h1_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#9CA3AF"), spaceBefore=1, spaceAfter=4))
            for cat in skills_cat:
                c_name_cat = sanitize_pdf_text(cat.get("category", "Technical"))
                c_skills = sanitize_pdf_text(cat.get("skills", ""))
                story.append(Paragraph(f"&bull; <b>{c_name_cat}:</b> {c_skills}", ats_bullet_style))

        # 3. WORK EXPERIENCE
        work_hist = resume_data.get("work_history", [])
        if work_hist:
            story.append(Paragraph("<b>PROFESSIONAL WORK EXPERIENCE</b>", ats_h1_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#9CA3AF"), spaceBefore=1, spaceAfter=4))
            for job in work_hist:
                j_title = sanitize_pdf_text(job.get("title", ""))
                j_comp = sanitize_pdf_text(job.get("company", ""))
                j_dur = sanitize_pdf_text(job.get("duration", ""))
                story.append(Paragraph(f"<b>{j_title}</b> &mdash; <i>{j_comp}</i> ({j_dur})", ats_body_style))
                for b in job.get("bullets", []):
                    clean_b = sanitize_pdf_text(b)
                    if clean_b:
                        story.append(Paragraph(f"&bull; {clean_b}", ats_bullet_style))
                story.append(Spacer(1, 2))

        # 4. KEY TECHNICAL PROJECTS
        projects = resume_data.get("projects", [])
        if projects:
            story.append(Paragraph("<b>KEY TECHNICAL &amp; PRODUCTION PROJECTS</b>", ats_h1_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#9CA3AF"), spaceBefore=1, spaceAfter=4))
            for proj in projects[:4]:
                p_title = sanitize_pdf_text(proj.get("title", ""))
                p_tech = sanitize_pdf_text(proj.get("technologies", ""))
                p_header = f"<b>{p_title}</b> &mdash; <i>Tech: {p_tech}</i>" if p_tech else f"<b>{p_title}</b>"
                story.append(Paragraph(p_header, ats_body_style))
                for b in proj.get("bullets", []):
                    clean_b = sanitize_pdf_text(b)
                    if clean_b:
                        story.append(Paragraph(f"&bull; {clean_b}", ats_bullet_style))
                story.append(Spacer(1, 2))

        # 5. EDUCATION
        education = resume_data.get("education", [])
        if education:
            story.append(Paragraph("<b>EDUCATION &amp; ACADEMIC CREDENTIALS</b>", ats_h1_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#9CA3AF"), spaceBefore=1, spaceAfter=4))
            for edu in education:
                e_deg = sanitize_pdf_text(edu.get("degree", ""))
                e_inst = sanitize_pdf_text(edu.get("institution", ""))
                e_dur = sanitize_pdf_text(edu.get("duration", ""))
                if e_deg:
                    story.append(Paragraph(f"<b>{e_deg}</b>", ats_body_style))
                if e_inst:
                    inst_line = f"{e_inst} ({e_dur})" if e_dur else e_inst
                    story.append(Paragraph(inst_line, ats_body_style))

        doc.build(story)
        return output_path

    def generate_ats_plaintext(self, resume_data: Dict[str, Any]) -> str:
        """Generates pure plaintext formatted specifically for ATS text input boxes."""
        ident = resume_data.get("identity", {})
        c_name = ident.get("full_name", "Candidate")
        title = resume_data.get("tailored_title", "Software Engineer")
        c_phone = ident.get("phone", "")
        c_email = ident.get("email", "")
        c_loc = ident.get("current_location", "Global / Remote")
        c_li = ident.get("linkedin", "")
        c_gh = ident.get("github", "")

        lines = [
            f"{c_name.upper()}",
            f"{title}",
            f"Email: {c_email} | Phone: {c_phone} | Location: {c_loc}",
            f"LinkedIn: {c_li} | GitHub: {c_gh}",
            "=" * 70,
            "",
            "PROFESSIONAL SUMMARY",
            "-" * 40,
            resume_data.get("summary") or resume_data.get("tailored_summary", ""),
            "",
            "TECHNICAL COMPETENCIES",
            "-" * 40,
        ]

        for cat in resume_data.get("core_skills_categorized", []):
            lines.append(f"* {cat.get('category', 'Technical')}: {cat.get('skills', '')}")

        lines.extend(["", "PROFESSIONAL EXPERIENCE", "-" * 40])
        for job in resume_data.get("work_history", []):
            lines.append(f"\n{job.get('title', '')} - {job.get('company', '')} ({job.get('duration', '')})")
            for b in job.get("bullets", []):
                lines.append(f"  * {b}")

        lines.extend(["", "KEY TECHNICAL PROJECTS", "-" * 40])
        for proj in resume_data.get("projects", []):
            lines.append(f"\n{proj.get('title', '')} | Tech: {proj.get('technologies', '')}")
            for b in proj.get("bullets", []):
                lines.append(f"  * {b}")

        lines.extend(["", "EDUCATION", "-" * 40])
        for edu in resume_data.get("education", []):
            lines.append(f"{edu.get('degree', '')}")
            if edu.get("institution"):
                lines.append(f"{edu.get('institution', '')} ({edu.get('duration', '')})".strip())

        return "\n".join(lines)

    def build_cover_letter_pdf(self, cover_letter_text: str, candidate_name: Any, output_path: Path) -> Path:
        """Renders an executive Europass-style cover letter in A4 format."""
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=40,
            rightMargin=40,
            topMargin=36,
            bottomMargin=36
        )
        story = []

        phone = ""
        email = ""
        location = ""
        if isinstance(candidate_name, dict):
            ident = candidate_name.get("identity", candidate_name)
            c_name = sanitize_pdf_text(ident.get("full_name", "Candidate"))
            phone = ident.get("phone", "")
            email = ident.get("email", "")
            location = ident.get("current_location", "Global / Remote")
        else:
            c_name = sanitize_pdf_text(str(candidate_name or "Candidate"))

        # Official Europass Letterhead
        story.append(Paragraph("<b>europass</b> &nbsp;|&nbsp; <b>APPLICATION COVER LETTER</b>", self.styles["EuropassBrand"]))
        story.append(Paragraph(f"<b>{c_name}</b>", self.styles["EuropassName"]))

        contact_parts = [p for p in [phone, email, location] if p]
        contact_line = sanitize_pdf_text(" | ".join(contact_parts)) if contact_parts else "Immediate International & Remote Relocation"
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
