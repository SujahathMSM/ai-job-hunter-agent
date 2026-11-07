"use client";

import React, { useState, useEffect } from "react";
import {
  UploadCloud,
  FileText,
  Search,
  Sparkles,
  ShieldCheck,
  Globe,
  ExternalLink,
  Send,
  Building2,
  MapPin,
  Calendar,
  Mail,
  CheckCircle2,
  Award,
  RefreshCw,
  X,
  Filter,
  DollarSign,
  Tag,
  Briefcase,
  Compass,
  MessageSquareCode,
  ScanSearch,
  AlertCircle
} from "lucide-react";
import { uploadAndMatchCV, analyzeCV, searchJobsForCV } from "../../lib/api";
import { JobItem } from "../../types";

interface UniversalCVHunterViewProps {
  onSelectForTailor: (job: JobItem) => void;
  onSelectForOutreach: (job: JobItem) => void;
  onSelectForInterview?: (jobTitle: string, company: string, location: string, desc: string) => void;
}

function formatDateBadge(dateStr?: string): string {
  if (!dateStr) return "Recent";
  const lower = dateStr.toLowerCase().trim();
  if (lower.includes("just") || lower.includes("today") || lower.includes("hour") || lower.includes("min")) return "Today";
  if (lower.includes("yesterday")) return "Yesterday";
  try {
    const d = new Date(dateStr);
    if (!isNaN(d.getTime())) {
      const formattedDate = d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
      const diffMs = Date.now() - d.getTime();
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
      if (diffDays === 0) return `${formattedDate} · Today`;
      if (diffDays === 1) return `${formattedDate} · Yesterday`;
      if (diffDays >= 2 && diffDays <= 30) return `${formattedDate} · ${diffDays}d ago`;
      return formattedDate;
    }
  } catch {}
  return dateStr;
}

