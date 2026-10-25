"use client";

import React, { useState, useEffect } from "react";
import {
  Laptop,
  Search,
  ShieldCheck,
  Globe,
  ExternalLink,
  Sparkles,
  Send,
  Building2,
  DollarSign,
  Tag,
  CheckCircle2,
  Users,
  RefreshCw,
  Zap,
  X,
  FileText,
  Calendar,
  AlertCircle,
} from "lucide-react";
import { GlobalRemoteJob, JobItem } from "../../types";
import { fetchGlobalRemoteJobs } from "../../lib/api";

interface GlobalRemoteJobsViewProps {
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

const QUICK_KEYWORDS = [
  "Python",
  "Backend",
  "AI / Machine Learning",
  "LLM Engineer",
  "FastAPI",
  "Full Stack",
  "Distributed Systems",
  "Data Engineer",
];

const SOURCE_FILTERS = [
  { id: "ALL", label: "All Sources" },
  { id: "ATS", label: "Direct ATS (Greenhouse/Ashby/Lever)" },
  { id: "REMOTEOK", label: "RemoteOK" },
  { id: "REMOTIVE", label: "Remotive" },
  { id: "HIMALAYAS", label: "Himalayas" },
  { id: "JOBICY", label: "Jobicy" },
  { id: "WWR", label: "WeWorkRemotely" },
  { id: "ARBEITNOW", label: "Arbeitnow" },
];

export default function GlobalRemoteJobsView({
  onSelectForTailor,
  onSelectForOutreach,
  onSelectForRecruiters,
}: GlobalRemoteJobsViewProps) {
  const [keyword, setKeyword] = useState("Python");
  const [sourceFilter, setSourceFilter] = useState("ALL");
  const [worldwideOnly, setWorldwideOnly] = useState(true);
  const [limit, setLimit] = useState(60);
  const [jobs, setJobs] = useState<GlobalRemoteJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [activeModalJob, setActiveModalJob] = useState<GlobalRemoteJob | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Auto-load initial batch on mount
  useEffect(() => {
    handleSearch("Python", "ALL", true);
  }, []);

  const handleSearch = async (
    kw: string = keyword,
    src: string = sourceFilter,
    worldwide: boolean = worldwideOnly
  ) => {
    setLoading(true);
    setHasSearched(true);
    setErrorMsg(null);
    setActiveModalJob(null);

    try {
      const data = await fetchGlobalRemoteJobs(kw, worldwide, limit, src);
      setJobs(data.jobs || []);
    } catch (err: any) {
      console.error("Failed to load remote jobs:", err);
      setErrorMsg(err.message || "Failed to fetch remote jobs");
    } finally {
      setLoading(false);
    }
  };

  const handleTailorBridge = (job: GlobalRemoteJob) => {
    const applyLink = job.apply_url || job.portal || job.job_url || "";
    const jobItem: JobItem = {
      id: job.id,
      job_title: job.job_title,
      company: job.company,
      location: job.location || "Remote (Worldwide)",
      description: job.description,
      full_description: job.description,
      job_url: applyLink,
      portal: applyLink,
      salary: job.salary,
      fit_analysis: {
        match_score: job.match_score || 85,
        is_engineering: true,
        geo_eligible: true,
        matched_skills: job.tags || ["Python", "Backend"],
        missing_tech: [],
        summary: `Strong worldwide remote match for ${job.job_title} at ${job.company}.`,
      },
    };
    onSelectForTailor(jobItem);
  };

  const handleOutreachBridge = (job: GlobalRemoteJob) => {
    const applyLink = job.apply_url || job.portal || job.job_url || "";
    const jobItem: JobItem = {
      id: job.id,
      job_title: job.job_title,
      company: job.company,
      location: job.location || "Remote (Worldwide)",
      description: job.description,
      full_description: job.description,
      job_url: applyLink,
      portal: applyLink,
      salary: job.salary,
    };
    onSelectForOutreach(jobItem);
  };

  const getSourceBadgeColor = (source: string, type: string) => {
    if (type === "ats" || source.includes("Greenhouse") || source.includes("Ashby") || source.includes("Lever")) {
      return "bg-[#805ad5]/20 text-[#d6bcfa] border-[#805ad5]/40";
    }
    if (source.includes("RemoteOK")) {
      return "bg-[#e53e3e]/20 text-[#feb2b2] border-[#e53e3e]/40";
    }
    if (source.includes("Remotive")) {
      return "bg-[#319795]/20 text-[#81e6d9] border-[#319795]/40";
    }
    if (source.includes("Himalayas")) {
      return "bg-[#3182ce]/20 text-[#bee3f8] border-[#3182ce]/40";
    }
    if (source.includes("Jobicy")) {
      return "bg-[#dd6b20]/20 text-[#fbd38d] border-[#dd6b20]/40";
    }
    if (source.includes("WeWorkRemotely") || source.includes("WWR")) {
      return "bg-[#d69e2e]/20 text-[#fefcbf] border-[#d69e2e]/40";
    }
    return "bg-[#292931] text-[#bcc9cd] border-[#3d494c]/40";
  };

  return (
    <div className="flex flex-col gap-5 p-6 max-w-7xl mx-auto">
      {/* Search Header Banner */}
      <div className="p-5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-[20px] font-semibold text-[#e3e1ec] tracking-tight flex items-center gap-2">
              <Laptop className="w-5 h-5 text-[#4cd7f6]" />
              Global Remote Jobs
              <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-[#005047]/30 border border-[#00a389]/40 text-[#4cd7f6] uppercase tracking-wider font-semibold">
                Worldwide Only
              </span>
            </h1>
            <p className="text-[13px] text-[#bcc9cd] mt-1">
              Curated 100% remote positions open to engineers worldwide — strictly eliminating US/EU/Canada geo-restrictions.
              Direct unauthenticated ATS boards &amp; remote feeds with direct application links.
            </p>
          </div>

          {/* Badges container */}
          <div className="flex items-center gap-2 flex-wrap">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#005047]/20 border border-[#00a389]/30 text-[#4cd7f6] text-[11px] font-mono">
              <Globe className="w-3.5 h-3.5" />
              <span>Work From Anywhere</span>
            </div>
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#93000a]/20 border border-[#93000a]/40 text-[#ffb4ab] text-[11px] font-mono">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Israel Exclusion: ENFORCED</span>
            </div>
          </div>
        </div>

        {/* Search Controls */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3 pt-2">
          {/* Keyword Search */}
          <div className="md:col-span-5 relative">
            <Search className="w-4 h-4 text-[#879396] absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch(keyword, sourceFilter, worldwideOnly)}
              placeholder="e.g. Python, AI/ML, FastAPI, Backend..."
              className="w-full pl-10 pr-4 py-2.5 bg-[#1a1b22] border border-[#3d494c]/40 rounded-lg text-sm text-[#e3e1ec] placeholder-[#879396] focus:outline-none focus:border-[#4cd7f6]"
            />
          </div>

          {/* Source Dropdown */}
          <div className="md:col-span-3">
            <select
              value={sourceFilter}
              onChange={(e) => {
                const val = e.target.value;
                setSourceFilter(val);
                handleSearch(keyword, val, worldwideOnly);
              }}
              className="w-full px-3 py-2.5 bg-[#1a1b22] border border-[#3d494c]/40 rounded-lg text-sm text-[#e3e1ec] focus:outline-none focus:border-[#4cd7f6]"
            >
              {SOURCE_FILTERS.map((s) => (
                <option key={s.id} value={s.id} className="bg-[#1a1b22] text-[#e3e1ec]">
                  {s.label}
                </option>
              ))}
            </select>
          </div>

          {/* Limit */}
          <div className="md:col-span-2">
            <select
              value={limit}
              onChange={(e) => {
                const val = Number(e.target.value);
                setLimit(val);
              }}
              className="w-full px-3 py-2.5 bg-[#1a1b22] border border-[#3d494c]/40 rounded-lg text-sm text-[#e3e1ec] focus:outline-none focus:border-[#4cd7f6]"
            >
              <option value={30} className="bg-[#1a1b22] text-[#e3e1ec]">30 jobs</option>
              <option value={60} className="bg-[#1a1b22] text-[#e3e1ec]">60 jobs</option>
              <option value={100} className="bg-[#1a1b22] text-[#e3e1ec]">100 jobs</option>
            </select>
          </div>

          {/* Search Button */}
          <div className="md:col-span-2">
            <button
              onClick={() => handleSearch(keyword, sourceFilter, worldwideOnly)}
              disabled={loading}
              className="w-full py-2.5 px-4 bg-gradient-to-r from-[#00687a] to-[#4cd7f6] hover:brightness-110 active:scale-[0.98] text-[#003640] font-semibold text-sm rounded-lg transition-all flex items-center justify-center gap-2 shadow-sm disabled:opacity-50"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin text-[#003640]" />
                  <span>Searching...</span>
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4 text-[#003640]" />
                  <span>Search Jobs</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Quick Pills & Worldwide Filter Toggle */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1 border-t border-[#3d494c]/20">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[11px] font-mono text-[#879396] mr-1">Quick:</span>
            {QUICK_KEYWORDS.map((kw) => (
              <button
                key={kw}
                onClick={() => {
                  setKeyword(kw);
                  handleSearch(kw, sourceFilter, worldwideOnly);
                }}
                className={`text-[11px] px-2.5 py-1 rounded-md border transition-all ${
                  keyword.toLowerCase() === kw.toLowerCase()
                    ? "bg-[#4cd7f6]/20 border-[#4cd7f6]/60 text-[#4cd7f6] font-semibold"
                    : "bg-[#1a1b22] border-[#3d494c]/40 text-[#bcc9cd] hover:border-[#4cd7f6]/40 hover:text-[#e3e1ec]"
                }`}
              >
                {kw}
              </button>
            ))}
          </div>

          {/* Worldwide Only Toggle */}
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={worldwideOnly}
              onChange={(e) => {
                const checked = e.target.checked;
                setWorldwideOnly(checked);
                handleSearch(keyword, sourceFilter, checked);
              }}
              className="w-4 h-4 accent-[#4cd7f6] rounded cursor-pointer"
            />
            <span className="text-[12px] font-medium text-[#e3e1ec]">
              Worldwide Only (Discard US/EU/Canada restricted)
            </span>
          </label>
        </div>
      </div>

      {/* Results Header */}
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-[#e3e1ec]">
            {loading ? "Scanning feeds & ATS..." : `${jobs.length} Verified Worldwide Jobs Found`}
          </span>
          {keyword && (
            <span className="text-xs text-[#879396]">for "{keyword}"</span>
          )}
        </div>
        <div className="text-xs text-[#879396]">
          Feed sources: Greenhouse • Ashby • Lever • RemoteOK • Remotive • Himalayas • Jobicy • WWR • Arbeitnow
        </div>
      </div>

      {/* Error display */}
      {errorMsg && (
        <div className="p-3 rounded-lg bg-[#93000a]/20 border border-[#93000a]/40 text-[#ffb4ab] text-xs font-mono">
          {errorMsg}
        </div>
      )}

      {/* Jobs Grid / List */}
      <div className="flex flex-col gap-3">
        {jobs.map((job) => {
          const applyLink = job.apply_url || job.portal || job.job_url || "";

          return (
            <div
              key={job.id}
              className="p-4 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 hover:border-[#4cd7f6]/40 transition-all flex flex-col gap-3 specular-border"
            >
              {/* Top row: Title, Company, Badges, Match Score */}
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                <div className="flex flex-col gap-1.5 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3
                      onClick={() => setActiveModalJob(job)}
                      className="text-base font-semibold text-[#e3e1ec] tracking-tight hover:text-[#4cd7f6] transition-colors cursor-pointer"
                    >
                      {job.job_title}
                    </h3>

                    {/* Worldwide Badge */}
                    <span className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded-full bg-[#005047]/20 border border-[#00a389]/40 text-[#4cd7f6]">
                      <Globe className="w-3 h-3" />
                      <span>{job.location || "Worldwide"}</span>
                    </span>

                    {/* Source Badge */}
                    <span
                      className={`inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-full border ${getSourceBadgeColor(
                        job.source,
                        job.source_type
                      )}`}
                    >
                      {job.source}
                    </span>

                    {/* Salary badge if available */}
                    {job.salary && (
                      <span className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded-md bg-[#292931] border border-[#3d494c]/50 text-[#81e6d9]">
                        <DollarSign className="w-3 h-3 text-[#4cd7f6]" />
                        <span>{job.salary}</span>
                      </span>
                    )}
                  </div>

                  {/* Company & Meta info */}
                  <div className="flex items-center gap-4 text-xs text-[#bcc9cd] flex-wrap">
                    <span className="flex items-center gap-1 font-medium text-[#e3e1ec]">
                      <Building2 className="w-3.5 h-3.5 text-[#4cd7f6]" />
                      {job.company}
                    </span>
                    {job.posted_at && (
                      <span className="text-[#879396]">
                        Posted: {job.posted_at}
                      </span>
                    )}
                  </div>
                </div>

                {/* Match Score Badge */}
                <div className="flex items-center gap-2 self-start">
                  <div className="flex flex-col items-end">
                    <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[#005047]/30 border border-[#00a389]/40 text-[#4cd7f6]">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span className="text-xs font-mono font-bold">
                        {job.match_score || 85}% ATS FIT
                      </span>
                    </div>
                    <span className="text-[10px] text-[#879396] mt-0.5">
                      Moratuwa Stack Match
                    </span>
                  </div>
                </div>
              </div>

              {/* Tags */}
              {job.tags && job.tags.length > 0 && (
                <div className="flex items-center gap-1.5 flex-wrap">
                  {job.tags.slice(0, 7).map((t, idx) => (
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
              <div className="flex items-center justify-between gap-2 pt-2 border-t border-[#3d494c]/20 flex-wrap">
                <div className="flex items-center gap-2 flex-wrap">
                  {/* Direct Official Apply Link - PROMINENT */}
                  {applyLink ? (
                    <a
                      href={applyLink}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#4cd7f6]/15 border border-[#4cd7f6]/60 hover:bg-[#4cd7f6]/25 text-xs font-semibold text-[#4cd7f6] transition-all shadow-sm"
                    >
                      <ExternalLink className="w-3.5 h-3.5 text-[#4cd7f6]" />
                      <span>Official Job Link ↗</span>
                    </a>
                  ) : (
                    <span className="text-xs text-[#869296] italic px-2 py-1">
                      Direct application on company board
                    </span>
                  )}

                  {/* Tailor CV */}
                  <button
                    onClick={() => handleTailorBridge(job)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#1a1b22] border border-[#4cd7f6]/40 hover:border-[#4cd7f6] hover:bg-[#4cd7f6]/10 text-xs font-medium text-[#4cd7f6] transition-all"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-[#4cd7f6]" />
                    <span>Tailor CV</span>
                  </button>

                  {/* Cold Outreach */}
                  <button
                    onClick={() => handleOutreachBridge(job)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#1a1b22] border border-[#3d494c]/50 hover:border-[#bcc9cd] hover:bg-[#292931] text-xs font-medium text-[#e3e1ec] transition-all"
                  >
                    <Send className="w-3.5 h-3.5 text-[#4cd7f6]" />
                    <span>Outreach Pitch</span>
                  </button>

                  {/* Find Recruiters */}
                  {onSelectForRecruiters && (
                    <button
                      onClick={() => onSelectForRecruiters(job.company, job.job_title)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#1a1b22] border border-[#3d494c]/50 hover:border-[#bcc9cd] hover:bg-[#292931] text-xs font-medium text-[#bcc9cd] hover:text-[#e3e1ec] transition-all"
                    >
                      <Users className="w-3.5 h-3.5 text-[#4cd7f6]" />
                      <span>Find Recruiters</span>
                    </button>
                  )}
                </div>

                {/* View Description Dialog Trigger */}
                <button
                  onClick={() => setActiveModalJob(job)}
                  className="flex items-center gap-1.5 text-xs text-[#bcc9cd] hover:text-[#4cd7f6] transition-colors py-1 px-2.5 rounded-md hover:bg-[#1a1b22]"
                >
                  <FileText className="w-3.5 h-3.5 text-[#4cd7f6]" />
                  <span>View Description</span>
                </button>
              </div>
            </div>
          );
        })}

        {/* Empty state */}
        {!loading && jobs.length === 0 && hasSearched && (
          <div className="p-12 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 flex flex-col items-center justify-center text-center gap-3">
            <Globe className="w-8 h-8 text-[#879396]" />
            <div className="text-sm font-semibold text-[#e3e1ec]">
              No remote jobs found matching your filters
            </div>
            <p className="text-xs text-[#879396] max-w-md">
              Try searching with broader keywords like "Python", "Engineer", or selecting "All Sources".
            </p>
          </div>
        )}
      </div>

      {/* User-Friendly Centered Description Modal with Blurred Backdrop */}
      {activeModalJob && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200"
          onClick={() => setActiveModalJob(null)}
        >
          <div
            className="relative w-full max-w-3xl max-h-[88vh] bg-[#0d0e15] border border-[#3d494c]/60 rounded-2xl shadow-2xl flex flex-col overflow-hidden specular-border"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-start justify-between p-5 border-b border-[#3d494c]/30 bg-[#14151e]">
              <div className="flex flex-col gap-1.5 pr-4">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-[#005047]/30 border border-[#00a389]/40 text-[#4cd7f6]">
                    🌐 {activeModalJob.location || "Worldwide"}
                  </span>
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${getSourceBadgeColor(
                      activeModalJob.source,
                      activeModalJob.source_type
                    )}`}
                  >
                    {activeModalJob.source}
                  </span>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#005047]/30 border border-[#00a389]/40 text-[#4cd7f6] font-bold">
                    ✓ {activeModalJob.match_score || 85}% ATS FIT
                  </span>
                </div>
                <h2 className="text-lg font-bold text-[#e3e1ec] tracking-tight">
                  {activeModalJob.job_title}
                </h2>
                <div className="flex items-center gap-3 text-xs text-[#bcc9cd]">
                  <span className="font-semibold text-[#e3e1ec] flex items-center gap-1">
                    <Building2 className="w-3.5 h-3.5 text-[#4cd7f6]" />
                    {activeModalJob.company}
                  </span>
                  {activeModalJob.salary && (
                    <span className="text-[#81e6d9] font-mono">
                      💰 {activeModalJob.salary}
                    </span>
                  )}
                  {activeModalJob.posted_at && (
                    <span className="text-[#879396]">
                      📅 {activeModalJob.posted_at}
                    </span>
                  )}
                </div>
              </div>

              <button
                onClick={() => setActiveModalJob(null)}
                className="p-1.5 rounded-lg text-[#869296] hover:text-[#e3e1ec] hover:bg-[#1a1b22] transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Quick Action Bar at top of modal */}
            <div className="flex items-center justify-between px-5 py-3 bg-[#1a1b22] border-b border-[#3d494c]/20 flex-wrap gap-2">
              <div className="flex items-center gap-2 flex-wrap">
                {activeModalJob.apply_url || activeModalJob.portal ? (
                  <a
                    href={activeModalJob.apply_url || activeModalJob.portal}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-gradient-to-r from-[#00687a] to-[#4cd7f6] text-[#003640] font-bold text-xs hover:brightness-110 transition-all shadow-md"
                  >
                    <ExternalLink className="w-4 h-4 text-[#003640]" />
                    <span>Open Application on Official Site ↗</span>
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

                {onSelectForRecruiters && (
                  <button
                    onClick={() => {
                      onSelectForRecruiters(activeModalJob.company, activeModalJob.job_title);
                      setActiveModalJob(null);
                    }}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-[#292931] border border-[#3d494c]/50 hover:border-[#bcc9cd] text-xs font-medium text-[#bcc9cd] hover:text-[#e3e1ec] transition-all"
                  >
                    <Users className="w-3.5 h-3.5 text-[#4cd7f6]" />
                    <span>Find Recruiters at {activeModalJob.company}</span>
                  </button>
                )}
              </div>
            </div>

            {/* Description Body */}
            <div className="flex-1 p-6 overflow-y-auto max-h-[55vh] text-[13px] text-[#e3e1ec] leading-relaxed whitespace-pre-wrap font-sans bg-[#0d0e15]">
              {formatCleanText(activeModalJob.description) || (
                <div className="text-center text-[#879396] py-8">
                  No full description text was returned by this public feed. Please visit the official job link above for complete requirements.
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between px-5 py-3.5 border-t border-[#3d494c]/30 bg-[#14151e]">
              <div className="text-[11px] font-mono text-[#869296]">
                Targeting worldwide engineering talent with Moratuwa stack match.
              </div>
              <button
                onClick={() => setActiveModalJob(null)}
                className="px-4 py-1.5 rounded-lg bg-[#292931] border border-[#3d494c]/50 hover:bg-[#3d494c]/40 text-xs text-[#e3e1ec] font-medium transition-all"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
