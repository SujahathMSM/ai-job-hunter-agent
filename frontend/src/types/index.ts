export interface CandidateProfile {
  identity: {
    full_name: string;
    professional_title: string;
    email: string;
    phone: string;
    current_location: string;
    nationality: string;
    relocation_status: string;
    linkedin: string;
    github: string;
  };
  summary: string;
  core_skills: string[];
  technical_stack: string[];
  core_skills_categorized?: Array<{
    category: string;
    skills: string;
  }>;
  work_history: Array<{
    title: string;
    company: string;
    duration: string;
    location: string;
    bullets: string[];
  }>;
  projects: Array<{
    title: string;
    technologies: string;
    bullets: string[];
  }>;
  education: Array<{
    degree: string;
    institution: string;
    duration: string;
    location: string;
    details: string;
  }>;
}

export interface JobItem {
  id?: string;
  job_title: string;
  company: string;
  location: string;
  site?: string;
  portal?: string;
  job_url?: string;
  date_posted?: string;
  posted_label?: string;
  days_ago?: number;
  salary?: string;
  salary_range?: string;
  description: string;
  full_description?: string;
  hr_email?: string;
  has_hr_email?: boolean;
  recruiter_dork?: string;
  fit_analysis?: {
    match_score: number;
    is_engineering: boolean;
    geo_eligible: boolean;
    matched_skills: string[];
    missing_tech: string[];
    summary?: string;
  };
}

export interface HiringCompanyLead {
  company: string;
  job_title: string;
  location: string;
  domain: string;
  email_pattern: string;
  primary_email: string;
  posting_emails: string[];
  verified_contacts: Array<{
    name: string;
    email: string;
    role: string;
    confidence: string;
  }>;
  portal: string;
  recruiter_dork: string;
  eng_lead_dork: string;
  description: string;
}

export interface ApplicationItem {
  id: number;
  job_title: string;
  company: string;
  location: string;
  hr_email: string;
  portal_link?: string;
  status: string;
  date_applied: string;
  notes?: string;
}

export interface GlobalRemoteJob {
  id: string;
  job_title: string;
  company: string;
  location: string;
  is_worldwide: boolean;
  salary: string;
  tags: string[];
  source: string;
  source_type: "public_api" | "rss" | "ats" | string;
  apply_url: string;
  description: string;
  match_score: number;
  posted_at?: string;
}
