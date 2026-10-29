"use client";

import React, { useState, useEffect } from "react";
import {
  Building2,
  Search,
  ShieldCheck,
  MapPin,
  ExternalLink,
  Sparkles,
  Send,
  Calendar,
  Mail,
  AlertCircle,
  Users,
  CheckCircle2,
  DollarSign,
  Tag,
  Briefcase,
  Layers,
  GraduationCap,
  X,
  ChevronDown,
  RefreshCw,
  Award,
} from "lucide-react";
import { DubaiJobItem, JobItem } from "../../types";
import { fetchDubaiJobs } from "../../lib/api";

interface DubaiJobHunterViewProps {
  onSelectForTailor: (job: JobItem) => void;
  onSelectForOutreach: (job: JobItem) => void;
  onSelectForRecruiters?: (company: string, jobTitle: string) => void;
}

function formatCleanText(text: string): string {
  if (!text) return "";
  return text
    .replace(/\*{1,3}(.*?)\*{1,3}/g, "$1")
    .replace(/^#{1,6}\s*/gm, "")
    .replace(/\[([^\]]+)\]\([^\)]+\)/g, "$1")
    .replace(/_{1,2}(.*?)_{1,2}/g, "$1")
    .replace(/^\s*[-*•]\s*/gm, "• ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function formatDatePosted(dateStr?: string): string {
  if (!dateStr || dateStr.toLowerCase() === "recently" || dateStr.toLowerCase() === "active") {
    return dateStr || "Recently Listed";
  }
  if (dateStr.includes("ago") || dateStr.includes("Trending") || dateStr.includes("Today") || dateStr.includes("Yesterday")) {
    return dateStr;
  }
  try {
    const d = new Date(dateStr);
    if (!isNaN(d.getTime())) {
      const diffMs = Date.now() - d.getTime();
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      const diffDays = Math.floor(diffHours / 24);
      if (diffHours < 1) return "Just now";
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays === 1) return "Yesterday";
      if (diffDays < 14) return `${diffDays}d ago`;
      return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
    }
  } catch {
    // fallback
  }
  return dateStr;
}

const CATEGORY_TABS = [
  { id: "ALL", label: "All Dubai Roles", icon: Briefcase, count: "High Fit" },
  { id: "BUSINESS_ANALYST", label: "Business Analyst", icon: Layers, count: "High Hireability" },
  { id: "IT_SUPPORT", label: "IT Support & Systems", icon: Award, count: "Overqualified Edge" },
  { id: "DOCUMENT_CONTROLLER", label: "Document Controller", icon: Tag, count: "Technical Edge" },
  { id: "SOFTWARE_DEV", label: "Python & Software Dev", icon: Sparkles, count: "Core Stack" },
  { id: "DATA_ANALYST", label: "Data & Ops Analyst", icon: GraduationCap, count: "Analytics" },
];

const QUICK_DISTRICTS = [
  "All UAE / Dubai",
  "Dubai Media City / Internet City",
  "Downtown / Business Bay",
  "DIFC (FinTech)",
  "JAFZA / Industrial",
  "Abu Dhabi",
];

