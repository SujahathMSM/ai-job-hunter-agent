import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import DB_PATH

PRESEEDED_PORTALS = [
    {
        "name": "ADNOC (Abu Dhabi National Oil Company)",
        "portal_url": "https://jobs.adnoc.ae/us/en",
        "region": "GULF",
        "country": "United Arab Emirates",
        "industry": "Energy, Oil & Gas",
        "ats_type": "Phenom People / Enterprise",
        "hr_email": "careers@adnoc.ae",
        "notes": "Direct career portal for UAE national energy group. High demand for IoT, telemetry, SCADA, and Python backend engineers."
    },
    {
        "name": "Saudi Aramco",
        "portal_url": "https://jobs.aramco.com",
        "region": "GULF",
        "country": "Saudi Arabia",
        "industry": "Energy & Advanced Materials",
        "ats_type": "SAP SuccessFactors",
        "hr_email": "recruitment@aramco.com",
        "notes": "World's largest integrated energy enterprise. Extensive digital transformation and industrial computing divisions in Dhahran."
    },
    {
        "name": "NEOM (Cognitive Cities & Tech)",
        "portal_url": "https://careers.neom.com",
        "region": "GULF",
        "country": "Saudi Arabia",
        "industry": "Smart Cities, AI & Clean Energy",
        "ats_type": "Workday",
        "hr_email": "talent@neom.com",
        "notes": "Saudi Arabia Vision 2030 flagship gigaproject. Enormous investments in autonomous systems, IoT networks, and green grid telemetry."
    },
    {
        "name": "G42 (Group 42 AI & Cloud)",
        "portal_url": "https://g42.ai/careers",
        "region": "GULF",
        "country": "United Arab Emirates",
        "industry": "Artificial Intelligence & Cloud",
        "ats_type": "Greenhouse",
        "hr_email": "careers@g42.ai",
        "notes": "Leading AI and cloud computing conglomerate in Abu Dhabi, building sovereign supercomputers and large models."
    },
    {
        "name": "Emirates Group",
        "portal_url": "https://www.emiratesgroupcareers.com",
        "region": "GULF",
        "country": "United Arab Emirates",
        "industry": "Aviation & Enterprise Systems",
        "ats_type": "Oracle Taleo",
        "hr_email": "recruitment@emirates.com",
        "notes": "Global aviation leader headquartered in Dubai with a massive in-house IT, microservices, and operations engineering division."
    },
    {
        "name": "DEWA (Dubai Electricity & Water Authority)",
        "portal_url": "https://www.dewa.gov.ae/en/about-us/careers",
        "region": "GULF",
        "country": "United Arab Emirates",
        "industry": "Smart Utilities & IoT Grid",
        "ats_type": "Oracle Cloud / Gov Portal",
        "hr_email": "careers@dewa.gov.ae",
        "notes": "Pioneering smart grid utility in Dubai. Key hub for smart meter data pipelines, TimescaleDB/PostgreSQL architectures, and SCADA."
    },
    {
        "name": "Mubadala Investment Company",
        "portal_url": "https://www.mubadala.com/en/careers",
        "region": "GULF",
        "country": "United Arab Emirates",
        "industry": "Sovereign Wealth & Deep Tech",
        "ats_type": "Workday",
        "hr_email": "careers@mubadala.ae",
        "notes": "Abu Dhabi sovereign investor managing global tech and infrastructure assets."
    },
    {
        "name": "Etisalat by e&",
        "portal_url": "https://www.eand.com/en/careers.html",
        "region": "GULF",
        "country": "United Arab Emirates",
        "industry": "Telecom & Digital Platforms",
        "ats_type": "SAP SuccessFactors",
        "hr_email": "careers@etisalat.ae",
        "notes": "Global technology group with presence across 16 countries in the Middle East, Asia, and Africa."
    },
    {
        "name": "QatarEnergy",
        "portal_url": "https://careers.qatarenergy.qa",
        "region": "GULF",
        "country": "Qatar",
        "industry": "LNG & Energy Infrastructure",
        "ats_type": "SAP SuccessFactors",
        "hr_email": "careers@qatarenergy.qa",
        "notes": "World leader in Liquefied Natural Gas (LNG) infrastructure, automation, and enterprise computing in Doha."
    },
    {
        "name": "SABIC (Saudi Basic Industries Corp)",
        "portal_url": "https://www.sabic.com/en/careers",
        "region": "GULF",
        "country": "Saudi Arabia",
        "industry": "Chemicals & Advanced Manufacturing",
        "ats_type": "SAP SuccessFactors",
        "hr_email": "recruitment@sabic.com",
        "notes": "Global leader in diversified chemicals with major digital and industrial software teams in Riyadh and Jubail."
    },
    {
        "name": "Careem (An Uber Company)",
        "portal_url": "https://www.careem.com/careers",
        "region": "GULF",
        "country": "United Arab Emirates",
        "industry": "Super-App & Logistics Tech",
        "ats_type": "Greenhouse",
        "hr_email": "talent@careem.com",
        "notes": "Leading everyday super-app across the Middle East. High-concurrency microservices, distributed caching, and backend systems."
    },
    {
        "name": "Talabat (Delivery Hero MENA)",
        "portal_url": "https://careers.deliveryhero.com/global/en/talabat",
        "region": "GULF",
        "country": "United Arab Emirates",
        "industry": "Quick-Commerce & On-Demand Delivery",
        "ats_type": "SmartRecruiters",
        "hr_email": "careers@talabat.com",
        "notes": "Pioneer of online food delivery and quick-commerce in the Middle East, HQ in Dubai."
    },
    {
        "name": "Dubai Careers (Official Govt Gateway)",
        "portal_url": "https://dubaicareers.ae",
        "region": "GULF",
        "country": "United Arab Emirates",
        "industry": "Government & Public Services",
        "ats_type": "GovPortal",
        "hr_email": "support@dubaicareers.ae",
        "notes": "Unified recruitment portal for 40+ Dubai Government entities, Digital Dubai, and municipal tech authorities."
    },
    {
        "name": "GovTech Singapore",
        "portal_url": "https://www.tech.gov.sg/careers",
        "region": "SINGAPORE",
        "country": "Singapore",
        "industry": "Government & Digital Platforms",
        "ats_type": "Workday",
        "hr_email": "join_us@tech.gov.sg",
        "notes": "Lead agency driving Singapore's Smart Nation initiative. Robust engineering practices, microservices, and public digital infrastructure."
    },
    {
        "name": "Grab Careers",
        "portal_url": "https://grab.careers",
        "region": "SINGAPORE",
        "country": "Singapore",
        "industry": "Mobility, Fintech & Deliveries",
        "ats_type": "Greenhouse",
        "hr_email": "careers@grab.com",
        "notes": "Southeast Asia's leading super-app platform spanning deliveries, mobility, and digital financial services."
    },
    {
        "name": "Civil Service Jobs UK (DDaT)",
        "portal_url": "https://www.civilservicejobs.service.gov.uk",
        "region": "UK_EUROPE",
        "country": "United Kingdom",
        "industry": "Public Sector & Trade Technology",
        "ats_type": "Oleeo",
        "hr_email": "DdaT.recruitment@businessandtrade.gov.uk",
        "notes": "Direct official portal for UK Government roles, including Department for Business and Trade digital engineering positions."
    },
    {
        "name": "Revolut",
        "portal_url": "https://www.revolut.com/careers",
        "region": "UK_EUROPE",
        "country": "United Kingdom / Remote",
        "industry": "Global Fintech & Banking",
        "ats_type": "Lever",
        "hr_email": "careers@revolut.com",
        "notes": "Global financial technology leader with massive Python, distributed systems, and real-time ledger engineering teams."
    }
]