export default function UniversalCVHunterView({
  onSelectForTailor,
  onSelectForOutreach,
  onSelectForInterview,
}: UniversalCVHunterViewProps) {
  const [file, setFile] = useState<File | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [searchStep, setSearchStep] = useState<string>("Ready");
  const [cvAnalysis, setCvAnalysis] = useState<any>(null);
  const [jobs, setJobs] = useState<any[]>([]);
  const [filteredJobs, setFilteredJobs] = useState<any[]>([]);
  const [selectedRegion, setSelectedRegion] = useState<string>("ALL");
  const [selectedMinMatch, setSelectedMinMatch] = useState<number>(65);
  const [searchKeyword, setSearchKeyword] = useState<string>("");
  const [activeModalJob, setActiveModalJob] = useState<any | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Auto-load matching jobs for current candidate on initial mount
  useEffect(() => {
    handleAnalyzeExisting();
  }, []);

  // Filter jobs dynamically
  useEffect(() => {
    let list = [...jobs];

    // Filter by Region
    if (selectedRegion !== "ALL") {
      const reg = selectedRegion.toLowerCase();
      if (reg === "remote") {
        list = list.filter((j) => (j.location || "").toLowerCase().includes("remote") || (j.location || "").toLowerCase().includes("worldwide"));
      } else if (reg === "gulf") {
        list = list.filter((j) => {
          const l = (j.location || "").toLowerCase();
          return l.includes("dubai") || l.includes("uae") || l.includes("gulf") || l.includes("abu dhabi") || l.includes("qatar") || l.includes("saudi");
        });
      } else if (reg === "europe") {
        list = list.filter((j) => {
          const l = (j.location || "").toLowerCase();
          return l.includes("uk") || l.includes("london") || l.includes("germany") || l.includes("europe") || l.includes("netherlands");
        });
      } else if (reg === "americas") {
        list = list.filter((j) => {
          const l = (j.location || "").toLowerCase();
          return l.includes("us") || l.includes("usa") || l.includes("united states") || l.includes("canada");
        });
      }
    }

    // Filter by Min Match Score
    list = list.filter((j) => (j.match_score || 0) >= selectedMinMatch);

    // Filter by Keyword Search
    if (searchKeyword.trim()) {
      const kw = searchKeyword.toLowerCase();
      list = list.filter((j) =>
        (j.job_title || "").toLowerCase().includes(kw) ||
        (j.company || "").toLowerCase().includes(kw) ||
        (j.description || "").toLowerCase().includes(kw)
      );
    }

    setFilteredJobs(list);
  }, [jobs, selectedRegion, selectedMinMatch, searchKeyword]);

  const handleFileUpload = async (selectedFile: File) => {
    setFile(selectedFile);
    setAnalyzing(true);
    setErrorMsg(null);
    setSearchStep("1/4: Parsing document structure & text extraction...");

    const timer1 = setTimeout(() => {
      setSearchStep("2/4: Synthesizing career domain, target roles & search vectors...");
    }, 1200);

    const timer2 = setTimeout(() => {
      setSearchStep("3/4: Scanning global live job feeds worldwide (Remote, Gulf, EU, US)...");
    }, 2800);

    const timer3 = setTimeout(() => {
      setSearchStep("4/4: Calculating semantic relevance & skill overlap scores...");
    }, 4200);

    try {
      const res = await uploadAndMatchCV(selectedFile);
      setCvAnalysis(res.analysis);
      setJobs(res.jobs || []);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || "Failed to parse and match CV. Please try again.");
    } finally {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      setAnalyzing(false);
      setSearchStep("Ready");
    }
  };

  const handleAnalyzeExisting = async () => {
    setAnalyzing(true);
    setErrorMsg(null);
    setSearchStep("Analyzing current candidate profile & career domain...");

    try {
      const analysis = await analyzeCV();
      setCvAnalysis(analysis);
      setSearchStep("Hunting matching worldwide opportunities...");
      const searchRes = await searchJobsForCV(analysis, selectedRegion, selectedMinMatch, 50);
      setJobs(searchRes.jobs || []);
    } catch (err: any) {
      console.error(err);
    } finally {
      setAnalyzing(false);
      setSearchStep("Ready");
    }
  };

  const handleRescan = async () => {
    if (!cvAnalysis) return;
    setAnalyzing(true);
    setSearchStep("Scanning live global job feeds with your CV parameters...");
    try {
      const res = await searchJobsForCV(cvAnalysis, selectedRegion, selectedMinMatch, 50);
      setJobs(res.jobs || []);
    } catch (err: any) {
      console.error(err);
      setErrorMsg("Rescan failed. Please check network connection.");
    } finally {
      setAnalyzing(false);
      setSearchStep("Ready");
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleBridgeTailor = (job: any) => {
    const jobItem: JobItem = {
      id: String(job.id || Math.random()),
      job_title: job.job_title,
      company: job.company,
      location: job.location,
      salary: job.salary || "Competitive",
      description: job.description || "",
      full_description: job.description || "",
      portal: job.portal || "",
      hr_email: job.hr_email || "",
      date_posted: job.date_posted || "Recent"
    };
    onSelectForTailor(jobItem);
  };

  const handleBridgeOutreach = (job: any) => {
    const jobItem: JobItem = {
      id: String(job.id || Math.random()),
      job_title: job.job_title,
      company: job.company,
      location: job.location,
      salary: job.salary || "Competitive",
      description: job.description || "",
      portal: job.portal || "",
      hr_email: job.hr_email || "",
      date_posted: job.date_posted || "Recent"
    };
    onSelectForOutreach(jobItem);
  };

  return (
    <div className="flex flex-col gap-6 p-6 max-w-7xl mx-auto">
      {/* Top Banner Header */}
      <div className="p-4 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-[20px] font-semibold text-[#e3e1ec] tracking-tight flex items-center gap-2">
            <ScanSearch className="w-5 h-5 text-[#4cd7f6]" />
            Universal CV Job Matcher &amp; Global Radar
          </h1>
          <p className="text-[13px] text-[#bcc9cd] mt-0.5">
            Upload <strong>any CV</strong> across any discipline (Engineering, Tech, Healthcare, Finance, Document Control, etc.) — our AI deeply analyzes your competencies and hunts matching jobs worldwide.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#4edea3]/10 border border-[#4edea3]/30 text-[#4edea3] text-[11px] font-mono">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Universal Any-Domain Matcher</span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#4cd7f6]/10 border border-[#4cd7f6]/30 text-[#4cd7f6] text-[11px] font-mono">
            <Globe className="w-3.5 h-3.5" />
            <span>Worldwide Coverage</span>
          </div>
        </div>
      </div>

      {/* CV UPLOAD & INTAKE ZONE */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Dropzone Card (5 cols) */}
        <div className="lg:col-span-5 flex flex-col gap-3">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className={`p-6 rounded-xl border-2 border-dashed transition-all flex flex-col items-center justify-center text-center gap-3 bg-[#0d0e15] ${
              dragOver
                ? "border-[#4cd7f6] bg-[#4cd7f6]/5"
                : "border-[#3d494c]/40 hover:border-[#4cd7f6]/70"
            }`}
          >
            <div className="w-12 h-12 rounded-xl bg-[#1a1b22] border border-[#3d494c]/40 flex items-center justify-center cyan-glow">
              <UploadCloud className="w-6 h-6 text-[#4cd7f6]" />
            </div>

            <div>
              <div className="text-[14px] font-semibold text-[#e3e1ec]">
                Upload Candidate CV to Match Worldwide
              </div>
              <p className="text-xs text-[#bcc9cd] mt-0.5">
                Supports PDF, DOCX, or TXT (Any profession or domain)
              </p>
            </div>

            <label className="cursor-pointer px-4 py-2 rounded-lg bg-[#4cd7f6] text-[#003640] font-semibold text-xs hover:bg-white transition-all flex items-center gap-2 cyan-glow shadow-sm">
              <FileText className="w-3.5 h-3.5" />
              <span>Choose CV File</span>
              <input
                type="file"
                accept=".pdf,.docx,.doc,.txt"
                className="hidden"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleFileUpload(e.target.files[0]);
                  }
                }}
              />
            </label>

            {file && (
              <span className="text-[11px] font-mono text-[#4edea3]">
                Selected: {file.name}
              </span>
            )}
          </div>

          <button
            onClick={handleAnalyzeExisting}
            disabled={analyzing}
            className="w-full py-2 px-3 rounded-lg bg-[#1a1b22] border border-[#3d494c]/40 text-[#bcc9cd] hover:text-[#e3e1ec] hover:border-[#4cd7f6] text-xs font-medium flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
          >
            <Sparkles className="w-3.5 h-3.5 text-[#4cd7f6]" />
            <span>Analyze Current Saved Profile CV</span>
          </button>
        </div>

        {/* PARSED CV PROFILE INTELLIGENCE (7 cols) */}
        <div className="lg:col-span-7 flex flex-col gap-3">
          <div className="p-4 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-3.5">
            <div className="flex items-center justify-between pb-2 border-b border-[#3d494c]/20">
              <span className="text-[11px] font-mono uppercase text-[#bcc9cd] flex items-center gap-1.5 font-semibold">
                <Compass className="w-3.5 h-3.5 text-[#4edea3]" />
                Extracted Career Vectors &amp; Matching Engine
              </span>
              {analyzing ? (
                <span className="text-[10px] font-mono text-[#4cd7f6] flex items-center gap-1.5 animate-pulse">
                  <RefreshCw className="w-3 h-3 animate-spin" />
                  <span>{searchStep}</span>
                </span>
              ) : (
                <span className="text-[10px] font-mono text-[#4edea3]">
                  AI Semantic Radar Ready
                </span>
              )}
            </div>

            {cvAnalysis ? (
              <div className="flex flex-col gap-3 text-xs">
                {/* Domain & Seniority */}
                <div className="flex flex-wrap items-center justify-between gap-2 p-2.5 rounded-lg bg-[#14151f] border border-[#3d494c]/20">
                  <div>
                    <div className="text-[10px] font-mono uppercase text-[#869296]">Detected Domain</div>
                    <div className="text-[13px] font-bold text-[#4cd7f6]">{cvAnalysis.primary_domain}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-[10px] font-mono uppercase text-[#869296]">Candidate &amp; Seniority</div>
                    <div className="text-[#e3e1ec] font-semibold font-mono">
                      {cvAnalysis.candidate_name} &bull; <span className="text-[#4edea3]">{cvAnalysis.seniority}</span>
                    </div>
                  </div>
                </div>

                {/* Target Roles Identified */}
                <div>
                  <div className="text-[10px] font-mono uppercase text-[#869296] mb-1.5">
                    Target Job Roles Discovered from CV ({cvAnalysis.target_roles?.length || 0}):
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {cvAnalysis.target_roles?.map((role: string, idx: number) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 rounded-md bg-[#4cd7f6]/10 border border-[#4cd7f6]/30 text-[#4cd7f6] font-mono text-xs"
                      >
                        {role}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Core Competencies Extracted */}
                <div>
                  <div className="text-[10px] font-mono uppercase text-[#869296] mb-1.5">
                    Core Technical &amp; Functional Competencies:
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {cvAnalysis.core_skills?.slice(0, 10).map((skill: string, idx: number) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 rounded-md bg-[#1e1f26] border border-[#3d494c]/40 text-[#bcc9cd] font-mono text-[11px]"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Global Search Vectors */}
                <div className="p-2.5 rounded-lg bg-[#14151f] border border-[#4edea3]/20 flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 truncate">
                    <Globe className="w-3.5 h-3.5 text-[#4edea3] shrink-0" />
                    <span className="text-[11px] text-[#bcc9cd] truncate">
                      Active Global Scrape Queries:{" "}
                      <strong className="text-[#e3e1ec] font-mono">
                        {cvAnalysis.search_queries?.join(", ") || cvAnalysis.target_roles?.join(", ")}
                      </strong>
                    </span>
                  </div>
                  <button
                    onClick={handleRescan}
                    disabled={analyzing}
                    className="shrink-0 px-2.5 py-1 rounded bg-[#4edea3]/20 hover:bg-[#4edea3]/30 text-[#4edea3] font-mono text-[10px] flex items-center gap-1 transition-colors"
                  >
                    <RefreshCw className="w-3 h-3" />
                    <span>Rescan</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="p-8 text-center text-[#869296] text-xs">
                Upload a CV file above or click "Analyze Current Saved Profile CV" to initialize universal global matching.
              </div>
            )}
          </div>
        </div>
      </div>

      {errorMsg && (
        <div className="p-3 rounded-xl bg-red-900/20 border border-red-500/30 text-xs text-red-200 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* FILTER & CONTROL BAR */}
      <div className="p-3.5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col md:flex-row md:items-center justify-between gap-3">
        {/* Left: Region Pills */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs">
          <span className="text-[10px] font-mono uppercase text-[#869296] mr-1">Region:</span>
          {[
            { id: "ALL", label: "Worldwide All" },
            { id: "remote", label: "Global Remote" },
            { id: "gulf", label: "Dubai & Gulf" },
            { id: "europe", label: "Europe & UK" },
            { id: "americas", label: "North America" },
          ].map((reg) => (
            <button
              key={reg.id}
              onClick={() => setSelectedRegion(reg.id)}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${
                selectedRegion === reg.id
                  ? "bg-[#292931] text-[#4cd7f6] border border-[#4cd7f6]/40"
                  : "bg-[#14151f] text-[#bcc9cd] hover:text-[#e3e1ec] border border-[#3d494c]/30"
              }`}
            >
              {reg.label}
            </button>
          ))}
        </div>

        {/* Right: Min Match & Search Box */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Match Score Filter */}
          <div className="flex items-center gap-1 text-xs">
            <span className="text-[10px] font-mono uppercase text-[#869296]">Match Fit:</span>
            {[
              { score: 65, label: "All" },
              { score: 80, label: "80%+ Fit" },
              { score: 90, label: "90%+ Super" },
            ].map((m) => (
              <button
                key={m.score}
                onClick={() => setSelectedMinMatch(m.score)}
                className={`px-2.5 py-1 rounded text-[11px] font-mono transition-all ${
                  selectedMinMatch === m.score
                    ? "bg-[#4edea3]/20 text-[#4edea3] border border-[#4edea3]/40"
                    : "bg-[#14151f] text-[#bcc9cd] border border-[#3d494c]/30"
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>

          {/* Quick Search */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-[#869296]" />
            <input
              type="text"
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              placeholder="Search title, company..."
              className="pl-8 pr-3 py-1.5 rounded-lg bg-[#14151f] border border-[#3d494c]/40 text-xs text-[#e3e1ec] focus:outline-none focus:border-[#4cd7f6] w-48"
            />
          </div>
        </div>
      </div>

      {/* JOB RESULTS DECK */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between px-1">
          <div className="text-xs text-[#bcc9cd] flex items-center gap-2">
            <span>Showing</span>
            <strong className="text-[#4cd7f6] font-mono">{filteredJobs.length}</strong>
            <span>worldwide jobs matching this CV</span>
          </div>
          <span className="text-[11px] font-mono text-[#869296]">
            Sorted by Highest Semantic Relevance
          </span>
        </div>

        {analyzing && jobs.length === 0 ? (
          <div className="p-16 text-center flex flex-col items-center justify-center gap-3">
            <RefreshCw className="w-8 h-8 text-[#4cd7f6] animate-spin" />
            <div className="text-sm font-semibold text-[#e3e1ec]">{searchStep}</div>
            <p className="text-xs text-[#bcc9cd]">Aggregating live job boards across worldwide remote, UAE, and international portals...</p>
          </div>
        ) : filteredJobs.length === 0 ? (
          <div className="p-12 text-center rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 flex flex-col items-center gap-2">
            <ScanSearch className="w-8 h-8 text-[#869296]" />
            <div className="text-sm font-semibold text-[#e3e1ec]">No jobs found matching current filters</div>
            <p className="text-xs text-[#bcc9cd]">Try selecting "Worldwide All" region or lowering the match threshold to "All".</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3.5">
            {filteredJobs.map((job, idx) => {
              const isSuper = (job.match_score || 0) >= 90;
              const isHigh = (job.match_score || 0) >= 80;
              const hasEmail = Boolean(job.hr_email && job.hr_email.includes("@"));

              return (
                <div
                  key={job.id || idx}
                  className="p-5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 hover:border-[#4cd7f6]/60 transition-all flex flex-col gap-3 shadow-md"
                >
                  {/* Card Header */}
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      {/* Match Score Badge */}
                      <div
                        className={`w-14 h-14 rounded-xl flex flex-col items-center justify-center font-mono font-bold shrink-0 border ${
                          isSuper
                            ? "bg-[#4edea3]/10 text-[#4edea3] border-[#4edea3]/40 emerald-glow"
                            : isHigh
                            ? "bg-[#4cd7f6]/10 text-[#4cd7f6] border-[#4cd7f6]/40 cyan-glow"
                            : "bg-[#f59e0b]/10 text-[#f59e0b] border-[#f59e0b]/40"
                        }`}
                      >
                        <span className="text-base leading-none">{job.match_score}%</span>
                        <span className="text-[8.5px] uppercase tracking-wider font-semibold mt-0.5">
                          {job.match_tier || "MATCH"}
                        </span>
                      </div>

                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="text-[16px] font-semibold text-[#e3e1ec] leading-snug">
                            {job.job_title}
                          </h3>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1e1f26] border border-[#3d494c]/40 text-[#bcc9cd]">
                            {job.source || "Global Remote"}
                          </span>
                        </div>

                        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-[#bcc9cd] mt-1 font-sans">
                          <span className="flex items-center gap-1 font-medium text-[#e3e1ec]">
                            <Building2 className="w-3.5 h-3.5 text-[#4cd7f6]" />
                            {job.company}
                          </span>
                          <span className="flex items-center gap-1 text-[#4edea3]">
                            <MapPin className="w-3.5 h-3.5" />
                            {job.location}
                          </span>
                          <span className="flex items-center gap-1 text-[#869296] font-mono text-[11px]">
                            <Calendar className="w-3 h-3" />
                            {formatDateBadge(job.date_posted)}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Trailing Actions */}
                    <div className="flex items-center gap-2 flex-wrap self-start sm:self-auto">
                      <button
                        onClick={() => handleBridgeTailor(job)}
                        className="px-3 py-1.5 rounded-lg bg-[#1a1b22] border border-[#4cd7f6]/40 hover:bg-[#4cd7f6]/10 text-[#4cd7f6] text-xs font-semibold flex items-center gap-1.5 transition-all"
                        title="Tailor your CV and cover letter for this specific posting"
                      >
                        <Sparkles className="w-3.5 h-3.5 text-[#4cd7f6]" />
                        <span>Tailor CV</span>
                      </button>

                      {onSelectForInterview && (
                        <button
                          onClick={() => onSelectForInterview(job.job_title, job.company, job.location, job.description)}
                          className="px-3 py-1.5 rounded-lg bg-[#1a1b22] border border-[#4edea3]/40 hover:bg-[#4edea3]/10 text-[#4edea3] text-xs font-semibold flex items-center gap-1.5 transition-all"
                          title="Generate STAR behavioral and technical interview questions for this job"
                        >
                          <MessageSquareCode className="w-3.5 h-3.5 text-[#4edea3]" />
                          <span>Prep Interview</span>
                        </button>
                      )}

                      {hasEmail && (
                        <button
                          onClick={() => handleBridgeOutreach(job)}
                          className="px-3 py-1.5 rounded-lg bg-[#4cd7f6] text-[#003640] text-xs font-semibold hover:bg-white transition-all flex items-center gap-1.5 cyan-glow"
                        >
                          <Send className="w-3.5 h-3.5" />
                          <span>Outreach</span>
                        </button>
                      )}

                      {job.portal && (
                        <a
                          href={job.portal}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-3 py-1.5 rounded-lg bg-[#292931] border border-[#3d494c]/40 text-[#e3e1ec] hover:text-white text-xs flex items-center gap-1.5 transition-all"
                        >
                          <span>Apply</span>
                          <ExternalLink className="w-3 h-3 text-[#4cd7f6]" />
                        </a>
                      )}
                    </div>
                  </div>

                  {/* Why this job fits this CV */}
                  {job.why_it_fits && (
                    <div className="p-2.5 rounded-lg bg-[#14151f] border border-[#3d494c]/30 text-xs text-[#bcc9cd] flex items-start gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-[#4edea3] shrink-0 mt-0.5" />
                      <div>
                        <strong className="text-[#4edea3] font-mono uppercase text-[10px] mr-1.5">
                          CV Semantic Match Insight:
                        </strong>
                        <span className="text-[#e3e1ec]">{job.why_it_fits}</span>
                      </div>
                    </div>
                  )}

                  {/* Matched Skills Pills & Details toggle */}
                  <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-[#3d494c]/20 text-xs">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="text-[10px] font-mono uppercase text-[#869296]">Matched Skills:</span>
                      {job.matched_skills && job.matched_skills.length > 0 ? (
                        job.matched_skills.map((s: string, sIdx: number) => (
                          <span
                            key={sIdx}
                            className="px-2 py-0.5 rounded bg-[#4edea3]/10 border border-[#4edea3]/30 text-[#4edea3] font-mono text-[10.5px]"
                          >
                            {s}
                          </span>
                        ))
                      ) : (
                        <span className="text-[11px] text-[#869296] italic">Direct Domain &amp; Title Match</span>
                      )}
                    </div>

                    <button
                      onClick={() => setActiveModalJob(job)}
                      className="text-[11px] font-mono text-[#4cd7f6] hover:underline"
                    >
                      Read Full Job Description &rarr;
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* MODAL: Full Job Description */}
      {activeModalJob && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="bg-[#0d0e15] border border-[#3d494c]/50 rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="p-6 border-b border-[#3d494c]/30 flex items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-[18px] font-bold text-[#e3e1ec]">
                    {activeModalJob.job_title}
                  </h2>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#4edea3]/10 text-[#4edea3] border border-[#4edea3]/30">
                    {activeModalJob.match_score}% Match
                  </span>
                </div>
                <div className="text-xs text-[#bcc9cd] mt-1 flex items-center gap-3">
                  <span className="text-[#4cd7f6] font-medium">{activeModalJob.company}</span>
                  <span>&bull;</span>
                  <span>{activeModalJob.location}</span>
                </div>
              </div>

              <button
                onClick={() => setActiveModalJob(null)}
                className="p-1.5 rounded-lg bg-[#1e1f26] text-[#bcc9cd] hover:text-[#e3e1ec]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto text-xs text-[#bcc9cd] leading-relaxed whitespace-pre-wrap font-sans space-y-4">
              {activeModalJob.why_it_fits && (
                <div className="p-3 rounded-lg bg-[#14151f] border border-[#4edea3]/30 text-xs">
                  <strong className="text-[#4edea3] font-mono uppercase text-[10px] block mb-1">
                    Why your CV matches this opening:
                  </strong>
                  <p className="text-[#e3e1ec]">{activeModalJob.why_it_fits}</p>
                </div>
              )}

              <div>
                <strong className="text-[#e3e1ec] font-mono uppercase text-[10px] block mb-2">
                  Full Job Description:
                </strong>
                <div className="p-4 rounded-lg bg-[#14151f] border border-[#3d494c]/20 max-h-[45vh] overflow-y-auto">
                  {activeModalJob.description || "No full description provided. Please use the official apply link."}
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-[#3d494c]/30 bg-[#12131a] flex items-center justify-between">
              <button
                onClick={() => {
                  handleBridgeTailor(activeModalJob);
                  setActiveModalJob(null);
                }}
                className="px-4 py-2 rounded-lg bg-[#4cd7f6] text-[#003640] font-semibold text-xs hover:bg-white transition-all flex items-center gap-1.5 cyan-glow"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Tailor CV for this Position</span>
              </button>

              {activeModalJob.portal && (
                <a
                  href={activeModalJob.portal}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-4 py-2 rounded-lg bg-[#292931] border border-[#3d494c]/40 text-[#e3e1ec] text-xs hover:text-white flex items-center gap-1.5"
                >
                  <span>Official Application ↗</span>
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
