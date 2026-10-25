import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import DB_PATH

PRESEEDED_PORTALS = [
    # --- UAE: ENERGY, UTILITIES & INDUSTRIAL IOT ---
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
        "name": "Masdar (Abu Dhabi Future Energy Company)",
        "portal_url": "https://masdar.ae/en/about-us/careers",
        "region": "GULF",
        "country": "United Arab Emirates",
        "industry": "Renewables, Solar & Clean Tech",
        "ats_type": "SuccessFactors",
        "hr_email": "careers@masdar.ae",
        "notes": "Global pioneer in utility-scale solar PV, wind farms, and battery energy storage systems (BESS). Perfect fit for solar telemetry and TimescaleDB background."
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
        "name": "TAQA (Abu Dhabi National Energy Company)",
        "portal_url": "https://www.taqa.com/careers/",
        "region": "GULF",
        "country": "United Arab Emirates",
        "industry": "Power Generation & Water Desalination",
        "ats_type": "Workday",
        "hr_email": "careers@taqa.com",
        "notes": "Major diversified utilities and energy group operating transmission, distribution, and generation assets across UAE and EMEA."
    },
    {
        "name": "Tabreed (National Central Cooling Company)",
        "portal_url": "https://www.tabreed.ae/careers/",
        "region": "GULF",
        "country": "United Arab Emirates",
        "industry": "District Cooling & Industrial IoT",
        "ats_type": "Enterprise Portal",
        "hr_email": "careers@tabreed.ae",
        "notes": "World's leading district cooling utility. Uses Modbus, industrial sensors, and IoT telemetry for automated thermal plants."
    },
    {
        "name": "ENOC (Emirates National Oil Company)",
        "portal_url": "https://www.enoc.com/careers",
        "region": "GULF",
        "country": "United Arab Emirates",
        "industry": "Oil, Gas & Energy Trading",
        "ats_type": "Oracle Taleo",
        "hr_email": "careers@enoc.com",
        "notes": "Wholly owned by the Government of Dubai. Operates refinery, fuel distribution networks, and digital logistics."
    },

    # --- UAE: SOVEREIGN TECH, AI & DEFENSE ---
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
        "name": "Presight.ai (G42 Big Data Analytics)",
        "portal_url": "https://www.presight.ai/careers",
        "region": "GULF",
        "country": "United Arab Emirates",
        "industry": "Big Data Analytics & Public Safety AI",
        "ats_type": "Greenhouse",
        "hr_email": "talent@presight.ai",
        "notes": "ADX-listed G42 company specializing in big data analytics, computer vision, and high-throughput telemetry pipelines."
    },
    {
        "name": "EDGE Group (Advanced Tech & Defense)",
        "portal_url": "https://edgegroup.ae/careers",
        "region": "GULF",
        "country": "United Arab Emirates",
        "industry": "Autonomous Systems, Robotics & Embedded",
        "ats_type": "SAP SuccessFactors",
        "hr_email": "careers@edgegroup.ae",
        "notes": "One of the world's leading advanced technology groups developing autonomous systems, robotics, radar, and electronic warfare."
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
        "name": "ADQ (Abu Dhabi Developmental Holding)",
        "portal_url": "https://www.adq.ae/careers",
        "region": "GULF",
        "country": "United Arab Emirates",
        "industry": "Sovereign Holdings & Infrastructure",
        "ats_type": "Workday",
        "hr_email": "careers@adq.ae",
        "notes": "One of the region's largest holding companies with investments across supply chain, digital, food and energy."
    },

    # --- UAE: TELECOM, AVIATION & DIGITAL ENTERPRISE ---
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
        "name": "du (Emirates Integrated Telecommunications)",
        "portal_url": "https://www.du.ae/about-us/careers",
        "region": "GULF",
        "country": "United Arab Emirates",
        "industry": "5G, Cloud & Telecom Networks",
        "ats_type": "SAP SuccessFactors",
        "hr_email": "careers@du.ae",
        "notes": "Major UAE telecommunications provider driving 5G slicing, IoT device networks, and enterprise cloud solutions."
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
        "name": "flydubai",
        "portal_url": "https://careers.flydubai.com",
        "region": "GULF",
        "country": "United Arab Emirates",
        "industry": "Commercial Aviation & Fleet Ops",
        "ats_type": "Oracle Taleo",
        "hr_email": "careers@flydubai.com",
        "notes": "Dubai-based airline operating modern Boeing 737 fleets with high-volume booking and flight operation microservices."
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
        "name": "Kitopi (Managed Cloud Kitchen Unicorn)",
        "portal_url": "https://www.kitopi.com/careers",
        "region": "GULF",
        "country": "United Arab Emirates",
        "industry": "Smart Kitchen Operating System (SKOS)",
        "ats_type": "Lever",
        "hr_email": "careers@kitopi.com",
        "notes": "Tech unicorn operating hundreds of smart kitchens across UAE, KSA, and Bahrain with proprietary IoT and telemetry software."
    },
    {
        "name": "Bayzat (HR Tech & FinTech)",
        "portal_url": "https://www.bayzat.com/careers",
        "region": "GULF",
        "country": "United Arab Emirates",
        "industry": "FinTech, Payroll & Insurance",
        "ats_type": "Greenhouse",
        "hr_email": "careers@bayzat.com",
        "notes": "Leading MENA employee management, payroll, and benefits SaaS platform based in Dubai."
    },
    {
        "name": "Emirates NBD",
        "portal_url": "https://www.emiratesnbd.com/en/careers",
        "region": "GULF",
        "country": "United Arab Emirates",
        "industry": "Banking & Financial Services",
        "ats_type": "SAP SuccessFactors",
        "hr_email": "careers@emiratesnbd.com",
        "notes": "Leading banking group in the MENAT region pioneering cloud-native microservices, open banking APIs, and Liv digital bank."
    },
    {
        "name": "First Abu Dhabi Bank (FAB)",
        "portal_url": "https://www.bankfab.com/en-ae/about-fab/careers",
        "region": "GULF",
        "country": "United Arab Emirates",
        "industry": "Corporate Banking & FinTech",
        "ats_type": "Workday",
        "hr_email": "careers@bankfab.com",
        "notes": "Largest bank in the UAE with international headquarters in Abu Dhabi and a large digital engineering lab."
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

    # --- SAUDI ARABIA: VISION 2030 MEGA-PROJECTS & ENERGY ---
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
        "name": "Red Sea Global",
        "portal_url": "https://careers.redseaglobal.com",
        "region": "GULF",
        "country": "Saudi Arabia",
        "industry": "Regenerative Tourism & Off-Grid Solar",
        "ats_type": "Workday",
        "hr_email": "careers@redseaglobal.com",
        "notes": "Pioneering 100% off-grid solar-and-battery powered luxury destinations. Direct application for solar/battery telemetry expertise."
    },
    {
        "name": "ACWA Power",
        "portal_url": "https://www.acwapower.com/en/careers/",
        "region": "GULF",
        "country": "Saudi Arabia",
        "industry": "Renewable Power, Green Hydrogen & Desalination",
        "ats_type": "Oracle Cloud",
        "hr_email": "careers@acwapower.com",
        "notes": "Global leader in desalinated water and renewable energy transition. Builds giant solar PV, concentrated solar, and energy storage telemetry plants."
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
        "name": "stc (Saudi Telecom Company)",
        "portal_url": "https://www.stc.com.sa/content/stc/sa/en/careers.html",
        "region": "GULF",
        "country": "Saudi Arabia",
        "industry": "Telecom, Cloud Infrastructure & Cybersecurity",
        "ats_type": "Workday",
        "hr_email": "careers@stc.com.sa",
        "notes": "Digital champion of MENA operating Tier IV data centers, large cloud regions, and extensive microservices architectures."
    },
    {
        "name": "solutions by stc",
        "portal_url": "https://solutions.com.sa/careers/",
        "region": "GULF",
        "country": "Saudi Arabia",
        "industry": "IT Transformation & Enterprise Cloud",
        "ats_type": "Oracle Cloud",
        "hr_email": "careers@solutions.com.sa",
        "notes": "Leading IT services enabler in Saudi Arabia, powering large-scale IoT integration and distributed systems for government and enterprise."
    },
    {
        "name": "Qiddiya Investment Company",
        "portal_url": "https://qiddiya.com/careers/",
        "region": "GULF",
        "country": "Saudi Arabia",
        "industry": "Smart Entertainment & Gaming City",
        "ats_type": "Workday",
        "hr_email": "careers@qiddiya.com",
        "notes": "PIF gigaproject building the global capital of entertainment, gaming, and sports with real-time digital twin architectures."
    },
    {
        "name": "ROSHN (PIF Real Estate Gigaproject)",
        "portal_url": "https://www.roshn.sa/en/careers",
        "region": "GULF",
        "country": "Saudi Arabia",
        "industry": "Smart Communities & PropTech",
        "ats_type": "Oracle Cloud",
        "hr_email": "careers@roshn.sa",
        "notes": "PIF-backed national community developer delivering integrated smart residential communities across Riyadh, Jeddah, and Makkah."
    },
    {
        "name": "Diriyah Company (DGDA)",
        "portal_url": "https://www.diriyah.sa/en/careers",
        "region": "GULF",
        "country": "Saudi Arabia",
        "industry": "Heritage & Smart Urban Development",
        "ats_type": "SAP SuccessFactors",
        "hr_email": "careers@diriyah.sa",
        "notes": "Preserving the birthplace of the Kingdom into a world-class smart cultural and historical destination."
    },
    {
        "name": "Elm (Saudi Government Digital Solutions)",
        "portal_url": "https://www.elm.sa/en/careers",
        "region": "GULF",
        "country": "Saudi Arabia",
        "industry": "Digital Government, Absher & FinTech",
        "ats_type": "SAP SuccessFactors",
        "hr_email": "careers@elm.sa",
        "notes": "Publicly traded leader in digital solutions that powers the Absher platform, e-visas, and trusted verification services."
    },
    {
        "name": "Saudi Electricity Company (SEC)",
        "portal_url": "https://www.se.com.sa/en-us/Pages/Careers.aspx",
        "region": "GULF",
        "country": "Saudi Arabia",
        "industry": "National Electric Grid & Telemetry",
        "ats_type": "SAP SuccessFactors",
        "hr_email": "recruitment@se.com.sa",
        "notes": "Monopoly electric generation, transmission, and smart grid distribution across the Kingdom."
    },
    {
        "name": "Lucid Motors Saudi Arabia",
        "portal_url": "https://lucidmotors.com/careers",
        "region": "GULF",
        "country": "Saudi Arabia",
        "industry": "Electric Vehicles & Battery Tech",
        "ats_type": "Jobvite",
        "hr_email": "careers@lucidmotors.com",
        "notes": "EV manufacturer building high-performance luxury electric vehicles with production facilities in King Abdullah Economic City."
    },

    # --- QATAR & OMAN: ENERGY & SYSTEMS ---
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
        "name": "Qatar Airways",
        "portal_url": "https://qatarairways.wd3.myworkdayjobs.com/QatarAirwaysCareers",
        "region": "GULF",
        "country": "Qatar",
        "industry": "Aviation & Global Logistics Tech",
        "ats_type": "Workday",
        "hr_email": "recruitment@qatarairways.com.qa",
        "notes": "One of the world's premier airlines with high-volume booking engines, flight telemetry, and distributed IT infrastructure."
    },
    {
        "name": "Ooredoo Qatar",
        "portal_url": "https://careers.ooredoo.com/",
        "region": "GULF",
        "country": "Qatar",
        "industry": "Telecommunications & Cloud",
        "ats_type": "SAP SuccessFactors",
        "hr_email": "careers@ooredoo.qa",
        "notes": "Leading international telecom provider headquartered in Doha, operating 5G and fiber network microservices."
    },
    {
        "name": "Petroleum Development Oman (PDO)",
        "portal_url": "https://www.pdo.co.om/en/careers/Pages/default.aspx",
        "region": "GULF",
        "country": "Oman",
        "industry": "Hydrocarbon Exploration & Industrial IoT",
        "ats_type": "Oracle Taleo",
        "hr_email": "careers@pdo.co.om",
        "notes": "Oman's leading oil and gas exploration and production company, investing heavily in solar-powered EOR and telemetry."
    },
    {
        "name": "OQ (Oman Global Integrated Energy)",
        "portal_url": "https://oq.com/en/careers",
        "region": "GULF",
        "country": "Oman",
        "industry": "Integrated Energy & Petrochemicals",
        "ats_type": "SAP SuccessFactors",
        "hr_email": "careers@oq.com",
        "notes": "Oman's global energy investment group with operations spanning 17 countries across energy infrastructure."
    },

    # --- SINGAPORE & SOUTHEAST ASIA TECH ---
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
        "name": "Sea Group / Shopee",
        "portal_url": "https://careers.sea.com",
        "region": "SINGAPORE",
        "country": "Singapore",
        "industry": "E-Commerce & Digital Finance",
        "ats_type": "Direct Portal",
        "hr_email": "careers@sea.com",
        "notes": "Leading consumer internet company in Southeast Asia and Taiwan, operating Shopee, SeaMoney, and Garena."
    },
    {
        "name": "Singtel",
        "portal_url": "https://www.singtel.com/about-us/careers",
        "region": "SINGAPORE",
        "country": "Singapore",
        "industry": "Telecommunications & Cyber Security",
        "ats_type": "Workday",
        "hr_email": "careers@singtel.com",
        "notes": "Asia's leading communications technology group providing fixed, mobile, data, internet, TV, and infocomms technology."
    },
    {
        "name": "DBS Bank",
        "portal_url": "https://www.dbs.com/careers",
        "region": "SINGAPORE",
        "country": "Singapore",
        "industry": "Digital Banking & FinTech Platform",
        "ats_type": "Workday",
        "hr_email": "careers@dbs.com",
        "notes": "World's Best Digital Bank. Operates like a technology company with 95% cloud-native backend microservices."
    },

    # --- UK, EUROPE & AUSTRALIA: MIGRATABLE CORRIDORS ---
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
    },
    {
        "name": "Deliveroo",
        "portal_url": "https://careers.deliveroo.co.uk/",
        "region": "UK_EUROPE",
        "country": "United Kingdom",
        "industry": "On-Demand Logistics & Microservices",
        "ats_type": "Greenhouse",
        "hr_email": "careers@deliveroo.co.uk",
        "notes": "Leading online food and grocery delivery company with sophisticated dispatch routing algorithms and Python/Go systems."
    },
    {
        "name": "Monzo Bank",
        "portal_url": "https://monzo.com/careers/",
        "region": "UK_EUROPE",
        "country": "United Kingdom",
        "industry": "Cloud-Native Digital Banking",
        "ats_type": "Greenhouse",
        "hr_email": "careers@monzo.com",
        "notes": "UK digital bank running over 2,500 core microservices, event-driven message architectures, and automated ledger infrastructure."
    },
    {
        "name": "Siemens Energy",
        "portal_url": "https://www.siemens-energy.com/global/en/company/jobs.html",
        "region": "UK_EUROPE",
        "country": "Germany / UK / Middle East",
        "industry": "Power Grid Automation & SCADA",
        "ats_type": "Workday",
        "hr_email": "careers@siemens-energy.com",
        "notes": "World leader in power generation transmission, grid telemetry, SCADA systems, and green hydrogen technologies."
    },
    {
        "name": "Canva",
        "portal_url": "https://www.lifeatcanva.com/en/jobs/",
        "region": "GLOBAL",
        "country": "Australia / Remote",
        "industry": "Visual Collaboration & Cloud Software",
        "ats_type": "Jobvite",
        "hr_email": "careers@canva.com",
        "notes": "Global visual communication platform headquartered in Sydney, Australia. Excellent migration and sponsorship support for senior talent."
    },
    {
        "name": "Atlassian",
        "portal_url": "https://www.atlassian.com/company/careers",
        "region": "GLOBAL",
        "country": "Australia / Remote",
        "industry": "Enterprise Collaboration Tools (Jira, Confluence)",
        "ats_type": "Jobvite",
        "hr_email": "careers@atlassian.com",
        "notes": "Global enterprise software powerhouse headquartered in Sydney, with remote-first engineering teams and extensive distributed microservices."
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
                    INSERT INTO career_portals (
                        name, portal_url, region, country, industry, ats_type, hr_email, notes, is_custom, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                    ON CONFLICT(portal_url) DO UPDATE SET
                        name=excluded.name,
                        region=excluded.region,
                        country=excluded.country,
                        industry=excluded.industry,
                        ats_type=excluded.ats_type,
                        hr_email=excluded.hr_email,
                        notes=excluded.notes
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
                sql += " AND (name LIKE ? OR industry LIKE ? OR country LIKE ? OR portal_url LIKE ? OR notes LIKE ?)"
                q_wildcard = f"%{query.strip()}%"
                params.extend([q_wildcard, q_wildcard, q_wildcard, q_wildcard, q_wildcard])

            sql += " ORDER BY is_custom DESC, region ASC, name ASC"
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
