import { CandidateProfile, JobItem, HiringCompanyLead, ApplicationItem } from "../types";

const API_BASE = "/api";

export async function fetchProfile(): Promise<CandidateProfile> {
  const res = await fetch(`${API_BASE}/profile`);
  if (!res.ok) throw new Error("Failed to fetch profile");
  return res.json();
}

export async function saveProfile(profile: CandidateProfile): Promise<any> {
  const res = await fetch(`${API_BASE}/profile`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });
  if (!res.ok) throw new Error("Failed to save profile");
  return res.json();
}

export async function uploadCVFile(file: File): Promise<any> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/profile/upload-cv`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Failed to parse and upload CV");
  return res.json();
}

export async function uploadMultipleCVs(files: File[]): Promise<any> {
  const formData = new FormData();
  files.forEach((f) => formData.append("files", f));
  const res = await fetch(`${API_BASE}/profile/upload-multiple-cvs`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Failed to upload and parse multiple CVs");
  return res.json();
}

export async function uploadChatHistory(files: File[]): Promise<any> {
  const formData = new FormData();
  files.forEach((f) => formData.append("files", f));
  const res = await fetch(`${API_BASE}/profile/upload-chat-history`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Failed to upload chat history");
  return res.json();
}

export async function parseGitHub(urlOrUsername: string): Promise<any> {
  const res = await fetch(`${API_BASE}/profile/parse-github`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url_or_username: urlOrUsername }),
  });
  if (!res.ok) throw new Error("Failed to parse GitHub profile");
  return res.json();
}

export async function parseLinkedIn(linkedinUrl: string, rawText?: string): Promise<any> {
  const res = await fetch(`${API_BASE}/profile/parse-linkedin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ linkedin_url: linkedinUrl, raw_text: rawText || "" }),
  });
  if (!res.ok) throw new Error("Failed to parse LinkedIn profile");
  return res.json();
}

export async function uploadLinkedInPDF(file: File): Promise<any> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/profile/upload-linkedin-pdf`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Failed to parse LinkedIn PDF");
  return res.json();
}

export async function parsePersonalWebsite(websiteUrl: string): Promise<any> {
  const res = await fetch(`${API_BASE}/profile/parse-website`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ website_url: websiteUrl }),
  });
  if (!res.ok) throw new Error("Failed to scrape personal website");
  return res.json();
}

export async function synthesizeMasterProfile(payload: {
  cv_sources?: any[];
  chat_sources?: any[];
  github_data?: any;
  linkedin_data?: any;
  website_data?: any;
}): Promise<any> {
  const res = await fetch(`${API_BASE}/profile/synthesize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to synthesize master profile");
  return res.json();
}

export async function downloadDefaultEuropassCV(): Promise<Blob> {
  const res = await fetch(`${API_BASE}/profile/download-europass-cv`);
  if (!res.ok) throw new Error("Failed to generate default Europass CV PDF");
  return res.blob();
}

export async function searchLiveJobs(keyword: string, region: string, maxResults: number = 15): Promise<JobItem[]> {
  const res = await fetch(`${API_BASE}/jobs/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ keyword, region, max_results: maxResults }),
  });
  if (!res.ok) throw new Error("Failed to search jobs");
  const data = await res.json();
  return data.jobs || [];
}

export async function findCompaniesByRole(role: string, region: string, limit: number = 10): Promise<HiringCompanyLead[]> {
  const res = await fetch(`${API_BASE}/hr/by-role`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role, region, limit }),
  });
  if (!res.ok) throw new Error("Failed to find hiring companies");
  const data = await res.json();
  return data.companies || [];
}

export async function searchCompanyHR(company: string, domain?: string, region: string = "GULF"): Promise<any> {
  const res = await fetch(`${API_BASE}/hr/by-company`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ company, domain, region }),
  });
  if (!res.ok) throw new Error("Failed to search company HR");
  return res.json();
}

export async function tailorResume(jobTitle: string, company: string, location: string, jdText: string): Promise<any> {
  const res = await fetch(`${API_BASE}/cv/tailor`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      job_title: jobTitle,
      company: company,
      location: location,
      jd_text: jdText,
    }),
  });
  if (!res.ok) throw new Error("Failed to tailor CV");
  return res.json();
}

export async function downloadEuropassPDF(tailoredResume: any): Promise<Blob> {
  const res = await fetch(`${API_BASE}/cv/generate-pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tailored_resume: tailoredResume }),
  });
  if (!res.ok) throw new Error("Failed to generate Europass PDF");
  return res.blob();
}

export async function draftEmail(jobTitle: string, company: string, hrEmail: string, hrName?: string, context?: string): Promise<any> {
  const res = await fetch(`${API_BASE}/outreach/draft`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      job_title: jobTitle,
      company: company,
      hr_email: hrEmail,
      hr_name: hrName || "Hiring Manager",
      tailored_content: context || "",
    }),
  });
  if (!res.ok) throw new Error("Failed to draft email");
  return res.json();
}

export async function sendEmail(payload: {
  to_email: string;
  subject: string;
  body: string;
  company: string;
  job_title: string;
  location?: string;
  portal_link?: string;
  dry_run?: boolean;
}): Promise<any> {
  const res = await fetch(`${API_BASE}/outreach/send`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || data.message || "Failed to dispatch email");
  }
  return data;
}

export async function fetchApplications(): Promise<{ metrics: any; applications: ApplicationItem[] }> {
  const res = await fetch(`${API_BASE}/tracker/applications`);
  if (!res.ok) throw new Error("Failed to fetch applications");
  return res.json();
}

export async function updateAppStatus(id: number, newStatus: string): Promise<any> {
  const res = await fetch(`${API_BASE}/tracker/update-status`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ application_id: id, new_status: newStatus }),
  });
  if (!res.ok) throw new Error("Failed to update status");
  return res.json();
}

export async function fetchSettings(): Promise<any> {
  const res = await fetch(`${API_BASE}/settings`);
  if (!res.ok) throw new Error("Failed to fetch settings");
  return res.json();
}

export async function saveSettings(settings: Record<string, string>): Promise<any> {
  const res = await fetch(`${API_BASE}/settings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ settings }),
  });
  if (!res.ok) throw new Error("Failed to update settings");
  return res.json();
}

export interface CareerPortalItem {
  id: number;
  name: string;
  portal_url: string;
  region: string;
  country: string;
  industry: string;
  ats_type: string;
  hr_email: string;
  notes: string;
  is_custom: number;
  created_at: string;
}

export async function fetchPortals(region?: string, query?: string): Promise<CareerPortalItem[]> {
  const params = new URLSearchParams();
  if (region && region !== "ALL") params.append("region", region);
  if (query) params.append("query", query);
  const res = await fetch(`${API_BASE}/portals?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch portals");
  const data = await res.json();
  return data.portals || [];
}

export async function addPortal(payload: {
  name: string;
  portal_url: string;
  region: string;
  country: string;
  industry: string;
  ats_type: string;
  hr_email?: string;
  notes?: string;
}): Promise<any> {
  const res = await fetch(`${API_BASE}/portals`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to add portal");
  return res.json();
}

export async function deletePortal(id: number): Promise<any> {
  const res = await fetch(`${API_BASE}/portals/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete portal");
  return res.json();
}
