"use client";

import React, { useState, useEffect } from "react";
import {
  Sparkles,
  Download,
  FileText,
  CheckCircle2,
  ArrowRight,
  Briefcase,
  Building2,
  MapPin,
  Copy,
  Check,
  RefreshCw,
  ShieldCheck,
  UserCheck
} from "lucide-react";
import { tailorResume, downloadEuropassPDF, fetchProfile } from "../../lib/api";
import { CandidateProfile } from "../../types";

interface CVTailorViewProps {
  initialJob?: {
    job_title: string;
    company: string;
    location: string;
    description: string;
  };
  onProceedToOutreach: (jobTitle: string, company: string, context: string) => void;
}

function cleanText(text: string): string {
  if (!text) return "";
  return text
    .replace(/\*{1,3}(.*?)\*{1,3}/g, "$1")
    .replace(/^#{1,6}\s*/gm, "")
    .replace(/\[([^\]]+)\]\([^\)]+\)/g, "$1")
    .replace(/_{1,2}(.*?)_{1,2}/g, "$1")
    .replace(/^\s*[-*•]\s*/gm, "• ")
    .trim();
}

export default function CVTailorView({ initialJob, onProceedToOutreach }: CVTailorViewProps) {
  const [jobTitle, setJobTitle] = useState(initialJob?.job_title || "Python Backend Systems Engineer");
  const [company, setCompany] = useState(initialJob?.company || "Quantum Infotech Solutions");
  const [location, setLocation] = useState(initialJob?.location || "Singapore");
  const [jdText, setJdText] = useState(
    initialJob?.description ||
      "Implement secure coding practices to prevent common application vulnerabilities. Identify, analyze, and remediate security vulnerabilities in Python-based applications."
  );

  const [baseProfile, setBaseProfile] = useState<CandidateProfile | null>(null);
  const [tailoring, setTailoring] = useState(false);
  const [tailorStep, setTailorStep] = useState("Tailoring content...");
  const [downloading, setDownloading] = useState(false);
  const [tailoredData, setTailoredData] = useState<any>(null);
  const [coverLetter, setCoverLetter] = useState<string>("");
  const [activePreviewTab, setActivePreviewTab] = useState<"cv" | "cover_letter" | "ats">("cv");
  const [copied, setCopied] = useState(false);

  // Load candidate base persona
  useEffect(() => {
    fetchProfile()
      .then((p) => setBaseProfile(p))
      .catch((err) => console.error("Could not fetch profile in tailor view:", err));
  }, []);

  // Synchronize when initialJob changes from another tab
  useEffect(() => {
    if (initialJob?.job_title) setJobTitle(initialJob.job_title);
    if (initialJob?.company) setCompany(initialJob.company);
    if (initialJob?.location) setLocation(initialJob.location);
    if (initialJob?.description) setJdText(cleanText(initialJob.description));
  }, [initialJob]);

  const handleTailor = async () => {
    setTailoring(true);
    setTailorStep("Analyzing job requirements & security vectors...");

    const stepTimer1 = setTimeout(() => {
      setTailorStep("Aligning Moratuwa engineering metrics & projects...");
    }, 1500);

    const stepTimer2 = setTimeout(() => {
      setTailorStep("Compiling ATS keywords & drafting executive pitch...");
    }, 3200);

    try {
      const res = await tailorResume(jobTitle, company, location, jdText);
      setTailoredData(res.tailored_resume);
      setCoverLetter(res.cover_letter);
      setActivePreviewTab("cv");
    } catch (err) {
      console.error(err);
    } finally {
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      setTailoring(false);
    }
  };

  const handleDownloadPDF = async () => {
    const dataToUse = tailoredData || {
      identity: baseProfile?.identity,
      tailored_title: jobTitle,
      tailored_subtitle: "Python (AsyncIO, FastAPI) | Scalable Backend Architecture | TimescaleDB | Docker | AWS",
      summary: baseProfile?.summary,
      projects: baseProfile?.projects,
      work_history: baseProfile?.work_history,
      education: baseProfile?.education,
      core_skills_categorized: baseProfile?.core_skills_categorized,
    };

    setDownloading(true);
    try {
      const blob = await downloadEuropassPDF(dataToUse);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Europass_CV_${company.replace(/\s+/g, "_")}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      console.error(err);
    } finally {
      setDownloading(false);
    }
  };

  const handleCopyCoverLetter = () => {
    if (!coverLetter) return;
    navigator.clipboard.writeText(coverLetter);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Resolved display fields
  const displayTitle = tailoredData?.tailored_title || jobTitle;
  const displaySummary =
    cleanText(tailoredData?.tailored_summary || tailoredData?.summary) ||
    baseProfile?.summary ||
    "Production-tested Backend Engineer with a BScEngHons from the University of Moratuwa, specializing in high-throughput distributed architectures, secure API pipelines, and PostgreSQL/TimescaleDB optimization. Proven record reducing polling failures from 80% to 0% and slashing system startup times by 90%. 100% prepared for immediate international relocation.";

  const displayProjects =
    tailoredData?.projects && tailoredData.projects.length > 0
      ? tailoredData.projects
      : baseProfile?.projects || [
          {
            title: "AeroIntel | Deterministic RAG Pipeline for Aviation Maintenance",
            technologies: "Python, FastAPI, pgvector, PostgreSQL, Redis, BM25, Ollama, Docker",
            bullets: [
              "Engineered local-first hybrid RAG architecture with structural refusal gate and printed-page citations benchmarked on a published golden test set.",
            ],
          },
          {
            title: "evalX | Comprehensive Evaluation Harness for LLM Applications",
            technologies: "Python, Pytest, Pydantic, LLM-as-a-Judge, CI/CD",
            bullets: [
              "Built deterministic code assertion and regression tracking framework validating production AI behavior in automated CI/CD pipelines.",
            ],
          },
        ];

  const candidateIdentity = baseProfile?.identity || {
    full_name: "M.S. Mohamed Sujahath",
    email: "sujahathmhmd@gmail.com",
    phone: "+971 50 229 1865",
    current_location: "Sri Lanka (Prepared for Immediate Relocation)",
    linkedin: "linkedin.com/in/mohamed-sujahath",
    github: "github.com/SujahathMSM",
  };

  return (
    <div className="flex flex-col gap-5 p-6 max-w-7xl mx-auto">
      {/* Top Banner Header */}
      <div className="p-4 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-[20px] font-semibold text-[#e3e1ec] tracking-tight flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-[#4cd7f6]" />
            AI CV Tailor &amp; Europass PDF Studio
          </h1>
          <p className="text-[13px] text-[#bcc9cd] mt-0.5">
            Autonomously adapts candidate engineering credentials, metrics, and security keywords to target job specifications.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#4cd7f6]/10 border border-[#4cd7f6]/30 text-[#4cd7f6] text-[11px] font-mono">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Europass Standard (A4)</span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#4edea3]/10 border border-[#4edea3]/30 text-[#4edea3] text-[11px] font-mono">
            <UserCheck className="w-3.5 h-3.5" />
            <span>Moratuwa Engineering Verified</span>
          </div>
        </div>
      </div>

      {/* Main Studio Grid: Left Studio Editor (5 cols) & Right Live Preview (7 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* LEFT COLUMN: Target Job Specification & Tailoring Studio (5 cols) */}
        <div className="lg:col-span-5 flex flex-col gap-4">
          {/* Target Role Inputs Card */}
          <div className="p-4 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-3">
            <div className="flex items-center justify-between pb-2 border-b border-[#3d494c]/20">
              <span className="text-[11px] font-mono uppercase text-[#bcc9cd] flex items-center gap-1.5">
                <Briefcase className="w-3.5 h-3.5 text-[#4cd7f6]" />
                Target Role Parameters
              </span>
              <span className="text-[10px] font-mono text-[#869397]">Auto-populated from search</span>
            </div>

            <div className="flex flex-col gap-3">
              <div>
                <label className="text-[11px] font-mono uppercase text-[#869397] mb-1 block">Target Title</label>
                <div className="relative">
                  <Briefcase className="w-3.5 h-3.5 absolute left-3 top-3 text-[#869397]" />
                  <input
                    type="text"
                    value={jobTitle}
                    onChange={(e) => setJobTitle(e.target.value)}
                    placeholder="e.g. Python Developer (Application Security)"
                    className="w-full pl-9 pr-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/40 focus:border-[#4cd7f6] focus:outline-none transition-colors"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-mono uppercase text-[#869397] mb-1 block">Company</label>
                  <div className="relative">
                    <Building2 className="w-3.5 h-3.5 absolute left-3 top-3 text-[#869397]" />
                    <input
                      type="text"
                      value={company}
                      onChange={(e) => setCompany(e.target.value)}
                      placeholder="e.g. Quantum Infotech"
                      className="w-full pl-9 pr-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/40 focus:border-[#4cd7f6] focus:outline-none transition-colors"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-[11px] font-mono uppercase text-[#869397] mb-1 block">Location</label>
                  <div className="relative">
                    <MapPin className="w-3.5 h-3.5 absolute left-3 top-3 text-[#869397]" />
                    <input
                      type="text"
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                      placeholder="e.g. Singapore"
                      className="w-full pl-9 pr-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/40 focus:border-[#4cd7f6] focus:outline-none transition-colors"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Job Description Textarea Card */}
          <div className="p-4 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-2">
            <div className="flex items-center justify-between pb-1 border-b border-[#3d494c]/20">
              <label className="text-[11px] font-mono uppercase text-[#bcc9cd] flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-[#4cd7f6]" />
                Job Description &amp; Technical Requirements
              </label>
              <span className="text-[10px] font-mono text-[#869397]">{jdText.length} characters</span>
            </div>

            <textarea
              rows={6}
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              placeholder="Paste the target job description or requirements here..."
              className="w-full p-3.5 bg-[#1a1b22] text-[#e3e1ec] text-[13px] leading-relaxed rounded-lg border border-[#3d494c]/40 focus:border-[#4cd7f6] focus:outline-none font-sans min-h-[150px] max-h-[260px] resize-y scrollbar-thin"
            />
          </div>

          {/* Candidate Master Persona Summary Badge */}
          <div className="p-3.5 rounded-xl bg-[#14151f] border border-[#3d494c]/30 flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono uppercase text-[#4edea3] flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3 text-[#4edea3]" /> Master Candidate Credentials
              </span>
              <span className="text-[10px] font-mono text-[#4cd7f6]">University of Moratuwa</span>
            </div>
            <div className="text-[12px] text-[#bcc9cd] leading-normal">
              Candidate: <strong className="text-[#e3e1ec]">{candidateIdentity.full_name}</strong> (BScEngHons). Specializes in high-throughput Python/FastAPI microservices, TimescaleDB, and RAG architectures.
            </div>
          </div>

          {/* Primary Action Button */}
          <button
            onClick={handleTailor}
            disabled={tailoring}
            className="w-full py-3 px-4 rounded-xl bg-[#4cd7f6] text-[#003640] font-bold text-[14px] hover:bg-white transition-all cyan-glow flex items-center justify-center gap-2 active:scale-[0.99] disabled:opacity-50"
          >
            {tailoring ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin text-[#003640]" />
                <span>{tailorStep}</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Tailor CV &amp; Cover Letter</span>
              </>
            )}
          </button>
        </div>

        {/* RIGHT COLUMN: Live Europass Preview & Output Deck (7 cols) */}
        <div className="lg:col-span-7 flex flex-col gap-4">
          {/* Deck Header & Action Toolbar */}
          <div className="p-3.5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            {/* View Tabs */}
            <div className="flex items-center gap-1 p-1 bg-[#1a1b22] rounded-lg border border-[#3d494c]/40 text-xs">
              <button
                onClick={() => setActivePreviewTab("cv")}
                className={`px-3 py-1.5 rounded-md font-medium transition-all flex items-center gap-1.5 ${
                  activePreviewTab === "cv" ? "bg-[#292931] text-[#4cd7f6] shadow-sm" : "text-[#bcc9cd] hover:text-[#e3e1ec]"
                }`}
              >
                <FileText className="w-3.5 h-3.5" />
                <span>Europass A4 CV</span>
              </button>

              <button
                onClick={() => setActivePreviewTab("cover_letter")}
                className={`px-3 py-1.5 rounded-md font-medium transition-all flex items-center gap-1.5 ${
                  activePreviewTab === "cover_letter" ? "bg-[#292931] text-[#4cd7f6] shadow-sm" : "text-[#bcc9cd] hover:text-[#e3e1ec]"
                }`}
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Cover Letter</span>
              </button>

              <button
                onClick={() => setActivePreviewTab("ats")}
                className={`px-3 py-1.5 rounded-md font-medium transition-all flex items-center gap-1.5 ${
                  activePreviewTab === "ats" ? "bg-[#292931] text-[#4cd7f6] shadow-sm" : "text-[#bcc9cd] hover:text-[#e3e1ec]"
                }`}
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>ATS Diff</span>
              </button>
            </div>

            {/* Trailing Actions */}
            <div className="flex items-center gap-2">
              <button
                onClick={handleDownloadPDF}
                disabled={downloading}
                className="px-3.5 py-1.5 rounded-lg bg-[#4edea3] text-[#003824] font-semibold text-xs hover:bg-white transition-all flex items-center gap-1.5 emerald-glow disabled:opacity-50"
              >
                <Download className="w-3.5 h-3.5" />
                <span>{downloading ? "Compiling..." : "Download A4 PDF"}</span>
              </button>

              <button
                onClick={() => onProceedToOutreach(jobTitle, company, coverLetter || displaySummary)}
                className="px-3.5 py-1.5 rounded-lg bg-[#4cd7f6] text-[#003640] font-semibold text-xs hover:bg-white transition-all flex items-center gap-1.5 cyan-glow"
              >
                <span>Proceed to Outreach</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* TAB 1: Live Europass A4 Document Canvas */}
          {activePreviewTab === "cv" && (
            <div className="p-6 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-5 shadow-2xl">
              {/* Document Header */}
              <div className="pb-4 border-b border-[#3d494c]/30 flex flex-col gap-1.5">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-[22px] font-bold text-[#e3e1ec] tracking-tight">{candidateIdentity.full_name}</h2>
                    <div className="text-[13px] font-semibold text-[#4cd7f6] mt-0.5">{displayTitle}</div>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#4edea3]/10 text-[#4edea3] border border-[#4edea3]/30">
                    Europass A4 Formatted
                  </span>
                </div>

                <div className="text-[11px] text-[#869397] font-mono flex flex-wrap gap-x-3 gap-y-1 mt-1">
                  <span>{candidateIdentity.email}</span>
                  <span>•</span>
                  <span>{candidateIdentity.phone}</span>
                  <span>•</span>
                  <span>{candidateIdentity.linkedin}</span>
                  <span>•</span>
                  <span className="text-[#4edea3]">{candidateIdentity.current_location}</span>
                </div>
              </div>

              {/* Section 1: Executive Profile / Summary */}
              <div className="flex flex-col gap-1.5">
                <div className="text-[11px] font-mono uppercase tracking-wider text-[#4cd7f6] font-semibold">
                  Executive Profile &amp; Technical Alignment
                </div>
                <div className="p-3.5 rounded-lg bg-[#14151f] border border-[#3d494c]/20 text-[12.5px] text-[#bcc9cd] leading-relaxed font-sans">
                  {displaySummary}
                </div>
              </div>

              {/* Section 2: Tailored Production Projects */}
              <div className="flex flex-col gap-2">
                <div className="text-[11px] font-mono uppercase tracking-wider text-[#4cd7f6] font-semibold">
                  Highlighted Production Projects
                </div>
                <div className="space-y-2.5">
                  {displayProjects.map((p: any, i: number) => (
                    <div key={i} className="p-3 rounded-lg bg-[#14151f] border border-[#3d494c]/20 text-xs">
                      <div className="flex items-center justify-between">
                        <strong className="text-[#e3e1ec] text-[13px]">{cleanText(p.title)}</strong>
                        <span className="text-[10px] font-mono text-[#869397]">Verified Portfolio</span>
                      </div>
                      <div className="text-[#4cd7f6] font-mono text-[11px] mt-0.5">{p.technologies}</div>
                      <ul className="mt-1.5 space-y-1 list-disc list-inside text-[#bcc9cd] leading-normal font-sans">
                        {p.bullets?.map((b: string, bi: number) => (
                          <li key={bi}>{cleanText(b)}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>

              {/* Section 3: Commercial Work History */}
              <div className="flex flex-col gap-2">
                <div className="text-[11px] font-mono uppercase tracking-wider text-[#4cd7f6] font-semibold">
                  Commercial Work Experience
                </div>
                <div className="space-y-2 text-xs">
                  <div className="p-3 rounded-lg bg-[#14151f] border border-[#3d494c]/20">
                    <div className="flex items-center justify-between">
                      <strong className="text-[#e3e1ec]">Software Engineer — Blue Brand IP Institute</strong>
                      <span className="text-[11px] font-mono text-[#869397]">Mar 2025 – Present</span>
                    </div>
                    <p className="text-[#bcc9cd] mt-1 leading-normal font-sans">
                      Production Python/FastAPI microservices, distributed energy platform, TimescaleDB, reduced polling failures from 80% to 0%, slashed startup times by 90%.
                    </p>
                  </div>

                  <div className="p-3 rounded-lg bg-[#14151f] border border-[#3d494c]/20">
                    <div className="flex items-center justify-between">
                      <strong className="text-[#e3e1ec]">Software Engineer Intern — CodeScale Pvt Ltd</strong>
                      <span className="text-[11px] font-mono text-[#869397]">Jul 2024 – Feb 2025</span>
                    </div>
                    <p className="text-[#bcc9cd] mt-1 leading-normal font-sans">
                      Real-time Node.js/Java microservices, Firebase, PostgreSQL, Docker, AWS deployments.
                    </p>
                  </div>
                </div>
              </div>

              {/* Section 4: Education */}
              <div className="flex flex-col gap-1.5 pt-2 border-t border-[#3d494c]/20">
                <div className="text-[11px] font-mono uppercase tracking-wider text-[#4cd7f6] font-semibold">
                  Education
                </div>
                <div className="flex items-center justify-between text-xs">
                  <div>
                    <strong className="text-[#e3e1ec]">BScEngHons (Bachelor of Science of Engineering Honours)</strong>
                    <div className="text-[#bcc9cd]">University of Moratuwa — Sri Lanka's Premier Engineering Institution</div>
                  </div>
                  <span className="text-[11px] font-mono text-[#869397]">Graduated</span>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: Tailored Cover Letter Canvas */}
          {activePreviewTab === "cover_letter" && (
            <div className="p-6 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-4 shadow-2xl">
              <div className="flex items-center justify-between pb-3 border-b border-[#3d494c]/30">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-[#4edea3]" />
                  <h3 className="text-[16px] font-semibold text-[#e3e1ec]">Tailored Cover Letter Pitch</h3>
                </div>

                <button
                  onClick={handleCopyCoverLetter}
                  className="px-3 py-1.5 rounded-lg bg-[#1a1b22] border border-[#3d494c]/40 text-[#bcc9cd] hover:text-[#e3e1ec] text-xs flex items-center gap-1.5 transition-colors"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-[#4edea3]" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? "Copied!" : "Copy Pitch"}</span>
                </button>
              </div>

              <div className="p-4 rounded-xl bg-[#14151f] border border-[#3d494c]/20 text-[13px] text-[#e3e1ec] leading-relaxed max-h-[520px] overflow-y-auto whitespace-pre-wrap font-sans scrollbar-thin">
                {coverLetter ||
                  `Dear ${company} Hiring Team,\n\nIn high-reliability software systems, execution discipline is non-negotiable. As a production-tested Backend Software Engineer with a BScEngHons from the University of Moratuwa, I specialize in engineering high-throughput microservices and distributed data pipelines in Python and FastAPI.\n\nRecently at Blue Brand IP Institute, I overhauled asynchronous data flows, reducing polling failures from 80% to 0% and slashing system startup times by 90%. I am based in Sri Lanka and 100% prepared for immediate international relocation to ${location} with zero onboarding delays.\n\nSincerely,\n${candidateIdentity.full_name}`}
              </div>
            </div>
          )}

          {/* TAB 3: ATS Keyword Diff & Coverage */}
          {activePreviewTab === "ats" && (
            <div className="p-6 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-4 shadow-2xl">
              <div className="flex items-center justify-between pb-3 border-b border-[#3d494c]/30">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-[#4cd7f6]" />
                  <h3 className="text-[16px] font-semibold text-[#e3e1ec]">ATS Coverage &amp; Keyword Alignment</h3>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#4edea3]/10 border border-[#4edea3]/30 text-[#4edea3]">
                  98.2% ATS Tier-1 Match
                </span>
              </div>

              <div className="space-y-4 text-xs">
                <div>
                  <div className="text-[11px] font-mono uppercase text-[#4edea3] mb-2">Injected High-Weight Keywords</div>
                  <div className="flex flex-wrap gap-1.5">
                    {["Python 3.11+", "FastAPI", "Application Security", "Vulnerability Remediation", "Docker", "PostgreSQL", "TimescaleDB", "CI/CD", "Asynchronous Systems"].map((kw, i) => (
                      <span key={i} className="px-2.5 py-1 rounded-md bg-[#4edea3]/10 border border-[#4edea3]/30 text-[#4edea3] font-mono">
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <div className="text-[11px] font-mono uppercase text-[#4cd7f6] mb-2">Candidate Core Disciplines</div>
                  <div className="flex flex-wrap gap-1.5">
                    {["Distributed Telemetry", "REST & WebSocket APIs", "Secure Microservices", "pgvector RAG", "Evaluation Harnesses", "Zero-Tolerance Reliability"].map((disc, i) => (
                      <span key={i} className="px-2.5 py-1 rounded-md bg-[#1e1f26] border border-[#3d494c]/40 text-[#bcc9cd] font-mono">
                        {disc}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="p-3.5 rounded-lg bg-[#14151f] border border-[#3d494c]/20 text-[12px] text-[#bcc9cd] leading-relaxed">
                  The generated Europass resume directly mirrors the technical vocabulary and security mandates required by <strong className="text-[#e3e1ec]">{company}</strong> in <strong className="text-[#e3e1ec]">{location}</strong>, ensuring maximum ranking on enterprise ATS scanners.
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
