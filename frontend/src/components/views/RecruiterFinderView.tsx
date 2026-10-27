"use client";

import React, { useState } from "react";
import { UserSearch, Building2, Mail, ExternalLink, CheckCircle2, Search, ArrowRight, Download, Users, Sparkles } from "lucide-react";
import { HiringCompanyLead } from "../../types";
import { findCompaniesByRole, searchCompanyHR } from "../../lib/api";

interface RecruiterFinderViewProps {
  onSelectForOutreach: (jobTitle: string, company: string, email: string, portal: string, desc: string) => void;
}

export default function RecruiterFinderView({ onSelectForOutreach }: RecruiterFinderViewProps) {
  const [mode, setMode] = useState<"role" | "company">("role");
  const [roleInput, setRoleInput] = useState("Python Developer");
  const [regionFilter, setRegionFilter] = useState("GULF");
  const [maxCompanies, setMaxCompanies] = useState(25);
  const [loading, setLoading] = useState(false);
  const [companies, setCompanies] = useState<HiringCompanyLead[]>([]);
  const [hasSearched, setHasSearched] = useState(false);

  // Single company search state
  const [singleCompany, setSingleCompany] = useState("Careem");
  const [singleDomain, setSingleDomain] = useState("");
  const [singleResult, setSingleResult] = useState<any>(null);

  const presets = [
    { label: "🐍 Python Developer", val: "Python Developer" },
    { label: "💻 Full Stack", val: "Full Stack Engineer" },
    { label: "🤖 AI / LLM Engineer", val: "AI Engineer" },
    { label: "⚡ Embedded Systems", val: "Embedded Systems Engineer" },
    { label: "☁️ DevOps / Cloud", val: "DevOps Engineer" },
    { label: "📊 Data Engineer", val: "Data Engineer" },
  ];

  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const sseRef = React.useRef<EventSource | null>(null);

  React.useEffect(() => {
    return () => {
      if (sseRef.current) sseRef.current.close();
    };
  }, []);

  const handleRoleSearch = (targetRole: string = roleInput) => {
    setLoading(true);
    setHasSearched(true);
    setCompanies([]);
    setErrorMsg(null);

    if (sseRef.current) {
      sseRef.current.close();
    }

    const url = `/api/hr/by-role/stream?role=${encodeURIComponent(targetRole)}&region=${regionFilter}&limit=${maxCompanies}`;
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
        setCompanies((prev) => {
          if (prev.some((c) => c.company.toLowerCase() === item.company.toLowerCase())) {
            return prev;
          }
          return [...prev, item];
        });
      } catch (err) {
        console.error("SSE parse err:", err);
      }
    };

    sse.onerror = (err) => {
      console.warn("SSE stream ended or closed", err);
      sse.close();
      sseRef.current = null;
      setLoading(false);
    };
  };

  const handleCompanySearch = async () => {
    setLoading(true);
    try {
      const data = await searchCompanyHR(singleCompany, singleDomain, regionFilter);
      setSingleResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = () => {
    if (!companies.length) return;
    const headers = ["Company,Job Title,Location,Domain,Direct HR Email,Portal URL\n"];
    const rows = companies.map((c) =>
      `"${c.company}","${c.job_title}","${c.location}","${c.domain}","${c.primary_email || ""}","${c.portal}"`
    );
    const blob = new Blob([...headers, ...rows.map((r) => r + "\n")], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `hiring_companies_${roleInput.toLowerCase().replace(/\s+/g, "_")}.csv`;
    a.click();
  };

  return (
    <div className="flex flex-col gap-5 p-6 max-w-7xl mx-auto">
      {/* Top Banner / Header */}
      <div className="p-4 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h1 className="text-[20px] font-semibold text-[#e3e1ec] tracking-tight flex items-center gap-2">
              <UserSearch className="w-5 h-5 text-[#4cd7f6]" />
              Global Recruiter &amp; Hiring Lead Finder
            </h1>
            <p className="text-[13px] text-[#bcc9cd] mt-0.5">
              Discover real companies hiring for your target engineering title and extract verified corporate HR contacts.
            </p>
          </div>

          {/* Mode Switcher */}
          <div className="flex items-center gap-1.5 p-1 bg-[#1a1b22] rounded-lg border border-[#3d494c]/40 text-xs">
            <button
              onClick={() => setMode("role")}
              className={`px-3 py-1.5 rounded-md font-medium transition-all ${
                mode === "role" ? "bg-[#292931] text-[#4cd7f6] shadow-sm" : "text-[#bcc9cd] hover:text-[#e3e1ec]"
              }`}
            >
              🎯 By Job Role
            </button>
            <button
              onClick={() => setMode("company")}
              className={`px-3 py-1.5 rounded-md font-medium transition-all ${
                mode === "company" ? "bg-[#292931] text-[#4cd7f6] shadow-sm" : "text-[#bcc9cd] hover:text-[#e3e1ec]"
              }`}
            >
              🏢 By Company
            </button>
          </div>
        </div>

        {mode === "role" && (
          <>
            {/* Quick Presets */}
            <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-[#3d494c]/20">
              <span className="text-[10px] font-mono uppercase text-[#869397] mr-1">QUICK PRESETS:</span>
              {presets.map((p) => (
                <button
                  key={p.val}
                  onClick={() => {
                    setRoleInput(p.val);
                    handleRoleSearch(p.val);
                  }}
                  className="px-2.5 py-1 rounded bg-[#1e1f26] border border-[#3d494c]/40 text-[#e3e1ec] text-[12px] hover:border-[#4cd7f6] hover:text-[#4cd7f6] transition-all"
                >
                  {p.label}
                </button>
              ))}
            </div>

            {/* Inputs & Action */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-end pt-2">
              <div className="md:col-span-5">
                <label className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1 block">Target Job Role</label>
                <div className="relative">
                  <Search className="w-4 h-4 absolute left-3 top-2.5 text-[#869397]" />
                  <input
                    type="text"
                    value={roleInput}
                    onChange={(e) => setRoleInput(e.target.value)}
                    placeholder="e.g. Python Developer, Full Stack Engineer"
                    className="w-full pl-9 pr-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none"
                  />
                </div>
              </div>

              <div className="md:col-span-3">
                <label className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1 block">Region Filter</label>
                <select
                  value={regionFilter}
                  onChange={(e) => setRegionFilter(e.target.value)}
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
                  value={maxCompanies}
                  onChange={(e) => setMaxCompanies(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none"
                >
                  <option value={10}>10 Companies (Fast)</option>
                  <option value={25}>25 Companies (Recommended)</option>
                  <option value={50}>50 Companies (Deep Scan)</option>
                  <option value={100}>100 Companies (Maximum Scrape)</option>
                </select>
              </div>

              <div className="md:col-span-2">
                <button
                  onClick={() => handleRoleSearch()}
                  disabled={loading}
                  className="w-full py-2 px-3 rounded-lg bg-[#4cd7f6] text-[#003640] font-semibold text-[13px] hover:bg-white transition-all cyan-glow disabled:opacity-50"
                >
                  {loading ? "Scanning..." : "🚀 Discover"}
                </button>
              </div>
            </div>
          </>
        )}

        {mode === "company" && (
          <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-end pt-2">
            <div className="md:col-span-4">
              <label className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1 block">Target Company Name</label>
              <input
                type="text"
                value={singleCompany}
                onChange={(e) => setSingleCompany(e.target.value)}
                placeholder="e.g. Careem, Talabat, Grab"
                className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none"
              />
            </div>
            <div className="md:col-span-4">
              <label className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1 block">Domain (Optional)</label>
              <input
                type="text"
                value={singleDomain}
                onChange={(e) => setSingleDomain(e.target.value)}
                placeholder="e.g. careem.com"
                className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none"
              />
            </div>
            <div className="md:col-span-2">
              <label className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1 block">Region</label>
              <select
                value={regionFilter}
                onChange={(e) => setRegionFilter(e.target.value)}
                className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none"
              >
                <option value="GULF">GULF</option>
                <option value="MIGRATABLE">MIGRATABLE</option>
                <option value="ALL">ALL</option>
              </select>
            </div>
            <div className="md:col-span-2">
              <button
                onClick={handleCompanySearch}
                disabled={loading}
                className="w-full py-2 px-3 rounded-lg bg-[#4cd7f6] text-[#003640] font-semibold text-[13px] hover:bg-white transition-all cyan-glow disabled:opacity-50"
              >
                {loading ? "Searching..." : "🔎 Find Contacts"}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Results Header with Metrics */}
      {mode === "role" && companies.length > 0 && (
        <div className="flex items-center justify-between">
          <div className="text-[14px] text-[#e3e1ec] font-medium flex items-center gap-2">
            <span>Found <strong className="text-[#4cd7f6]">{companies.length}</strong> hiring companies for "{roleInput}"</span>
            {loading && (
              <span className="text-xs text-[#4cd7f6] font-mono animate-pulse flex items-center gap-1.5 ml-2">
                <span className="w-2 h-2 rounded-full bg-[#4cd7f6] animate-ping"></span>
                Streaming live companies...
              </span>
            )}
          </div>
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#1a1b22] border border-[#3d494c]/40 text-[#bcc9cd] hover:text-[#e3e1ec] text-xs transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>
        </div>
      )}

      {/* Loading Skeleton: Only shown while waiting for first company */}
      {loading && companies.length === 0 && (
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
      {!loading && hasSearched && companies.length === 0 && mode === "role" && (
        <div className="p-12 text-center rounded-xl bg-[#0d0e15] border border-[#3d494c]/30">
          <p className="text-[#bcc9cd] text-sm">No live vacancies found for "{roleInput}" in {regionFilter}. Try expanding to "ALL" regions.</p>
        </div>
      )}

      {/* Role Results Bento Grid */}
      {mode === "role" && companies.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {companies.map((c, idx) => (
            <div
              key={idx}
              className="p-5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 hover:border-[#3d494c]/80 transition-all specular-border flex flex-col justify-between group"
            >
              <div>
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-[#292931] border border-[#3d494c]/40 flex items-center justify-center font-mono font-bold text-[#4cd7f6] text-sm">
                      {c.company.slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <h3 className="text-[16px] font-semibold text-[#e3e1ec] group-hover:text-[#4cd7f6] transition-colors">
                        {c.company}
                      </h3>
                      <div className="text-[12px] text-[#bcc9cd]">{c.location}</div>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#4edea3]/10 border border-[#4edea3]/30 text-[#4edea3]">
                    Hiring Now
                  </span>
                </div>

                {/* Opening Role */}
                <div className="mt-3.5 pt-3 border-t border-[#3d494c]/20">
                  <div className="text-[13px] font-medium text-[#e3e1ec]">
                    💼 Opening: <span className="text-[#4cd7f6]">{c.job_title}</span>
                  </div>
                  <div className="text-[11px] font-mono text-[#869397] mt-1">
                    Domain: <code className="text-[#bcc9cd]">{c.domain}</code>
                  </div>

                  {/* Primary Email Badge */}
                  <div className="mt-2.5 flex items-center gap-2">
                    {c.primary_email ? (
                      <div className="px-2 py-1 rounded bg-[#1a1b22] border border-[#4edea3]/40 flex items-center gap-1.5 font-mono text-[11px] text-[#4edea3]">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>{c.primary_email}</span>
                      </div>
                    ) : (
                      <div className="px-2 py-1 rounded bg-[#1a1b22] border border-[#3d494c]/40 flex items-center gap-1.5 text-[11px] text-[#bcc9cd]">
                        <span>🌐 Direct Portal Application</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="mt-4 pt-3 border-t border-[#3d494c]/20 flex items-center justify-between">
                <div className="flex items-center gap-3 text-xs">
                  <a
                    href={c.recruiter_dork}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1 text-[#4cd7f6] hover:underline"
                  >
                    <Users className="w-3.5 h-3.5" />
                    <span>Recruiters</span>
                  </a>
                  <a
                    href={c.portal}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1 text-[#bcc9cd] hover:text-[#e3e1ec]"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    <span>Job Link</span>
                  </a>
                </div>

                {c.primary_email ? (
                  <button
                    onClick={() =>
                      onSelectForOutreach(
                        c.job_title,
                        c.company,
                        c.primary_email,
                        c.portal,
                        c.description
                      )
                    }
                    className="px-3 py-1.5 rounded-lg bg-[#4cd7f6] text-[#003640] font-medium text-xs hover:bg-white transition-all flex items-center gap-1.5 active:scale-[0.98] cyan-glow shadow-sm"
                  >
                    <Mail className="w-3.5 h-3.5" />
                    <span>Outreach</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                ) : (
                  <a
                    href={c.portal}
                    target="_blank"
                    rel="noreferrer"
                    className="px-3 py-1.5 rounded-lg bg-[#1a1b22] border border-[#3d494c]/50 hover:border-[#4cd7f6]/60 text-[#e3e1ec] hover:text-[#4cd7f6] font-medium text-xs transition-all flex items-center gap-1.5 active:scale-[0.98]"
                  >
                    <span>Apply via Portal</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Single Company Results */}
      {mode === "company" && singleResult && (
        <div className="p-6 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h2 className="text-[18px] font-semibold text-[#e3e1ec]">{singleResult.company}</h2>
            <span className="text-xs font-mono text-[#4cd7f6]">{singleResult.domain}</span>
          </div>

          {singleResult.verified_contacts && singleResult.verified_contacts.length > 0 ? (
            <div className="flex flex-col gap-2 mt-2">
              <h4 className="text-xs font-mono text-[#869397] uppercase">Verified Contacts:</h4>
              {singleResult.verified_contacts.map((v: any, i: number) => (
                <div key={i} className="p-3 rounded-lg bg-[#1a1b22] border border-[#3d494c]/30 flex items-center justify-between text-xs">
                  <div>
                    <strong className="text-[#e3e1ec]">{v.name}</strong> — <span className="text-[#bcc9cd]">{v.role}</span>
                    <div className="text-[#4cd7f6] font-mono mt-0.5">{v.email}</div>
                  </div>
                  <button
                    onClick={() => onSelectForOutreach("Software Engineer", singleResult.company, v.email, "", "")}
                    className="px-2.5 py-1 rounded bg-[#4cd7f6] text-[#003640] font-medium"
                  >
                    Outreach
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-[#bcc9cd]">No leaked public emails in databases. Use the precision recruiter search dorks below:</p>
          )}

          {singleResult.search_dorks && (
            <div className="flex flex-col gap-1.5 mt-2">
              {singleResult.search_dorks.map((d: any, i: number) => (
                <a
                  key={i}
                  href={d.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-[#4cd7f6] hover:underline flex items-center gap-1"
                >
                  👉 {d.title}
                </a>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
