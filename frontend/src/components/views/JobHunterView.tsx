"use client";

import React, { useState } from "react";
import { Radar, Search, ShieldCheck, ArrowRight, ExternalLink, Sparkles, Send } from "lucide-react";
import { JobItem } from "../../types";
import { searchLiveJobs } from "../../lib/api";

interface JobHunterViewProps {
  onSelectForTailor: (job: JobItem) => void;
  onSelectForOutreach: (job: JobItem) => void;
}

export default function JobHunterView({ onSelectForTailor, onSelectForOutreach }: JobHunterViewProps) {
  const [keyword, setKeyword] = useState("Python Developer");
  const [region, setRegion] = useState("GULF");
  const [maxResults, setMaxResults] = useState(15);
  const [loading, setLoading] = useState(false);
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = () => {
    setLoading(true);
    setHasSearched(true);
    setJobs([]);

    const url = `/api/jobs/stream?keyword=${encodeURIComponent(keyword)}&region=${region}&max_results=${maxResults}`;
    const sse = new EventSource(url);

    sse.onmessage = (event) => {
      if (event.data === "[DONE]") {
        sse.close();
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
              <option value={10}>10 Postings</option>
              <option value={15}>15 Postings</option>
              <option value={25}>25 Postings</option>
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

      {/* Results Header */}
      {jobs.length > 0 && (
        <div className="text-[14px] text-[#e3e1ec] font-medium">
          Found <strong className="text-[#4cd7f6]">{jobs.length}</strong> active verified postings:
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && (
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

      {/* Empty State */}
      {!loading && hasSearched && jobs.length === 0 && (
        <div className="p-12 text-center rounded-xl bg-[#0d0e15] border border-[#3d494c]/30">
          <p className="text-[#bcc9cd] text-sm">No live jobs found matching "{keyword}". Try expanding your region or keyword.</p>
        </div>
      )}

      {/* Jobs Grid */}
      {!loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {jobs.map((job, idx) => {
            const score = job.fit_analysis?.match_score || 70;
            const scoreColor =
              score >= 75 ? "text-[#4edea3] border-[#4edea3]/40 bg-[#4edea3]/10" : "text-[#4cd7f6] border-[#4cd7f6]/40 bg-[#4cd7f6]/10";

            return (
              <div
                key={idx}
                className="p-5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 hover:border-[#3d494c]/80 transition-all specular-border flex flex-col justify-between group"
              >
                <div>
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-[16px] font-semibold text-[#e3e1ec] group-hover:text-[#4cd7f6] transition-colors">
                        {job.job_title}
                      </h3>
                      <div className="text-[13px] text-[#bcc9cd] mt-0.5">
                        <strong className="text-[#e3e1ec]">{job.company}</strong> &nbsp;•&nbsp; {job.location}
                      </div>
                    </div>
                    <span className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded border ${scoreColor}`}>
                      {score}% ATS Match
                    </span>
                  </div>

                  <div className="mt-3 text-[12px] text-[#bcc9cd] line-clamp-3">
                    {job.description || "Active production opening in the engineering platform team."}
                  </div>

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

                {/* Card Actions */}
                <div className="mt-4 pt-3 border-t border-[#3d494c]/20 flex items-center justify-between">
                  <a
                    href={job.portal || job.job_url || "#"}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1 text-xs text-[#bcc9cd] hover:text-[#e3e1ec]"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    <span>View Portal</span>
                  </a>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => onSelectForTailor(job)}
                      className="px-2.5 py-1.5 rounded-lg bg-[#1a1b22] border border-[#3d494c]/40 text-[#e3e1ec] text-xs hover:border-[#4cd7f6] hover:text-[#4cd7f6] flex items-center gap-1 transition-all"
                    >
                      <Sparkles className="w-3 h-3" />
                      <span>Tailor CV</span>
                    </button>

                    <button
                      onClick={() => onSelectForOutreach(job)}
                      className="px-3 py-1.5 rounded-lg bg-[#4cd7f6] text-[#003640] font-medium text-xs hover:bg-white transition-all flex items-center gap-1 active:scale-[0.98] cyan-glow"
                    >
                      <Send className="w-3 h-3" />
                      <span>Outreach</span>
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
