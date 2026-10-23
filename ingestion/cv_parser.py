import re
from pathlib import Path
from typing import Dict, Any, List
import pypdf
import docx

class CVParser:
    """Parses CVs in PDF, DOCX, and TXT formats and extracts structured sections with high accuracy."""

    @staticmethod
    def extract_text_from_pdf(pdf_path: Path) -> str:
        text = ""
        try:
            reader = pypdf.PdfReader(str(pdf_path))
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except Exception as e:
            text = f"Error reading PDF: {e}"
        return text.strip()

    @staticmethod
    def extract_text_from_docx(docx_path: Path) -> str:
        text = ""
        try:
            doc = docx.Document(str(docx_path))
            for para in doc.paragraphs:
                if para.text.strip():
                    text += para.text + "\n"
            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_text:
                        text += " | ".join(row_text) + "\n"
        except Exception as e:
            text = f"Error reading DOCX: {e}"
        return text.strip()

    @staticmethod
    def extract_text_from_txt(txt_path: Path) -> str:
        try:
            with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read().strip()
        except Exception as e:
            return f"Error reading TXT: {e}"

    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            raw_text = self.extract_text_from_pdf(file_path)
        elif ext in [".docx", ".doc"]:
            raw_text = self.extract_text_from_docx(file_path)
        else:
            raw_text = self.extract_text_from_txt(file_path)

        # Normalize inline bullet characters and clean formatting
        raw_text = re.sub(r"[\u25a0\u25aa■\uf0b7]\s*", "\n• ", raw_text)
        raw_text = re.sub(r"\n{3,}", "\n\n", raw_text)

        extracted_name = self._extract_candidate_name(raw_text)
        contact_info = self._extract_contacts(raw_text)
        sections = self._segment_sections(raw_text)
        parsed_experience = self._parse_experience_items(sections.get("experience", ""))
        parsed_projects = self._parse_project_items(sections.get("projects", ""))
        parsed_education = self._parse_education_items(sections.get("education", ""))

        return {
            "source_file": file_path.name,
            "candidate_name": extracted_name,
            "raw_text": raw_text,
            "contact_info": contact_info,
            "sections": sections,
            "parsed_experience": parsed_experience,
            "parsed_projects": parsed_projects,
            "parsed_education": parsed_education
        }

    def _extract_candidate_name(self, text: str) -> str:
        """Finds candidate's real name from the very top lines of the document."""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines[:6]:
            # Skip noise or generic headers
            if any(kw in line.lower() for kw in ["contact", "curriculum", "resume", "page", "phone", "email", "http"]):
                continue
            # Candidate names are usually 2-5 words, alphabetic with possible initials
            clean = re.sub(r"[^a-zA-Z\s.]", "", line).strip()
            words = clean.split()
            if 2 <= len(words) <= 5 and not any(w.lower() in ["engineer", "developer", "summary", "skills"] for w in words):
                return clean
        return ""

    def _extract_contacts(self, text: str) -> Dict[str, str]:
        email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        phone_matches = re.findall(r"\+?[0-9]{1,4}[\s\-]?[0-9]{2,5}[\s\-]?[0-9]{3,5}[\s\-]?[0-9]{3,5}", text)
        linkedin_match = re.search(r"linkedin\.com/in/[a-zA-Z0-9_\-]+", text, re.IGNORECASE)
        github_match = re.search(r"github\.com/[a-zA-Z0-9_\-]+", text, re.IGNORECASE)

        phone = " / ".join(phone_matches[:2]) if phone_matches else ""

        return {
            "email": email_match.group(0) if email_match else "",
            "phone": phone,
            "linkedin": f"https://{linkedin_match.group(0)}" if linkedin_match else "",
            "github": f"https://{github_match.group(0)}" if github_match else ""
        }

    def _segment_sections(self, text: str) -> Dict[str, str]:
        lines = text.split("\n")
        sections: Dict[str, List[str]] = {
            "summary": [],
            "skills": [],
            "experience": [],
            "projects": [],
            "education": [],
            "certifications": [],
            "other": []
        }

        current_section = "summary"

        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                continue

            clean_header = re.sub(r"[^a-zA-Z\s]", "", trimmed).lower().strip()

            # Flexible header detection
            if any(clean_header == h for h in ["summary", "professional summary", "profile", "about me", "objective"]):
                current_section = "summary"
                continue
            elif any(w in clean_header for w in ["skill", "competenc", "technologies", "tech stack"]) and len(clean_header) < 30:
                current_section = "skills"
                continue
            elif any(w in clean_header for w in ["experience", "work history", "employment", "career"]) and len(clean_header) < 35:
                current_section = "experience"
                continue
            elif any(w in clean_header for w in ["project", "selected project", "key project"]) and len(clean_header) < 30:
                current_section = "projects"
                continue
            elif any(w in clean_header for w in ["education", "academic", "qualifications", "degree"]) and len(clean_header) < 30:
                current_section = "education"
                continue
            elif any(w in clean_header for w in ["certification", "licenses", "certificates", "courses"]) and len(clean_header) < 30:
                current_section = "certifications"
                continue

            sections[current_section].append(trimmed)

        return {k: "\n".join(v).strip() for k, v in sections.items() if v}

    def _parse_experience_items(self, text: str) -> List[Dict[str, Any]]:
        """Parses company, title, dates, and bullet points from experience text."""
        items = []
        if not text:
            return items

        lines = [l.strip() for l in text.split("\n") if l.strip()]
        current_item: Dict[str, Any] = {}

        # Matches dates like 'Mar 2025 – Present' or 'Jul 2024 – Feb 2025' or '2021 - 2024'
        date_pattern = re.compile(
            r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}|\d{4})\s*[-–—]\s*(Present|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}|\d{4})",
            re.I
        )

        for line in lines:
            date_match = date_pattern.search(line)
            # If line has date and is not a bullet point
            if date_match and not line.startswith("•") and not line.startswith("-") and not line.startswith("*"):
                if current_item and current_item.get("bullets"):
                    items.append(current_item)

                matched_dates = date_match.group(0).strip()
                company_part = line[:date_match.start()].strip(" –—-|")
                after_part = line[date_match.end():].strip(" –—-|")

                current_item = {
                    "company": company_part or "Engineering Organization",
                    "title": after_part or "",
                    "duration": matched_dates,
                    "bullets": []
                }
            elif line.startswith("•") or line.startswith("-") or line.startswith("*"):
                bullet = re.sub(r"^[•\-*]\s*", "", line).strip()
                if current_item:
                    current_item.setdefault("bullets", []).append(bullet)
                else:
                    current_item = {
                        "company": "Commercial Engineering Experience",
                        "title": "Software Engineer",
                        "duration": "",
                        "bullets": [bullet]
                    }
            else:
                if current_item:
                    # If we don't have a title yet, this next non-bullet line is the job title / location
                    if not current_item.get("title"):
                        current_item["title"] = line
                    elif current_item.get("bullets"):
                        current_item["bullets"][-1] += " " + line
                    else:
                        current_item.setdefault("bullets", []).append(line)

        if current_item and current_item.get("bullets"):
            items.append(current_item)

        return items

    def _parse_project_items(self, text: str) -> List[Dict[str, Any]]:
        """Parses projects with titles, technologies, and bullet points."""
        projects = []
        if not text:
            return projects

        lines = [l.strip() for l in text.split("\n") if l.strip()]
        curr_proj: Dict[str, Any] = {}

        for line in lines:
            if "|" in line or "—" in line or " - " in line and not line.startswith("•"):
                if curr_proj and curr_proj.get("bullets"):
                    projects.append(curr_proj)
                
                split_parts = re.split(r"[|—]", line)
                p_title = split_parts[0].strip()
                p_tech = [t.strip() for t in split_parts[1].split(",") if t.strip()] if len(split_parts) > 1 else []
                
                curr_proj = {
                    "title": p_title,
                    "technologies": p_tech,
                    "bullets": []
                }
            elif line.startswith("•") or line.startswith("-") or line.startswith("*"):
                clean = re.sub(r"^[•\-*]\s*", "", line).strip()
                if curr_proj:
                    curr_proj.setdefault("bullets", []).append(clean)
                else:
                    curr_proj = {"title": "Key Engineering Project", "technologies": [], "bullets": [clean]}
            else:
                if curr_proj and curr_proj.get("bullets"):
                    curr_proj["bullets"][-1] += " " + line
                elif curr_proj:
                    curr_proj.setdefault("bullets", []).append(line)

        if curr_proj and curr_proj.get("bullets"):
            projects.append(curr_proj)

        return projects

    def _parse_education_items(self, text: str) -> List[Dict[str, Any]]:
        """Parses education degrees, institutions, and dates cleanly."""
        edu_list = []
        if not text:
            return edu_list

        lines = [l.strip() for l in text.split("\n") if l.strip()]
        curr_edu: Dict[str, Any] = {}

        for line in lines:
            if any(w in line.lower() for w in ["university", "institute", "college", "school"]):
                if curr_edu:
                    edu_list.append(curr_edu)
                curr_edu = {"institution": line, "degree": "", "details": ""}
            elif any(w in line.lower() for w in ["bsc", "bachelor", "master", "msc", "diploma", "degree", "beng"]):
                if curr_edu:
                    curr_edu["degree"] = line
                else:
                    curr_edu = {"institution": "", "degree": line, "details": ""}
            elif line.startswith("•") or "study:" in line.lower():
                clean = re.sub(r"^[•\-*]\s*", "", line).strip()
                if curr_edu:
                    curr_edu["details"] = clean
            else:
                if curr_edu and not curr_edu.get("degree"):
                    curr_edu["degree"] = line

        if curr_edu:
            edu_list.append(curr_edu)

        return edu_list