export default function DubaiJobHunterView({
  onSelectForTailor,
  onSelectForOutreach,
  onSelectForRecruiters,
}: DubaiJobHunterViewProps) {
  const [selectedCategory, setSelectedCategory] = useState("ALL");
  const [keyword, setKeyword] = useState("");
  const [jobs, setJobs] = useState<DubaiJobItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [activeModalJob, setActiveModalJob] = useState<DubaiJobItem | null>(null);
  const [selectedDistrict, setSelectedDistrict] = useState("All UAE / Dubai");

  useEffect(() => {
    loadJobs("", "ALL");
  }, []);

  const loadJobs = async (kw: string = keyword, cat: string = selectedCategory) => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await fetchDubaiJobs(kw, cat, 50);
      setJobs(data.jobs || []);
    } catch (err: any) {
      console.error("Error loading Dubai jobs:", err);
      setErrorMsg(err.message || "Failed to load Dubai jobs");
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryChange = (catId: string) => {
    setSelectedCategory(catId);
    loadJobs(keyword, catId);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadJobs(keyword, selectedCategory);
  };

  const handleTailorBridge = (job: DubaiJobItem) => {
    const applyLink = job.apply_url || job.portal || "";
    const jobItem: JobItem = {
      id: job.id,
      job_title: job.job_title,
      company: job.company,
      location: job.location,
      description: job.description,
      full_description: job.description,
      job_url: applyLink,
      portal: applyLink,
      salary: job.salary,
      hr_email: job.hr_email || undefined,
      fit_analysis: {
        match_score: job.match_score || 92,
        is_engineering: true,
        geo_eligible: true,
        matched_skills: job.tags || ["Business Analysis", "Systems", "Python"],
        missing_tech: [],
        summary: `Strong Dubai candidate match. Engineering foundation from Moratuwa provides exceptional hireability for ${job.job_title} at ${job.company}.`,
      },
    };
    onSelectForTailor(jobItem);
  };

  const handleOutreachBridge = (job: DubaiJobItem) => {
    const applyLink = job.apply_url || job.portal || "";
    const jobItem: JobItem = {
      id: job.id,
      job_title: job.job_title,
      company: job.company,
      location: job.location,
      description: job.description,
      full_description: job.description,
      job_url: applyLink,
      portal: applyLink,
      salary: job.salary,
      hr_email: job.hr_email || undefined,
    };
    onSelectForOutreach(jobItem);
  };

  const getCategoryColor = (cat: string) => {
    switch (cat) {
      case "BUSINESS_ANALYST":
        return "bg-[#805ad5]/20 text-[#d6bcfa] border-[#805ad5]/40";
      case "IT_SUPPORT":
        return "bg-[#3182ce]/20 text-[#bee3f8] border-[#3182ce]/40";
      case "DOCUMENT_CONTROLLER":
        return "bg-[#dd6b20]/20 text-[#fbd38d] border-[#dd6b20]/40";
      case "SOFTWARE_DEV":
        return "bg-[#005047]/30 text-[#4cd7f6] border-[#00a389]/40";
      case "DATA_ANALYST":
        return "bg-[#4edea3]/10 text-[#4edea3] border-[#4edea3]/30";
      default:
        return "bg-[#292931] text-[#bcc9cd] border-[#3d494c]/40";
    }
  };

  const filteredJobs = jobs.filter((j) => {
    if (selectedDistrict === "All UAE / Dubai") return true;
    if (selectedDistrict.includes("Media City") && (j.location.includes("Media City") || j.location.includes("Internet City"))) return true;
    if (selectedDistrict.includes("Business Bay") && (j.location.includes("Business Bay") || j.location.includes("Downtown"))) return true;
    if (selectedDistrict.includes("DIFC") && j.location.includes("DIFC")) return true;
    if (selectedDistrict.includes("JAFZA") && j.location.includes("JAFZA")) return true;
    if (selectedDistrict.includes("Abu Dhabi") && j.location.includes("Abu Dhabi")) return true;
    return true;
  });

  return (
    <div className="flex flex-col gap-5 p-6 max-w-7xl mx-auto">
      {/* Search Header Banner */}
      <div className="p-5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-[20px] font-semibold text-[#e3e1ec] tracking-tight flex items-center gap-2">
              <Building2 className="w-5 h-5 text-[#4cd7f6]" />
              Dubai &amp; UAE Career Hunter
              <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-[#005047]/30 border border-[#00a389]/40 text-[#4cd7f6] uppercase tracking-wider font-semibold">
                Dubai • Abu Dhabi • Sharjah
              </span>
            </h1>
            <p className="text-[13px] text-[#bcc9cd] mt-1">
              Dedicated engine for Dubai &amp; UAE corporate openings. Tailored for Business Analysts, IT Support, Document Controllers, and Software Engineers where your Moratuwa engineering credentials offer strong analytical overqualification and competitive standing.
            </p>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#005047]/20 border border-[#00a389]/30 text-[#4cd7f6] text-[11px] font-mono">
              <GraduationCap className="w-3.5 h-3.5" />
              <span>Overqualified Advantage Active</span>
            </div>
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#93000a]/20 border border-[#93000a]/40 text-[#ffb4ab] text-[11px] font-mono">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Strict Israel Exclusion</span>
            </div>
          </div>
        </div>

        {/* Category Filter Pills */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 pt-1 no-scrollbar">
          {CATEGORY_TABS.map((cat) => {
            const Icon = cat.icon;
            const isSelected = selectedCategory === cat.id;
            return (
              <button
                key={cat.id}
                onClick={() => handleCategoryChange(cat.id)}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-medium border transition-all whitespace-nowrap active:scale-[0.98] ${
                  isSelected
                    ? "bg-[#4cd7f6] text-[#003640] border-[#4cd7f6] font-semibold shadow-md cyan-glow"
                    : "bg-[#1a1b22] text-[#bcc9cd] border-[#3d494c]/40 hover:text-[#e3e1ec] hover:border-[#4cd7f6]/50"
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isSelected ? "text-[#003640]" : "text-[#4cd7f6]"}`} />
                <span>{cat.label}</span>
                <span
                  className={`text-[10px] font-mono px-1.5 py-0.2 rounded ${
                    isSelected ? "bg-[#003640]/20 text-[#003640]" : "bg-[#292931] text-[#869397]"
                  }`}
                >
                  {cat.count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Search Controls Row */}
        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 md:grid-cols-12 gap-3 pt-1">
          {/* Keyword Search */}
          <div className="md:col-span-8 relative">
            <Search className="w-4 h-4 text-[#879396] absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="Search by skill, tools (Aconex, Power BI, SQL, Python, ITIL, Jira, EDMS, ERP)..."
              className="w-full pl-10 pr-4 py-2.5 bg-[#1a1b22] border border-[#3d494c]/40 rounded-lg text-sm text-[#e3e1ec] placeholder-[#879396] focus:outline-none focus:border-[#4cd7f6]"
            />
          </div>

          {/* Search CTA */}
          <div className="md:col-span-4 flex items-center gap-2">
            <button
              type="submit"
              className="flex-1 px-4 py-2.5 rounded-lg bg-[#4cd7f6] text-[#003640] font-semibold text-xs hover:bg-white transition-all flex items-center justify-center gap-1.5 cyan-glow"
            >
              <Search className="w-3.5 h-3.5" />
              <span>Search Dubai Jobs</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setKeyword("");
                loadJobs("", selectedCategory);
              }}
              title="Reset Search"
              className="p-2.5 rounded-lg bg-[#1a1b22] border border-[#3d494c]/40 text-[#bcc9cd] hover:text-[#e3e1ec] transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </form>

        {/* District Quick Chips */}
        <div className="flex items-center gap-2 flex-wrap text-xs pt-1 border-t border-[#3d494c]/20">
          <span className="text-[#879396] text-[11px] font-mono">Hubs:</span>
          {QUICK_DISTRICTS.map((d) => (
            <button
              key={d}
              onClick={() => setSelectedDistrict(d)}
              className={`px-2 py-0.5 rounded text-[11px] font-mono border transition-all ${
                selectedDistrict === d
                  ? "bg-[#4cd7f6]/15 border-[#4cd7f6]/50 text-[#4cd7f6]"
                  : "bg-[#14151f] border-[#3d494c]/30 text-[#879396] hover:text-[#e3e1ec]"
              }`}
            >
              {d}
            </button>
          ))}
        </div>
      </div>

      {/* Results Header */}
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-[#e3e1ec]">
            {loading ? "Scanning Dubai & UAE corporate channels..." : `${filteredJobs.length} Dubai Vacancies Available`}
          </span>
          {keyword && <span className="text-xs text-[#879396]">matching "{keyword}"</span>}
        </div>
        <div className="text-xs text-[#879396] font-mono">
          Emaar • Emirates • Careem • Noon • Aster • DAMAC • Sobha • Talabat • Petrofac
        </div>
      </div>

      {/* Error alert */}
      {errorMsg && (
        <div className="p-3 rounded-lg bg-[#93000a]/20 border border-[#93000a]/40 text-[#ffb4ab] text-xs font-mono">
          {errorMsg}
        </div>
      )}

      {/* Jobs List */}
      <div className="flex flex-col gap-3">
        {filteredJobs.map((job) => {
          const applyLink = job.apply_url || job.portal || "";
          const hasEmail = Boolean(job.hr_email && job.hr_email.includes("@"));

          return (
            <div
              key={job.id}
              className="p-5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 hover:border-[#4cd7f6]/40 transition-all flex flex-col gap-3.5 specular-border"
            >
              {/* Top Row: Title, Location, Badges, Match Score */}
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                <div className="flex flex-col gap-1.5 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3
                      onClick={() => setActiveModalJob(job)}
                      className="text-base font-semibold text-[#e3e1ec] tracking-tight hover:text-[#4cd7f6] transition-colors cursor-pointer"
                    >
                      {job.job_title}
                    </h3>

                    {/* Location Badge */}
                    <span className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded-full bg-[#005047]/20 border border-[#00a389]/40 text-[#4cd7f6]">
                      <MapPin className="w-3 h-3" />
                      <span>{job.location}</span>
                    </span>

                    {/* Category Badge */}
                    <span
                      className={`inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-full border ${getCategoryColor(
                        job.category
                      )}`}
                    >
                      {job.category.replace("_", " ")}
                    </span>

                    {/* Salary Pill in AED */}
                    {job.salary && (
                      <span className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded-md bg-[#292931] border border-[#3d494c]/50 text-[#81e6d9]">
                        <DollarSign className="w-3 h-3 text-[#4cd7f6]" />
                        <span>{job.salary}</span>
                      </span>
                    )}
                  </div>

                  {/* Company & Meta info */}
                  <div className="flex items-center gap-3 text-xs text-[#bcc9cd] flex-wrap">
                    <span className="flex items-center gap-1 font-semibold text-[#e3e1ec]">
                      <Building2 className="w-3.5 h-3.5 text-[#4cd7f6]" />
                      {job.company}
                    </span>
                    <span className="inline-flex items-center gap-1 text-[11px] font-mono text-[#bcc9cd] bg-[#1a1b22] px-2 py-0.5 rounded border border-[#3d494c]/40">
                      <Calendar className="w-3 h-3 text-[#4cd7f6]" />
                      <span>Posted: {formatDatePosted(job.date_posted || job.posted_at)}</span>
                    </span>
                    <span className="text-[11px] text-[#869397] font-mono">
                      Source: {job.source}
                    </span>
                  </div>
                </div>

                {/* Match Score Badge */}
                <div className="flex items-center gap-2 self-start">
                  <div className="flex flex-col items-end">
                    <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[#005047]/30 border border-[#00a389]/40 text-[#4cd7f6]">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span className="text-xs font-mono font-bold">
                        {job.match_score || 92}% MATCH
                      </span>
                    </div>
                    <span className="text-[10px] text-[#4edea3] font-mono mt-0.5 font-medium">
                      High Hireability Edge
                    </span>
                  </div>
                </div>
              </div>

              {/* Overqualification Insight Box */}
              {job.overqualification_insight && (
                <div className="p-2.5 rounded-lg bg-[#14151f] border border-[#3d494c]/30 flex items-start gap-2 text-[12px] text-[#bcc9cd]">
                  <GraduationCap className="w-4 h-4 text-[#4cd7f6] shrink-0 mt-0.5" />
                  <div className="leading-snug">
                    <strong className="text-[#4cd7f6] font-mono text-[11px] uppercase mr-1">
                      Candidate Advantage:
                    </strong>
                    {job.overqualification_insight}
                  </div>
                </div>
              )}

              {/* Short description */}
              <div className="text-[12px] text-[#bcc9cd] line-clamp-2 leading-relaxed">
                {formatCleanText(job.description)}
              </div>

              {/* Tags */}
              {job.tags && job.tags.length > 0 && (
                <div className="flex items-center gap-1.5 flex-wrap">
                  {job.tags.map((t, idx) => (
                    <span
                      key={idx}
                      className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1a1b22] border border-[#3d494c]/40 text-[#bcc9cd]"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              )}

              {/* Action Buttons Row */}
              <div className="pt-2 border-t border-[#3d494c]/20 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  {hasEmail ? (
                    <span className="inline-flex items-center gap-1 text-[11px] font-mono text-[#4edea3] bg-[#4edea3]/10 px-2 py-0.5 rounded border border-[#4edea3]/30">
                      <Mail className="w-3 h-3 text-[#4edea3]" />
                      <span>HR: {job.hr_email}</span>
                    </span>
                  ) : (
                    <span className="text-[11px] font-mono text-[#879396] flex items-center gap-1">
                      <AlertCircle className="w-3 h-3 text-[#f59e0b]" />
                      <span>Corporate Portal Application</span>
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2 flex-wrap">
                  <button
                    onClick={() => handleTailorBridge(job)}
                    className="px-3 py-1.5 rounded-lg bg-[#1a1b22] border border-[#3d494c]/40 hover:border-[#4cd7f6] text-[#e3e1ec] hover:text-[#4cd7f6] text-xs flex items-center gap-1.5 transition-all"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-[#4cd7f6]" />
                    <span>Tailor CV</span>
                  </button>

                  {hasEmail && (
                    <button
                      onClick={() => handleOutreachBridge(job)}
                      className="px-3 py-1.5 rounded-lg bg-[#4cd7f6] text-[#003640] font-semibold text-xs hover:bg-white transition-all flex items-center gap-1.5 cyan-glow"
                    >
                      <Send className="w-3.5 h-3.5" />
                      <span>Outreach Email</span>
                    </button>
                  )}

                  {applyLink && (
                    <a
                      href={applyLink}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
                        !hasEmail
                          ? "bg-[#4cd7f6] text-[#003640] hover:bg-white cyan-glow"
                          : "bg-[#292931] border border-[#3d494c]/40 text-[#bcc9cd] hover:text-white"
                      }`}
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      <span>Apply on Portal ↗</span>
                    </a>
                  )}

                  {onSelectForRecruiters && (
                    <button
                      onClick={() => onSelectForRecruiters(job.company, job.job_title)}
                      className="px-2.5 py-1.5 rounded-lg bg-[#1a1b22] border border-[#3d494c]/30 hover:border-[#bcc9cd] text-[#bcc9cd] hover:text-white text-xs flex items-center gap-1 transition-all"
                    >
                      <Users className="w-3 h-3 text-[#4cd7f6]" />
                      <span>Recruiters</span>
                    </button>
                  )}

                  <button
                    onClick={() => setActiveModalJob(job)}
                    className="px-2.5 py-1.5 rounded-lg bg-[#292931] text-[#bcc9cd] hover:text-white text-xs flex items-center gap-1 transition-all"
                  >
                    <span>Details</span>
                    <ChevronDown className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal View for Full JD */}
      {activeModalJob && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
          <div className="w-full max-w-3xl rounded-2xl bg-[#0d0e15] border border-[#3d494c]/50 shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
            {/* Modal Header */}
            <div className="p-6 border-b border-[#3d494c]/30 flex items-start justify-between gap-4 bg-[#12131a]">
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-[#005047]/30 border border-[#00a389]/40 text-[#4cd7f6]">
                    📍 {activeModalJob.location}
                  </span>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#005047]/30 border border-[#00a389]/40 text-[#4cd7f6] font-bold">
                    ✓ {activeModalJob.match_score || 92}% ATS FIT
                  </span>
                </div>
                <h2 className="text-xl font-bold text-[#e3e1ec] tracking-tight">
                  {activeModalJob.job_title}
                </h2>
                <div className="flex items-center gap-3 text-xs text-[#bcc9cd] flex-wrap mt-1">
                  <span className="font-semibold text-[#e3e1ec] flex items-center gap-1">
                    <Building2 className="w-3.5 h-3.5 text-[#4cd7f6]" />
                    {activeModalJob.company}
                  </span>
                  {activeModalJob.salary && (
                    <span className="text-[#81e6d9] font-mono">
                      💰 {activeModalJob.salary}
                    </span>
                  )}
                  <span className="inline-flex items-center gap-1 text-[11px] font-mono text-[#bcc9cd] bg-[#1a1b22] px-2.5 py-0.5 rounded border border-[#3d494c]/40">
                    <Calendar className="w-3.5 h-3.5 text-[#4cd7f6]" />
                    <span>Posted: {formatDatePosted(activeModalJob.date_posted || activeModalJob.posted_at)}</span>
                  </span>
                </div>
              </div>

              <button
                onClick={() => setActiveModalJob(null)}
                className="p-1.5 rounded-lg text-[#869296] hover:text-[#e3e1ec] hover:bg-[#1a1b22] transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Quick Actions Bar */}
            <div className="flex items-center justify-between px-6 py-3 bg-[#1a1b22] border-b border-[#3d494c]/20 flex-wrap gap-2">
              <div className="flex items-center gap-2 flex-wrap">
                {activeModalJob.apply_url || activeModalJob.portal ? (
                  <a
                    href={activeModalJob.apply_url || activeModalJob.portal}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-gradient-to-r from-[#00687a] to-[#4cd7f6] text-[#003640] font-bold text-xs hover:brightness-110 transition-all shadow-md"
                  >
                    <ExternalLink className="w-4 h-4 text-[#003640]" />
                    <span>Apply via Official UAE Portal ↗</span>
                  </a>
                ) : null}

                <button
                  onClick={() => {
                    handleTailorBridge(activeModalJob);
                    setActiveModalJob(null);
                  }}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-[#292931] border border-[#4cd7f6]/40 hover:border-[#4cd7f6] text-xs font-semibold text-[#4cd7f6] transition-all"
                >
                  <Sparkles className="w-3.5 h-3.5 text-[#4cd7f6]" />
                  <span>Tailor CV with this JD</span>
                </button>

                {activeModalJob.hr_email && (
                  <button
                    onClick={() => {
                      handleOutreachBridge(activeModalJob);
                      setActiveModalJob(null);
                    }}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-[#4cd7f6] text-[#003640] font-semibold text-xs hover:bg-white transition-all cyan-glow"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>Outreach Email</span>
                  </button>
                )}
              </div>
            </div>

            {/* Modal Body */}
            <div className="flex-1 p-6 overflow-y-auto max-h-[55vh] text-[13px] text-[#e3e1ec] leading-relaxed whitespace-pre-wrap font-sans bg-[#0d0e15]">
              {activeModalJob.overqualification_insight && (
                <div className="mb-4 p-3.5 rounded-xl bg-[#005047]/20 border border-[#00a389]/40 text-[#e3e1ec]">
                  <div className="font-semibold text-[#4cd7f6] text-xs font-mono uppercase mb-1 flex items-center gap-1.5">
                    <GraduationCap className="w-4 h-4 text-[#4cd7f6]" />
                    <span>Moratuwa Engineering Graduate Advantage:</span>
                  </div>
                  <p className="text-xs text-[#bcc9cd] leading-relaxed">
                    {activeModalJob.overqualification_insight}
                  </p>
                </div>
              )}
              {formatCleanText(activeModalJob.description)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