class CareerPortalManager:
    """Manages enterprise career portals (ADNOC, Aramco, NEOM, DEWA, etc.)
    with local persistence in SQLite and quick search capabilities."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()
        self._seed_default_portals()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS career_portals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    portal_url TEXT NOT NULL UNIQUE,
                    region TEXT NOT NULL,
                    country TEXT,
                    industry TEXT,
                    ats_type TEXT,
                    hr_email TEXT,
                    notes TEXT,
                    is_custom INTEGER DEFAULT 0,
                    created_at TEXT
                )
            """)
            conn.commit()

    def _seed_default_portals(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for p in PRESEEDED_PORTALS:
                cursor.execute("""
                    INSERT OR IGNORE INTO career_portals (
                        name, portal_url, region, country, industry, ats_type, hr_email, notes, is_custom, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                """, (
                    p["name"], p["portal_url"], p["region"], p["country"],
                    p["industry"], p["ats_type"], p["hr_email"], p["notes"], now
                ))
            conn.commit()

    def list_portals(
        self,
        region: Optional[str] = None,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            sql = "SELECT * FROM career_portals WHERE 1=1"
            params = []

            if region and region.upper() != "ALL":
                sql += " AND region = ?"
                params.append(region.upper())

            if query and query.strip():
                sql += " AND (name LIKE ? OR industry LIKE ? OR country LIKE ? OR portal_url LIKE ?)"
                q_wildcard = f"%{query.strip()}%"
                params.extend([q_wildcard, q_wildcard, q_wildcard, q_wildcard])

            sql += " ORDER BY is_custom DESC, name ASC"
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    def add_custom_portal(
        self,
        name: str,
        portal_url: str,
        region: str = "GULF",
        country: str = "UAE",
        industry: str = "Technology & Engineering",
        ats_type: str = "Direct Portal",
        hr_email: str = "",
        notes: str = ""
    ) -> Dict[str, Any]:
        # Normalize URL
        url = portal_url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO career_portals (
                    name, portal_url, region, country, industry, ats_type, hr_email, notes, is_custom, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                ON CONFLICT(portal_url) DO UPDATE SET
                    name=excluded.name,
                    region=excluded.region,
                    country=excluded.country,
                    industry=excluded.industry,
                    hr_email=excluded.hr_email,
                    notes=excluded.notes
            """, (
                name.strip(), url, region.upper(), country.strip(),
                industry.strip(), ats_type.strip(), hr_email.strip(), notes.strip(), now
            ))
            conn.commit()
            portal_id = cursor.lastrowid

        return {
            "id": portal_id,
            "name": name,
            "portal_url": url,
            "region": region,
            "country": country,
            "industry": industry,
            "hr_email": hr_email,
            "notes": notes,
            "is_custom": 1,
            "created_at": now
        }

    def delete_portal(self, portal_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM career_portals WHERE id = ?", (portal_id,))
            conn.commit()
            return cursor.rowcount > 0
