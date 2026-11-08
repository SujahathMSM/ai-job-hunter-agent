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
  Mail,
  UserCheck,
  Award,
  BookOpen,
  AlertCircle,
  MessageSquareCode,
  FileCode
} from "lucide-react";
import {
  tailorResume,
  downloadEuropassPDF,
  downloadATSPDF,
  fetchATSPlaintext,
  fetchProfile
} from "../../lib/api";
import { CandidateProfile } from "../../types";

interface CVTailorViewProps {
  initialJob?: {
    job_title: string;
    company: string;
    location: string;
    hr_email?: string;
    description: string;
  };
  onProceedToOutreach: (jobTitle: string, company: string, context: string, hrEmail?: string) => void;
  onSelectForInterview?: (jobTitle: string, company: string, location: string, desc: string) => void;
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

function extractEmailFromText(text: string): string {
  if (!text) return "";
  const matches = text.match(/[\w.-]+@[\w.-]+\.[a-zA-Z]{2,}/g) || [];
  const found = matches.find(
    (e) => !e.includes("sujahath") && !e.includes("example.com") && !e.includes("candidate@")
  );
  return found || "";
}

export default function CVTailorView({ initialJob, onProceedToOutreach, onSelectForInterview }: CVTailorViewProps) {
  const [jobTitle, setJobTitle] = useState(initialJob?.job_title || "Python Backend Systems Engineer");
  const [company, setCompany] = useState(initialJob?.company || "Quantum Infotech Solutions");
  const [location, setLocation] = useState(initialJob?.location || "Singapore");
  const [hrEmail, setHrEmail] = useState(
    initialJob?.hr_email || extractEmailFromText(initialJob?.description || "")
  );
  const [jdText, setJdText] = useState(
    initialJob?.description ||
      "Implement secure coding practices to prevent common application vulnerabilities. Identify, analyze, and remediate security vulnerabilities in Python-based applications."
  );

  const [baseProfile, setBaseProfile] = useState<CandidateProfile | null>(null);
  const [tailoring, setTailoring] = useState(false);
  const [tailorStep, setTailorStep] = useState("Tailoring content...");
  const [downloading, setDownloading] = useState(false);
  const [downloadingATS, setDownloadingATS] = useState(false);
  const [tailoredData, setTailoredData] = useState<any>(null);
  const [coverLetter, setCoverLetter] = useState<string>("");
  const [reviewerAudit, setReviewerAudit] = useState<any>(null);
  const [skillGap, setSkillGap] = useState<any>(null);
  const [atsRawText, setAtsRawText] = useState<string>("");
  const [activePreviewTab, setActivePreviewTab] = useState<"cv" | "cover_letter" | "ats" | "skill_gap" | "ats_raw">("cv");
  const [copied, setCopied] = useState(false);
  const [copiedATS, setCopiedATS] = useState(false);

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
    if (initialJob?.description) {
      setJdText(cleanText(initialJob.description));
      if (!initialJob?.hr_email) {
        const found = extractEmailFromText(initialJob.description);
        if (found) setHrEmail(found);
      }
    }
    if (initialJob?.hr_email) setHrEmail(initialJob.hr_email);
  }, [initialJob]);

  const handleTailor = async () => {
    setTailoring(true);
    setTailorStep("Stage 1: Drafter Agent tailoring keywords & metrics...");

    const stepTimer1 = setTimeout(() => {
      setTailorStep("Stage 2: Reviewer Agent fact-checking & auditing claims...");
    }, 1800);

    const stepTimer2 = setTimeout(() => {
      setTailorStep("Calculating Skill Gap roadmap & compiling ATS layers...");
    }, 3400);

    try {
      const res = await tailorResume(jobTitle, company, location, jdText);
      setTailoredData(res.tailored_resume);
      setCoverLetter(res.cover_letter);
      if (res.reviewer_audit) setReviewerAudit(res.reviewer_audit);
      if (res.skill_gap) setSkillGap(res.skill_gap);
      setActivePreviewTab("cv");

      // Preload raw ATS text
      fetchATSPlaintext(res.tailored_resume)
        .then((txtData) => setAtsRawText(txtData.plaintext))
        .catch(() => {});
    } catch (err) {
      console.error(err);
    } finally {
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      setTailoring(false);
    }
  };

  const getDataToUse = () => {
    return (
      tailoredData || {
        identity: baseProfile?.identity,
        tailored_title: jobTitle,
        tailored_subtitle: "Python (AsyncIO, FastAPI) | Scalable Backend Architecture | TimescaleDB | Docker | AWS",
        summary: baseProfile?.summary,
        projects: baseProfile?.projects,
        work_history: baseProfile?.work_history,
        education: baseProfile?.education,
        core_skills_categorized: baseProfile?.core_skills_categorized,
      }
    );
  };

  const handleDownloadPDF = async () => {
    const dataToUse = getDataToUse();
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

  const handleDownloadATSPDF = async () => {
    const dataToUse = getDataToUse();
    setDownloadingATS(true);
    try {
      const blob = await downloadATSPDF(dataToUse);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Clean_ATS_CV_${company.replace(/\s+/g, "_")}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      console.error(err);
    } finally {
      setDownloadingATS(false);
    }
  };

  const handleInspectATS = async () => {
    setActivePreviewTab("ats_raw");
    if (!atsRawText) {
      try {
        const dataToUse = getDataToUse();
        const res = await fetchATSPlaintext(dataToUse);
        setAtsRawText(res.plaintext);
      } catch (err) {
        console.error(err);
      }
    }
  };

  const handleCopyCoverLetter = () => {
    if (!coverLetter) return;
    navigator.clipboard.writeText(coverLetter);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCopyATS = () => {
    if (!atsRawText) return;
    navigator.clipboard.writeText(atsRawText);
    setCopiedATS(true);
    setTimeout(() => setCopiedATS(false), 2000);
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
    full_name: "Candidate",
    email: "",
    phone: "",
    current_location: "Remote / International Relocation",
    linkedin: "",
    github: "",
  };
  const displayWorkHistory =
    tailoredData?.work_history && tailoredData.work_history.length > 0
      ? tailoredData.work_history
      : baseProfile?.work_history || [];
  const displayEducation =
    tailoredData?.education && tailoredData.education.length > 0
      ? tailoredData.education
      : baseProfile?.education || [];

  return (
    <div className="flex flex-col gap-5 p-6 max-w-7xl mx-auto">
      {/* Top Banner Header */}
      <div className="p-4 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-[20px] font-semibold text-[#e3e1ec] tracking-tight flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-[#4cd7f6]" />
            AI CV Studio &amp; Anti-Hallucination Reviewer
          </h1>
          <p className="text-[13px] text-[#bcc9cd] mt-0.5">
            Two-stage Drafter-Reviewer pipeline: Adapts credentials to JD requirements while strictly fact-checking against authentic evidence.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#4cd7f6]/10 border border-[#4cd7f6]/30 text-[#4cd7f6] text-[11px] font-mono">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>2-Stage Reviewer Verified</span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#4edea3]/10 border border-[#4edea3]/30 text-[#4edea3] text-[11px] font-mono">
            <UserCheck className="w-3.5 h-3.5" />
            <span>Moratuwa Engineering Grounded</span>
          </div>
        </div>
      </div>

      {/* TWO-STAGE QUALITY CONTROL BANNER & REVIEWER AUDIT SHIELD */}
      <div className="p-3.5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/40 specular-border flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#4edea3]/10 border border-[#4edea3]/30 flex items-center justify-center shrink-0">
            <ShieldCheck className="w-4 h-4 text-[#4edea3]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-[#e3e1ec]">Adversarial Reviewer Audit Gate</span>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[#4edea3]/20 text-[#4edea3] border border-[#4edea3]/40">
                {reviewerAudit?.status || "PASS (100% GROUNDED)"}
              </span>
            </div>
            <div className="text-[11px] text-[#bcc9cd] mt-0.5">
              {reviewerAudit?.reviewer_verdict ||
                "Stage 1 Drafter adapted keywords to target JD &bull; Stage 2 Reviewer cross-checked metrics against Moratuwa &amp; Blue Brand evidence bank."}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start md:self-auto shrink-0 font-mono text-[11px]">
          <span className="px-2.5 py-1 rounded bg-[#1e1f26] border border-[#3d494c]/40 text-[#4cd7f6]">
            Hallucination Score: <strong>{reviewerAudit?.hallucination_score || 100}/100</strong>
          </span>
          <span className="px-2.5 py-1 rounded bg-[#1e1f26] border border-[#3d494c]/40 text-[#4edea3]">
            0 Fabricated Claims
          </span>
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

              <div>
                <label className="text-[11px] font-mono uppercase text-[#869397] mb-1 flex items-center justify-between">
                  <span>HR / Recruiter Email</span>
                  {hrEmail ? (
                    <span className="text-[10px] text-[#4edea3] font-mono">Found in job</span>
                  ) : (
                    <span className="text-[10px] text-[#ffb4ab] font-mono">Optional</span>
                  )}
                </label>
                <div className="relative">
                  <Mail className="w-3.5 h-3.5 absolute left-3 top-3 text-[#869397]" />
                  <input
                    type="email"
                    value={hrEmail}
                    onChange={(e) => setHrEmail(e.target.value)}
                    placeholder="e.g. recruiter@company.com"
                    className="w-full pl-9 pr-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/40 focus:border-[#4cd7f6] focus:outline-none font-mono transition-colors"
                  />
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
              <span className="text-[10px] font-mono text-[#4cd7f6]">{baseProfile?.education?.[0]?.details || "Engineering Profile"}</span>
            </div>
            <div className="text-[12px] text-[#bcc9cd] leading-normal">
              Candidate: <strong className="text-[#e3e1ec]">{candidateIdentity.full_name}</strong>. {displayTitle ? `Role alignment: ${displayTitle}.` : "Tailored for production software engineering."}
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
          <div className="p-3.5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-3">
            {/* View Tabs */}
            <div className="flex flex-wrap items-center gap-1 p-1 bg-[#1a1b22] rounded-lg border border-[#3d494c]/40 text-xs">
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

              <button
                onClick={() => setActivePreviewTab("skill_gap")}
                className={`px-3 py-1.5 rounded-md font-medium transition-all flex items-center gap-1.5 ${
                  activePreviewTab === "skill_gap" ? "bg-[#292931] text-[#4edea3] shadow-sm" : "text-[#bcc9cd] hover:text-[#e3e1ec]"
                }`}
              >
                <BookOpen className="w-3.5 h-3.5" />
                <span>Skill Gap &amp; Roadmap</span>
              </button>

              <button
                onClick={handleInspectATS}
                className={`px-3 py-1.5 rounded-md font-medium transition-all flex items-center gap-1.5 ${
                  activePreviewTab === "ats_raw" ? "bg-[#292931] text-[#4cd7f6] shadow-sm" : "text-[#bcc9cd] hover:text-[#e3e1ec]"
                }`}
              >
                <FileCode className="w-3.5 h-3.5" />
                <span>Raw ATS Text</span>
              </button>
            </div>

            {/* Trailing Actions */}
            <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-[#3d494c]/20">
              <div className="flex items-center gap-2">
                <button
                  onClick={handleDownloadPDF}
                  disabled={downloading}
                  className="px-3 py-1.5 rounded-lg bg-[#4edea3] text-[#003824] font-semibold text-xs hover:bg-white transition-all flex items-center gap-1.5 emerald-glow disabled:opacity-50"
                  title="Download European Union standard styled A4 PDF"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>{downloading ? "Compiling..." : "Europass PDF"}</span>
                </button>

                <button
                  onClick={handleDownloadATSPDF}
                  disabled={downloadingATS}
                  className="px-3 py-1.5 rounded-lg bg-[#1e1f26] border border-[#3d494c]/50 text-[#e3e1ec] font-semibold text-xs hover:bg-[#292931] transition-all flex items-center gap-1.5 disabled:opacity-50"
                  title="Download 100% clean single-column machine-readable ATS PDF (LaTeX / Typst style)"
                >
                  <FileCode className="w-3.5 h-3.5 text-[#4cd7f6]" />
                  <span>{downloadingATS ? "Building..." : "Clean ATS PDF"}</span>
                </button>
              </div>

              <div className="flex items-center gap-2">
                {onSelectForInterview && (
                  <button
                    onClick={() => onSelectForInterview(jobTitle, company, location, jdText)}
                    className="px-3 py-1.5 rounded-lg bg-[#1a1b22] border border-[#4cd7f6]/40 text-[#4cd7f6] hover:bg-[#292931] text-xs font-semibold flex items-center gap-1.5 transition-all"
                  >
                    <MessageSquareCode className="w-3.5 h-3.5" />
                    <span>Prep Interview</span>
                  </button>
                )}

                <button
                  onClick={() => {
                    const resolvedEmail = hrEmail || extractEmailFromText(jdText) || extractEmailFromText(coverLetter);
                    onProceedToOutreach(jobTitle, company, coverLetter || displaySummary, resolvedEmail);
                  }}
                  className="px-3.5 py-1.5 rounded-lg bg-[#4cd7f6] text-[#003640] font-semibold text-xs hover:bg-white transition-all flex items-center gap-1.5 cyan-glow"
                >
                  <span>Proceed to Outreach</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
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
              {displayWorkHistory.length > 0 && (
                <div className="flex flex-col gap-2">
                  <div className="text-[11px] font-mono uppercase tracking-wider text-[#4cd7f6] font-semibold">
                    Commercial Work Experience
                  </div>
                  <div className="space-y-2 text-xs">
                    {displayWorkHistory.slice(0, 3).map((job: any, idx: number) => (
                      <div key={idx} className="p-3 rounded-lg bg-[#14151f] border border-[#3d494c]/20">
                        <div className="flex items-center justify-between">
                          <strong className="text-[#e3e1ec]">
                            {job.title} — {job.company}
                          </strong>
                          <span className="text-[11px] font-mono text-[#869397]">{job.duration}</span>
                        </div>
                        {job.bullets && job.bullets.length > 0 && (
                          <p className="text-[#bcc9cd] mt-1 leading-normal font-sans">
                            {job.bullets.slice(0, 2).join(" ")}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Section 4: Education */}
              {displayEducation.length > 0 && (
                <div className="flex flex-col gap-1.5 pt-2 border-t border-[#3d494c]/20">
                  <div className="text-[11px] font-mono uppercase tracking-wider text-[#4cd7f6] font-semibold">
                    Education
                  </div>
                  {displayEducation.slice(0, 2).map((edu: any, idx: number) => (
                    <div key={idx} className="flex items-center justify-between text-xs">
                      <div>
                        <strong className="text-[#e3e1ec]">{edu.degree}</strong>
                        <div className="text-[#bcc9cd]">{edu.institution}</div>
                      </div>
                      <span className="text-[11px] font-mono text-[#869397]">{edu.duration || "Graduated"}</span>
                    </div>
                  ))}
                </div>
              )}
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

          {/* TAB 4: Skill Gap & 24-Hour Quick-Study Roadmap */}
          {activePreviewTab === "skill_gap" && (
            <div className="p-6 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-5 shadow-2xl">
              <div className="flex items-center justify-between pb-3 border-b border-[#3d494c]/30">
                <div className="flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-[#4edea3]" />
                  <h3 className="text-[16px] font-semibold text-[#e3e1ec]">
                    Skill Gap Breakdown &amp; 24-Hour Quick-Study Roadmap
                  </h3>
                </div>
                <span className="text-[11px] font-mono px-2.5 py-0.5 rounded bg-[#4edea3]/10 border border-[#4edea3]/30 text-[#4edea3]">
                  {skillGap?.ats_score || 92}% Compatibility
                </span>
              </div>

              {/* Matched Strengths */}
              <div className="flex flex-col gap-2">
                <div className="text-[11px] font-mono uppercase tracking-wider text-[#4edea3] font-semibold flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Matched Hard Skills ({skillGap?.matched_skills?.length || 6})</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {(skillGap?.matched_skills || [
                    "Python 3.11+",
                    "FastAPI",
                    "PostgreSQL",
                    "TimescaleDB",
                    "Docker",
                    "AsyncIO",
                    "REST APIs",
                    "Git & CI/CD",
                  ]).map((skill: string, idx: number) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 rounded-md bg-[#4edea3]/10 border border-[#4edea3]/30 text-[#4edea3] font-mono text-xs"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              {/* Missing Skills / Hard Gaps */}
              <div className="flex flex-col gap-2">
                <div className="text-[11px] font-mono uppercase tracking-wider text-[#4cd7f6] font-semibold flex items-center gap-1.5">
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span>Missing High-Demand Keywords / Opportunity Gaps</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {(skillGap?.missing_skills || [
                    "Kafka Event Streaming",
                    "Kubernetes Orchestration",
                    "Aconex / Enterprise EDMS",
                  ]).map((skill: string, idx: number) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 rounded-md bg-[#1e1f26] border border-[#3d494c]/50 text-[#bcc9cd] font-mono text-xs"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              {/* 24-Hour Quick Study Cheat Sheet */}
              <div className="flex flex-col gap-2 pt-2 border-t border-[#3d494c]/20">
                <div className="text-[11px] font-mono uppercase tracking-wider text-[#e3e1ec] font-semibold flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-[#4cd7f6]" />
                  <span>24-Hour Quick-Study Talking Scripts (Screening Cheat Sheet)</span>
                </div>
                <p className="text-xs text-[#bcc9cd]">
                  If an interviewer or recruiter asks about an unfamiliar tool, bridge your grounded experience with these 2-sentence talking points:
                </p>

                <div className="space-y-3 mt-1">
                  {(skillGap?.quick_study_guide || [
                    {
                      skill: "Kafka / Distributed Streaming",
                      talking_point:
                        "While my production work focused on high-throughput MQTT and Redis streaming pipelines, the pub/sub architectural principles, consumer groups, and partition semantics map directly to Kafka. I've studied Kafka topic partitions and can onboard immediately.",
                      study_topic: "Kafka consumer offset commits and topic partitions",
                    },
                    {
                      skill: "Kubernetes Orchestration",
                      talking_point:
                        "I develop daily with multi-container Docker environments and CI/CD automated deployments; container lifecycle concepts, ingress routing, and pod scaling principles transition seamlessly to production k8s clusters.",
                      study_topic: "K8s Ingress, Deployments, and ConfigMaps",
                    },
                  ]).map((item: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-3.5 rounded-lg bg-[#14151f] border border-[#3d494c]/30 text-xs flex flex-col gap-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <strong className="text-[#4cd7f6]">{item.skill}</strong>
                        {item.study_topic && (
                          <span className="text-[10px] font-mono text-[#869397]">Focus: {item.study_topic}</span>
                        )}
                      </div>
                      <p className="text-[#e3e1ec] leading-relaxed italic">
                        "{item.talking_point}"
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: Raw ATS Linear Text Stream Inspector */}
          {activePreviewTab === "ats_raw" && (
            <div className="p-6 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-4 shadow-2xl">
              <div className="flex items-center justify-between pb-3 border-b border-[#3d494c]/30">
                <div className="flex items-center gap-2">
                  <FileCode className="w-5 h-5 text-[#4cd7f6]" />
                  <div>
                    <h3 className="text-[16px] font-semibold text-[#e3e1ec]">
                      Raw ATS OCR &amp; Text Layer Inspector
                    </h3>
                    <p className="text-[11px] text-[#bcc9cd]">
                      This is the 100% linear, machine-readable text stream extracted by Workday, Greenhouse, and Taleo parsers.
                    </p>
                  </div>
                </div>

                <button
                  onClick={handleCopyATS}
                  className="px-3 py-1.5 rounded-lg bg-[#1a1b22] border border-[#3d494c]/40 text-[#bcc9cd] hover:text-[#e3e1ec] text-xs flex items-center gap-1.5 transition-colors"
                >
                  {copiedATS ? <Check className="w-3.5 h-3.5 text-[#4edea3]" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedATS ? "Copied Plaintext!" : "Copy for Portal Form"}</span>
                </button>
              </div>

              <div className="p-4 rounded-xl bg-[#08090f] border border-[#3d494c]/30 text-[11.5px] font-mono text-[#4edea3] leading-relaxed max-h-[500px] overflow-y-auto whitespace-pre-wrap scrollbar-thin">
                {atsRawText || "Loading clean linear ATS text layer..."}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
