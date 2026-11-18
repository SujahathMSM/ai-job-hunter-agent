import html
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

    # ReportLab parses text as XML-like markup: a raw "&" or "<" garbles output ("R&D" -> "R&D;")
    text = html.escape(text, quote=False)

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

    def _section(self, story: list, title: str, first_block: list) -> None:
        """Section heading kept on the same page as the section's first entry (no stranded headings)."""
        story.append(KeepTogether([
            Paragraph(title, self.styles["EuropassSectionTitle"]),
            HRFlowable(width="100%", thickness=0.8, color=self.c_europass, spaceBefore=1, spaceAfter=3),
            *first_block,
        ]))

    def _two_col(self, dates: str, place: str, right_cell: list) -> list:
        left = [Paragraph(f"<b>{sanitize_pdf_text(dates)}</b>", self.styles["EuropassDateCol"])]
        if place:
            left.append(Paragraph(sanitize_pdf_text(place), self.styles["EuropassCityCol"]))
        table = Table([[left, right_cell]], colWidths=[105, 430])
        table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        return [table, Spacer(1, 2)]

    @staticmethod
    def _clean_skill_groups(groups: List[Any], project_titles: List[str]) -> List[tuple]:
        """De-duplicate skills across groups, drop project names listed as skills, and fold
        one-item groups into a final 'Other' line so the section doesn't fragment."""
        project_keys = {re.sub(r"[^a-z0-9]", "", t.split("|")[0].lower()) for t in project_titles if t}
        seen, cleaned, leftovers = set(), [], []
        for g in groups or []:
            if not isinstance(g, dict):
                continue
            raw = g.get("skills", "")
            items = raw if isinstance(raw, list) else re.split(r",(?![^()]*\))", str(raw))
            kept = []
            for item in (str(x).strip() for x in items):
                key = re.sub(r"[^a-z0-9]", "", item.lower())
                base = re.sub(r"[^a-z0-9]", "", item.split("(")[0].lower())
                if not item or key in seen or base in project_keys:
                    continue
                seen.add(key)
                kept.append(item)
            if len(kept) >= 2:
                cleaned.append((str(g.get("category", "")).strip() or "Skills", kept))
            else:
                leftovers.extend(kept)
        if leftovers:
            cleaned.append(("Other", leftovers))
        return cleaned

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

        identity = resume_data.get("identity", {}) or {}
        full_name = sanitize_pdf_text(identity.get("full_name") or "Candidate")
        # Headline is the candidate's own title, never the target job's title
        title = sanitize_pdf_text(identity.get("professional_title") or resume_data.get("tailored_title") or "")
        # Raw values here; each is sanitized exactly once when its cell is built
        subtitle = resume_data.get("tailored_subtitle") or resume_data.get("subtitle") or identity.get("subtitle") or ""
        relocation = identity.get("relocation_status") or ""
        linkedin = (identity.get("linkedin") or "").replace("https://", "").replace("http://", "").rstrip("/")
        github = (identity.get("github") or "").replace("https://", "").replace("http://", "").rstrip("/")

        # 1. HEADER
        story.append(Paragraph("<b>CURRICULUM VITAE</b>", self.styles["EuropassBrand"]))
        story.append(HRFlowable(width="100%", thickness=1.5, color=self.c_europass, spaceBefore=1, spaceAfter=5))
        story.append(Paragraph(full_name, self.styles["EuropassName"]))
        if title:
            story.append(Paragraph(title, self.styles["EuropassRoleTitle"]))

        contacts = [
            ("Location", identity.get("current_location")), ("Phone", identity.get("phone")),
            ("Email", identity.get("email")), ("Nationality", identity.get("nationality")),
            ("LinkedIn", linkedin), ("GitHub", github),
            ("Availability", relocation), ("Core Stack", subtitle),
        ]
        cells = [Paragraph(f"<b>{label}:</b> {sanitize_pdf_text(value)}", self.styles["EuropassContactItem"])
                 for label, value in contacts if value and str(value).strip()]
        if cells:
            rows = [cells[i:i + 2] + [""] * (2 - len(cells[i:i + 2])) for i in range(0, len(cells), 2)]
            t_contact = Table(rows, colWidths=[267, 268])
            t_contact.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 0.5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0.5),
            ]))
            story.append(t_contact)
        story.append(Spacer(1, 4))

        # 2. PROFILE
        summary = resume_data.get("summary", "") or resume_data.get("tailored_summary", "")
        if summary:
            self._section(story, "PROFILE", [Paragraph(sanitize_pdf_text(summary), self.styles["EuropassBody"]), Spacer(1, 3)])

        # 3. WORK EXPERIENCE (two columns: dates/place | role, employer, bullets)
        work_history = self._deduplicate_work_history(resume_data.get("work_history", []))
        for i, exp in enumerate(work_history):
            right_cell = [
                Paragraph(f"<b>{sanitize_pdf_text(exp.get('title', ''))}</b>", self.styles["EuropassJobTitle"]),
                Paragraph(f"<b>{sanitize_pdf_text(exp.get('company', ''))}</b>", self.styles["EuropassEmployer"]),
            ]
            if exp.get("sector"):
                right_cell.append(Paragraph(sanitize_pdf_text(exp["sector"]), self.styles["EuropassSector"]))
            for b in exp.get("bullets", []):
                clean_b = sanitize_pdf_text(b)
                if clean_b:
                    right_cell.append(Paragraph(f"&bull; {clean_b}", self.styles["EuropassBullet"]))
            block = self._two_col(exp.get("duration", ""), exp.get("location") or exp.get("branch") or "", right_cell)
            if i == 0:
                self._section(story, "WORK EXPERIENCE", block)
            else:
                story.extend(block)

        # 4. EDUCATION AND TRAINING
        education = self._deduplicate_education(resume_data.get("education", []))
        for i, edu in enumerate(education):
            right_cell = [
                Paragraph(f"<b>{sanitize_pdf_text(edu.get('degree', ''))}</b>", self.styles["EuropassJobTitle"]),
                Paragraph(f"<b>{sanitize_pdf_text(edu.get('institution', ''))}</b>", self.styles["EuropassEmployer"]),
            ]
            det = sanitize_pdf_text(edu.get("details", ""))
            if det:
                right_cell.append(Paragraph(f"&bull; {det}", self.styles["EuropassBullet"]))
            block = self._two_col(edu.get("duration", ""), edu.get("location", ""), right_cell)
            if i == 0:
                self._section(story, "EDUCATION AND TRAINING", block)
            else:
                story.extend(block)

        # 5. SKILLS
        projects = self._deduplicate_projects(resume_data.get("projects", []))
        skill_groups = self._clean_skill_groups(
            resume_data.get("core_skills_categorized", []),
            [p.get("title", "") for p in projects],
        )
        if skill_groups:
            lines = [Paragraph(f"<b>{sanitize_pdf_text(cat)}:</b> {sanitize_pdf_text(', '.join(items))}", self.styles["EuropassBody"])
                     for cat, items in skill_groups]
            self._section(story, "SKILLS", lines[:2])
            story.extend(lines[2:])
            story.append(Spacer(1, 2))

        # 6. PROJECTS
        for i, proj in enumerate(projects[:4]):
            p_title = sanitize_pdf_text(proj.get("title", ""))
            p_tech = sanitize_pdf_text(proj.get("technologies", ""))
            block = [Paragraph(f"<b>{p_title}</b> | <font color='#0E4194'>{p_tech}</font>" if p_tech else f"<b>{p_title}</b>",
                               self.styles["EuropassBody"])]
            for b in proj.get("bullets", []):
                clean_b = sanitize_pdf_text(b)
                if clean_b:
                    block.append(Paragraph(f"&bull; {clean_b}", self.styles["EuropassBullet"]))
            block.append(Spacer(1, 1))
            if i == 0:
                self._section(story, "PROJECTS", block)
            else:
                story.append(KeepTogether(block))

        # 7. LANGUAGES (from the profile; omitted if none are listed)
        languages = resume_data.get("languages") or identity.get("languages")
        if languages:
            text = languages if isinstance(languages, str) else ", ".join(str(x) for x in languages)
            self._section(story, "LANGUAGES", [Paragraph(sanitize_pdf_text(text), self.styles["EuropassBody"]), Spacer(1, 2)])

        # 8. CERTIFICATIONS (from the profile only)
        certs = [sanitize_pdf_text(c if isinstance(c, str) else c.get("name", "")) for c in (resume_data.get("certifications") or [])]
        certs = [c for c in certs if c]
        if certs:
            self._section(story, "CERTIFICATIONS", [Paragraph(" &nbsp;|&nbsp; ".join(certs), self.styles["EuropassBody"])])

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
        title = sanitize_pdf_text(ident.get("professional_title") or resume_data.get("tailored_title") or "")
        
        c_phone = ident.get("phone", "")
        c_email = ident.get("email", "")
        c_loc = ident.get("current_location", "")
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
        if title:
            story.append(Paragraph(f"<b>{title.upper()}</b>", ats_title_style))
        contact_str = " | ".join(v for v in (c_email, c_phone, c_loc, c_li, c_gh) if v and str(v).strip())
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
        title = (resume_data.get("identity") or {}).get("professional_title") or resume_data.get("tailored_title") or ""
        c_phone = ident.get("phone", "")
        c_email = ident.get("email", "")
        c_loc = ident.get("current_location", "")
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
