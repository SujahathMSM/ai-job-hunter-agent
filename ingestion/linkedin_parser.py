import csv
import re
from pathlib import Path
from typing import Dict, Any, List
import pypdf

class LinkedInParser:
    """Parses LinkedIn PDF Profile exports and LinkedIn Data Archive CSV files without noise."""

    def parse_profile_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """Extracts structured sections from LinkedIn's official 'Save to PDF' profile export."""
        text = ""
        try:
            reader = pypdf.PdfReader(str(pdf_path))
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        except Exception as e:
            return {"error": f"Failed to read LinkedIn PDF: {e}"}

        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # Find real candidate name in LinkedIn PDF:
        # In LinkedIn PDFs, the real name appears prominently before the Headline & Summary,
        # usually after "Contact", "Top Skills", and "Certifications" blocks.
        candidate_name = ""
        headline = ""
        location = ""

        # Search for lines followed by "Summary" or before a headline
        for i, line in enumerate(lines):
            # Skip noise
            if line.lower() in ["contact", "top skills", "certifications", "languages", "page"]:
                continue
            if "@" in line or "http" in line or "linkedin.com" in line or "+" in line:
                continue
            # Look for the line right before the headline or summary
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if any(kw in next_line.lower() for kw in ["engineer", "developer", "architect", "lead", "specialist"]):
                    clean = re.sub(r"[^a-zA-Z\s.]", "", line).strip()
                    if 2 <= len(clean.split()) <= 4:
                        candidate_name = clean
                        headline = next_line
                        if i + 2 < len(lines) and ("sri lanka" in lines[i+2].lower() or "province" in lines[i+2].lower()):
                            location = lines[i+2]
                        break

        # Fallback if name not found yet
        if not candidate_name:
            for line in lines:
                if line.lower() not in ["contact", "top skills", "certifications", "summary"] and not any(c in line for c in ["@", "http", "+", "/"]):
                    words = line.split()
                    if 2 <= len(words) <= 4:
                        candidate_name = line
                        break

        # Extract Skills
        skills = []
        skills_match = re.search(r"Top Skills\s+(.*?)(?=Certifications|Languages|Summary|Experience|$)", text, re.DOTALL)
        if skills_match:
            raw_skills = skills_match.group(1).split("\n")
            skills = [s.strip() for s in raw_skills if s.strip() and len(s.strip()) < 35]

        # Extract Summary
        summary = ""
        summary_match = re.search(r"Summary\s+(.*?)(?=Experience|Education|$)", text, re.DOTALL)
        if summary_match:
            summary = summary_match.group(1).strip()

        return {
            "source": "LinkedIn PDF",
            "name": candidate_name,
            "headline": headline,
            "location": location,
            "summary": summary,
            "top_skills": skills,
            "full_text": text
        }

    def parse_csv_archive(self, folder_or_file: Path) -> Dict[str, Any]:
        data = {
            "source": "LinkedIn Archive CSV",
            "profile": {},
            "positions": [],
            "skills": [],
            "education": []
        }

        search_dir = folder_or_file if folder_or_file.is_dir() else folder_or_file.parent

        profile_csv = search_dir / "Profile.csv"
        if profile_csv.exists():
            try:
                with open(profile_csv, mode="r", encoding="utf-8", errors="ignore") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        data["profile"] = row
                        break
            except Exception as e:
                print(f"Error reading Profile.csv: {e}")

        pos_csv = search_dir / "Positions.csv"
        if pos_csv.exists():
            try:
                with open(pos_csv, mode="r", encoding="utf-8", errors="ignore") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        data["positions"].append(row)
            except Exception as e:
                print(f"Error reading Positions.csv: {e}")

        skills_csv = search_dir / "Skills.csv"
        if skills_csv.exists():
            try:
                with open(skills_csv, mode="r", encoding="utf-8", errors="ignore") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        s_name = row.get("Name", "").strip()
                        if s_name:
                            data["skills"].append(s_name)
            except Exception as e:
                print(f"Error reading Skills.csv: {e}")

        edu_csv = search_dir / "Education.csv"
        if edu_csv.exists():
            try:
                with open(edu_csv, mode="r", encoding="utf-8", errors="ignore") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        data["education"].append(row)
            except Exception as e:
                print(f"Error reading Education.csv: {e}")

        return data

    def parse_any(self, path: Path) -> Dict[str, Any]:
        if path.suffix.lower() == ".pdf":
            return self.parse_profile_pdf(path)
        elif path.suffix.lower() == ".csv" or path.is_dir():
            return self.parse_csv_archive(path)
        return {}
