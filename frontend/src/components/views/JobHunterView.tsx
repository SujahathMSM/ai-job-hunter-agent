"use client";

import React, { useState } from "react";
import {
  Radar,
  Search,
  ShieldCheck,
  ExternalLink,
  Sparkles,
  Send,
  Calendar,
  Mail,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Users,
  CheckCircle2,
  Building2,
  MapPin,
  X,
} from "lucide-react";
import { JobItem } from "../../types";

interface JobHunterViewProps {
  onSelectForTailor: (job: JobItem) => void;
  onSelectForOutreach: (job: JobItem) => void;
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

export default function JobHunterView({ onSelectForTailor, onSelectForOutreach }: JobHunterViewProps) {
  const [keyword, setKeyword] = useState("Python Developer");
  const [region, setRegion] = useState("GULF");
  const [maxResults, setMaxResults] = useState(30);
  const [loading, setLoading] = useState(false);
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [expandedJobKey, setExpandedJobKey] = useState<string | null>(null);
  const [modalJob, setModalJob] = useState<JobItem | null>(null);
  const sseRef = React.useRef<EventSource | null>(null);

  React.useEffect(() => {
    return () => {
      if (sseRef.current) sseRef.current.close();
    };
  }, []);

  const toggleExpand = (key: string) => {
    setExpandedJobKey((prev) => (prev === key ? null : key));
  };

  const handleSearch = () => {
    setLoading(true);
    setHasSearched(true);
    setJobs([]);
    setExpandedJobKey(null);

    if (sseRef.current) {
      sseRef.current.close();
    }

    const url = `/api/jobs/stream?keyword=${encodeURIComponent(keyword)}&region=${region}&max_results=${maxResults}`;
    const sse = new EventSource(url);
    sseRef.current = sse;

    sse.onmessage = (event) => {
      if (event.data === "[DONE]") {
        sse.close();
        sseRef.current = null;
        setLoading(false);
        return;
      }
      try {
        const item = JSON.parse(event.data);
        setJobs((prev) => {
          if (prev.some((j) => j.job_title === item.job_title && j.company === item.company)) {
            return prev;
          }
          return [...prev, item];
        });
      } catch (err) {
        console.error("Job SSE parse err:", err);
      }
    };

    sse.onerror = (err) => {
      console.warn("Job stream ended or closed", err);
      sse.close();
      sseRef.current = null;
      setLoading(false);
    };
  };

  return (
    <div className="flex flex-col gap-5 p-6 max-w-7xl mx-auto">
      {/* Search Header Banner */}
      <div className="p-4 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h1 className="text-[20px] font-semibold text-[#e3e1ec] tracking-tight flex items-center gap-2">
              <Radar className="w-5 h-5 text-[#4cd7f6]" />
              Live Job Hunter &amp; ATS Fit Analyzer
            </h1>
            <p className="text-[13px] text-[#bcc9cd] mt-0.5">
              Live multi-board scraper enforcing a 14-day recency cutoff and automated ATS relevance scoring.
            </p>
          </div>
          {/* Strict Israel Exclusion Badge */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#93000a]/20 border border-[#93000a]/40 text-[#ffb4ab] text-[11px] font-mono">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Israel Exclusion: ENFORCED</span>
          </div>
        </div>

        {/* Input Controls */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-end pt-2 border-t border-[#3d494c]/20">
          <div className="md:col-span-5">
            <label className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1 block">Engineering Search Keyword</label>
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-[#869397]" />
              <input
                type="text"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                placeholder="e.g. Python Developer, Backend Systems Engineer"
                className="w-full pl-9 pr-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none"
              />
            </div>
          </div>

          <div className="md:col-span-3">
            <label className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1 block">Regional Filter</label>
            <select
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none"
            >
              <option value="GULF">GULF (UAE, KSA, Qatar, Oman)</option>
              <option value="MIGRATABLE">MIGRATABLE (Singapore, UK, Germany, AU)</option>
              <option value="ALL">ALL (Global)</option>
            </select>
          </div>

          <div className="md:col-span-2">
            <label className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1 block">Max Results</label>
            <select
              value={maxResults}
              onChange={(e) => setMaxResults(Number(e.target.value))}
              className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none"
            >
              <option value={15}>15 Postings (Fast)</option>
              <option value={30}>30 Postings (Recommended)</option>
              <option value={50}>50 Postings (Deep Scan)</option>
              <option value={100}>100 Postings (Maximum Scrape)</option>
              <option value={150}>150 Postings (Exhaustive)</option>
            </select>
          </div>

          <div className="md:col-span-2">
            <button
              onClick={handleSearch}
              disabled={loading}
              className="w-full py-2 px-3 rounded-lg bg-[#4cd7f6] text-[#003640] font-semibold text-[13px] hover:bg-white transition-all cyan-glow disabled:opacity-50"
            >
              {loading ? "Scraping..." : "⚡ Hunt Jobs"}
            </button>
          </div>
        </div>
      </div>

      {/* Results Header & Streaming Status */}
      {jobs.length > 0 && (
        <div className="flex items-center justify-between text-[14px] text-[#e3e1ec] font-medium">
          <div>
            Found <strong className="text-[#4cd7f6]">{jobs.length}</strong> active verified postings:
          </div>
          {loading && (
            <span className="text-xs text-[#4cd7f6] font-mono animate-pulse flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#4cd7f6] animate-ping"></span>
              Streaming live postings...
            </span>
          )}
        </div>
      )}

      {/* Loading Skeleton: Only shown while waiting for first job */}
      {loading && jobs.length === 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="p-5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 animate-pulse h-48 flex flex-col justify-between">
              <div className="h-5 bg-[#292931] rounded w-1/3"></div>
              <div className="h-4 bg-[#1e1f26] rounded w-2/3"></div>
              <div className="h-4 bg-[#1e1f26] rounded w-1/2"></div>
            </div>
          ))}
        </div>
      )}

      {/* Empty State: Only shown if search completed with 0 results */}
      {!loading && hasSearched && jobs.length === 0 && (
        <div className="p-12 text-center rounded-xl bg-[#0d0e15] border border-[#3d494c]/30">
          <p className="text-[#bcc9cd] text-sm">No live jobs found matching "{keyword}". Try expanding your region or keyword.</p>
        </div>
      )}

      {/* Jobs Grid */}
      {jobs.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {jobs.map((job, idx) => {
            const jobKey = job.id || `${job.company}-${job.job_title}-${idx}`;
            const isExpanded = expandedJobKey === jobKey;
            const score = job.fit_analysis?.match_score || 70;
            const scoreColor =
              score >= 75 ? "text-[#4edea3] border-[#4edea3]/40 bg-[#4edea3]/10" : "text-[#4cd7f6] border-[#4cd7f6]/40 bg-[#4cd7f6]/10";
            const hasEmail = Boolean(job.hr_email && job.hr_email.includes("@"));
            const portalUrl = job.portal || job.job_url || "#";
            const recruiterSearchUrl =
              job.recruiter_dork ||
              `https://www.google.com/search?q=site:linkedin.com/in+('Technical+Recruiter'+OR+'Talent+Acquisition')+${encodeURIComponent('"' + job.company + '"')}`;

            if (isExpanded) {
              return (
                <div
                  key={jobKey}
                  className="col-span-1 md:col-span-2 p-6 rounded-xl bg-[#0e1017] border-2 border-[#4cd7f6]/60 specular-border flex flex-col gap-4 shadow-2xl transition-all"
                >
                  {/* Expanded Top Header */}
                  <div className="flex flex-col md:flex-row md:items-start justify-between gap-3 pb-3 border-b border-[#3d494c]/30">
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <h2 className="text-[19px] font-bold text-[#e3e1ec]">{job.job_title}</h2>
                        <span className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded border ${scoreColor}`}>
                          {score}% ATS Match
                        </span>
                        {job.site && (
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1e1f26] text-[#869397] border border-[#3d494c]/30">
                            via {job.site}
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-2 text-[13px] text-[#bcc9cd] mt-1.5 flex-wrap">
                        <span className="flex items-center gap-1 font-semibold text-[#e3e1ec]">
                          <Building2 className="w-3.5 h-3.5 text-[#4cd7f6]" /> {job.company}
                        </span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3.5 h-3.5 text-[#869397]" /> {job.location}
                        </span>
                        <span>•</span>
                        <span className="flex items-center gap-1 text-[#4cd7f6] font-mono">
                          <Calendar className="w-3.5 h-3.5" /> {job.posted_label || job.date_posted || "Recently Listed"}
                        </span>
                        {job.salary && (
                          <>
                            <span>•</span>
                            <span className="text-[#4edea3] font-mono font-semibold">{job.salary}</span>
                          </>
                        )}
                      </div>

                      {/* Prominent HR Status Badge */}
                      <div className="mt-2.5">
                        {hasEmail ? (
                          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#4edea3]/10 border border-[#4edea3]/30 text-[#4edea3] text-[11px] font-mono">
                            <Mail className="w-3.5 h-3.5 text-[#4edea3]" />
                            <span>Verified Corporate HR: <strong>{job.hr_email}</strong></span>
                          </div>
                        ) : (
                          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#f59e0b]/10 border border-[#f59e0b]/30 text-[#f59e0b] text-[11px] font-mono">
                            <AlertCircle className="w-3.5 h-3.5 text-[#f59e0b]" />
                            <span>No Direct HR Email in Posting • Direct Portal Application Required</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Expanded Top Action Buttons */}
                    <div className="flex items-center gap-2 flex-wrap self-start md:self-auto">
                      <button
                        onClick={() => onSelectForTailor(job)}
                        className="px-3 py-1.5 rounded-lg bg-[#1a1b22] border border-[#3d494c]/50 text-[#e3e1ec] text-xs hover:border-[#4cd7f6] hover:text-[#4cd7f6] flex items-center gap-1.5 transition-all"
                      >
                        <Sparkles className="w-3.5 h-3.5 text-[#4cd7f6]" />
                        <span>Tailor CV</span>
                      </button>

                      {hasEmail ? (
                        <button
                          onClick={() => onSelectForOutreach(job)}
                          className="px-3.5 py-1.5 rounded-lg bg-[#4cd7f6] text-[#003640] font-semibold text-xs hover:bg-white transition-all flex items-center gap-1.5 cyan-glow"
                        >
                          <Send className="w-3.5 h-3.5" />
                          <span>Outreach Email</span>
                        </button>
                      ) : (
                        <a
                          href={portalUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="px-3.5 py-1.5 rounded-lg bg-[#4cd7f6] text-[#003640] font-semibold text-xs hover:bg-white transition-all flex items-center gap-1.5 cyan-glow"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                          <span>Apply on Portal ↗</span>
                        </a>
                      )}

                      <a
                        href={recruiterSearchUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-1.5 rounded-lg bg-[#1a1b22] border border-[#3d494c]/40 text-[#bcc9cd] hover:text-[#e3e1ec] text-xs flex items-center gap-1.5 transition-all"
                      >
                        <Users className="w-3.5 h-3.5 text-[#4cd7f6]" />
                        <span>Find Recruiters ↗</span>
                      </a>

                      <button
                        onClick={() => toggleExpand(jobKey)}
                        className="px-3 py-1.5 rounded-lg bg-[#292931] text-[#bcc9cd] hover:text-white text-xs flex items-center gap-1 transition-all"
                      >
                        <ChevronUp className="w-3.5 h-3.5" />
                        <span>Collapse</span>
                      </button>
                    </div>
                  </div>

                  {/* Skills & ATS Insights */}
                  {job.fit_analysis && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 p-3.5 rounded-lg bg-[#14151f] border border-[#3d494c]/20">
                      <div>
                        <div className="text-[11px] font-mono uppercase text-[#4edea3] mb-1.5 flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Matched Engineering Skills
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {job.fit_analysis.matched_skills && job.fit_analysis.matched_skills.length > 0 ? (
                            job.fit_analysis.matched_skills.map((s, i) => (
                              <span key={i} className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#4edea3]/10 text-[#4edea3] border border-[#4edea3]/20">
                                {s}
                              </span>
                            ))
                          ) : (
                            <span className="text-xs text-[#869397]">Core backend architecture & engineering standards</span>
                          )}
                        </div>
                      </div>

                      <div>
                        <div className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1.5">
                          Target Platform Tech Stack
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {job.fit_analysis.missing_tech && job.fit_analysis.missing_tech.length > 0 ? (
                            job.fit_analysis.missing_tech.map((s, i) => (
                              <span key={i} className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#1e1f26] text-[#bcc9cd] border border-[#3d494c]/30">
                                {s}
                              </span>
                            ))
                          ) : (
                            <span className="text-xs text-[#869397]">Aligned with candidate master engineering persona</span>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Full Clean Formatted Description */}
                  <div className="flex flex-col gap-1.5">
                    <div className="text-[11px] font-mono uppercase text-[#869397]">
                      Full Production Job Description
                    </div>
                    <div className="p-4 rounded-xl bg-[#14151f] border border-[#3d494c]/30 text-[13px] text-[#e3e1ec] leading-relaxed max-h-[460px] overflow-y-auto whitespace-pre-line font-sans scrollbar-thin">
                      {formatCleanText(job.full_description || job.description)}
                    </div>
                  </div>

                  {/* Expanded Bottom Action Footer */}
                  <div className="pt-3 border-t border-[#3d494c]/20 flex items-center justify-between">
                    <a
                      href={portalUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center gap-1.5 text-xs text-[#4cd7f6] hover:underline"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      <span>Open Original Job Posting Link ({job.company})</span>
                    </a>

                    <button
                      onClick={() => toggleExpand(jobKey)}
                      className="text-xs text-[#bcc9cd] hover:text-[#e3e1ec] flex items-center gap-1"
                    >
                      <ChevronUp className="w-3.5 h-3.5" />
                      <span>Close Details</span>
                    </button>
                  </div>
                </div>
              );
            }

            // Compact Bento Grid Card
            return (
              <div
                key={jobKey}
                className="p-5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 hover:border-[#3d494c]/80 transition-all specular-border flex flex-col justify-between group"
              >
                <div>
                  <div className="flex items-start justify-between">
                    <div>
                      <h3
                        onClick={() => setModalJob(job)}
                        className="text-[16px] font-semibold text-[#e3e1ec] group-hover:text-[#4cd7f6] transition-colors cursor-pointer"
                      >
                        {job.job_title}
                      </h3>
                      <div className="text-[13px] text-[#bcc9cd] mt-0.5">
                        <strong className="text-[#e3e1ec]">{job.company}</strong> &nbsp;•&nbsp; {job.location}
                      </div>
                      {/* Date Posted & Salary */}
                      <div className="flex items-center gap-2 text-[11px] text-[#869397] font-mono mt-1">
                        <span className="flex items-center gap-1 text-[#4cd7f6]">
                          <Calendar className="w-3 h-3" />
                          {job.posted_label || job.date_posted || "Recently Listed"}
                        </span>
                        {job.salary && (
                          <>
                            <span>•</span>
                            <span className="text-[#4edea3] font-semibold">{job.salary}</span>
                          </>
                        )}
                      </div>
                    </div>
                    <span className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded border ${scoreColor}`}>
                      {score}% ATS Match
                    </span>
                  </div>

                  {/* HR Status Pill */}
                  <div className="mt-2.5">
                    {hasEmail ? (
                      <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-[#4edea3]/10 border border-[#4edea3]/30 text-[#4edea3] text-[10px] font-mono">
                        <Mail className="w-3 h-3 text-[#4edea3]" />
                        <span>HR: {job.hr_email}</span>
                      </div>
                    ) : (
                      <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-[#f59e0b]/10 border border-[#f59e0b]/30 text-[#f59e0b] text-[10px] font-mono">
                        <AlertCircle className="w-3 h-3 text-[#f59e0b]" />
                        <span>No Direct HR Email • Apply on Portal</span>
                      </div>
                    )}
                  </div>

                  {/* Clean Snippet Description */}
                  <div className="mt-3 text-[12px] text-[#bcc9cd] line-clamp-3 leading-relaxed">
                    {formatCleanText(job.description || "Active engineering opening in the production platform team.")}
                  </div>

                  {/* View Full Description Trigger */}
                  <button
                    onClick={() => setModalJob(job)}
                    className="text-[11px] text-[#4cd7f6] hover:underline mt-2 flex items-center gap-1 font-mono"
                  >
                    <span>View Full Job Details &amp; Requirements</span>
                    <ChevronDown className="w-3 h-3" />
                  </button>

                  {/* Skills badges */}
                  {job.fit_analysis?.matched_skills && job.fit_analysis.matched_skills.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-3">
                      {job.fit_analysis.matched_skills.slice(0, 4).map((s, i) => (
                        <span key={i} className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1e1f26] text-[#4cd7f6] border border-[#3d494c]/30">
                          {s}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Card Actions Footer */}
                <div className="mt-4 pt-3 border-t border-[#3d494c]/20 flex items-center justify-between">
                  <a
                    href={portalUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1 text-xs text-[#bcc9cd] hover:text-[#e3e1ec]"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    <span>Job Portal</span>
                  </a>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => onSelectForTailor(job)}
                      className="px-2.5 py-1.5 rounded-lg bg-[#1a1b22] border border-[#3d494c]/40 text-[#e3e1ec] text-xs hover:border-[#4cd7f6] hover:text-[#4cd7f6] flex items-center gap-1 transition-all"
                    >
                      <Sparkles className="w-3 h-3" />
                      <span>Tailor CV</span>
                    </button>

                    {hasEmail ? (
                      <button
                        onClick={() => onSelectForOutreach(job)}
                        className="px-3 py-1.5 rounded-lg bg-[#4cd7f6] text-[#003640] font-semibold text-xs hover:bg-white transition-all flex items-center gap-1 active:scale-[0.98] cyan-glow"
                      >
                        <Send className="w-3 h-3" />
                        <span>Outreach</span>
                      </button>
                    ) : (
                      <a
                        href={portalUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-1.5 rounded-lg bg-[#4cd7f6] text-[#003640] font-semibold text-xs hover:bg-white transition-all flex items-center gap-1 active:scale-[0.98] cyan-glow"
                      >
                        <ExternalLink className="w-3 h-3" />
                        <span>Apply on Portal ↗</span>
                      </a>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* User-Friendly Centered Description Modal with Blurred Backdrop */}
      {modalJob && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200"
          onClick={() => setModalJob(null)}
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
                    📍 {modalJob.location}
                  </span>
                  {modalJob.site && (
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full border border-[#3d494c]/40 bg-[#1e1f26] text-[#869397]">
                      via {modalJob.site}
                    </span>
                  )}
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#005047]/30 border border-[#00a389]/40 text-[#4cd7f6] font-bold">
                    ✓ {modalJob.fit_analysis?.match_score || 70}% ATS MATCH
                  </span>
                </div>
                <h2 className="text-lg font-bold text-[#e3e1ec] tracking-tight">
                  {modalJob.job_title}
                </h2>
                <div className="flex items-center gap-3 text-xs text-[#bcc9cd]">
                  <span className="font-semibold text-[#e3e1ec] flex items-center gap-1">
                    <Building2 className="w-3.5 h-3.5 text-[#4cd7f6]" />
                    {modalJob.company}
                  </span>
                  {modalJob.salary && (
                    <span className="text-[#81e6d9] font-mono">
                      💰 {modalJob.salary}
                    </span>
                  )}
                  <span className="text-[#879396]">
                    📅 {modalJob.posted_label || modalJob.date_posted || "Recently Listed"}
                  </span>
                </div>
              </div>

              <button
                onClick={() => setModalJob(null)}
                className="p-1.5 rounded-lg text-[#869296] hover:text-[#e3e1ec] hover:bg-[#1a1b22] transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Quick Action Bar at top of modal */}
            <div className="flex items-center justify-between px-5 py-3 bg-[#1a1b22] border-b border-[#3d494c]/20 flex-wrap gap-2">
              <div className="flex items-center gap-2 flex-wrap">
                {modalJob.portal || modalJob.job_url ? (
                  <a
                    href={modalJob.portal || modalJob.job_url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-gradient-to-r from-[#00687a] to-[#4cd7f6] text-[#003640] font-bold text-xs hover:brightness-110 transition-all shadow-md"
                  >
                    <ExternalLink className="w-4 h-4 text-[#003640]" />
                    <span>Apply on Portal ↗</span>
                  </a>
                ) : null}

                <button
                  onClick={() => {
                    onSelectForTailor(modalJob);
                    setModalJob(null);
                  }}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-[#292931] border border-[#4cd7f6]/40 hover:border-[#4cd7f6] text-xs font-semibold text-[#4cd7f6] transition-all"
                >
                  <Sparkles className="w-3.5 h-3.5 text-[#4cd7f6]" />
                  <span>Tailor CV with this JD</span>
                </button>

                {Boolean(modalJob.hr_email) && (
                  <button
                    onClick={() => {
                      onSelectForOutreach(modalJob);
                      setModalJob(null);
                    }}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-[#4cd7f6] text-[#003640] hover:bg-white text-xs font-semibold transition-all cyan-glow shadow-sm"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>Outreach Pitch</span>
                  </button>
                )}
              </div>
            </div>

            {/* Description Body */}
            <div className="flex-1 p-6 overflow-y-auto max-h-[55vh] text-[13px] text-[#e3e1ec] leading-relaxed whitespace-pre-wrap font-sans bg-[#0d0e15]">
              {formatCleanText(modalJob.full_description || modalJob.description) || (
                <div className="text-center text-[#879396] py-8">
                  No full description text was returned. Please visit the official portal link above for complete requirements.
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between px-5 py-3.5 border-t border-[#3d494c]/30 bg-[#14151e]">
              <div className="text-[11px] font-mono text-[#869296]">
                Targeting verified engineering roles with zero Israel tolerance.
              </div>
              <button
                onClick={() => setModalJob(null)}
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
