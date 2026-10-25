"use client";

import React, { useEffect, useState } from "react";
import {
  UserCheck,
  UploadCloud,
  FileText,
  CheckCircle2,
  Briefcase,
  GraduationCap,
  Code,
  Github,
  Linkedin,
  Globe,
  MessageSquare,
  Sparkles,
  Download,
  Trash2,
  ExternalLink,
  RefreshCw,
  AlertCircle,
  Plus,
  Layers,
  ChevronDown,
  ChevronUp
} from "lucide-react";
import { CandidateProfile } from "../../types";
import {
  fetchProfile,
  uploadMultipleCVs,
  uploadChatHistory,
  parseGitHub,
  parseLinkedIn,
  parsePersonalWebsite,
  synthesizeMasterProfile,
  downloadDefaultEuropassCV,
  saveSettings
} from "../../lib/api";

export default function ProfileView() {
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  // Intake States
  const [uploadedCVs, setUploadedCVs] = useState<any[]>([]);
  const [chatInsights, setChatInsights] = useState<any[]>([]);
  const [githubData, setGithubData] = useState<any>(null);
  const [linkedinData, setLinkedinData] = useState<any>(null);
  const [websiteData, setWebsiteData] = useState<any>(null);

  // Form Inputs
  const [githubInput, setGithubInput] = useState("https://github.com/SujahathMSM");
  const [linkedinInput, setLinkedinInput] = useState("https://linkedin.com/in/sujahath-siddeek");
  const [websiteInput, setWebsiteInput] = useState("");
  const [linkedinRawText, setLinkedinRawText] = useState("");

  // Loading States
  const [uploadingCVs, setUploadingCVs] = useState(false);
  const [uploadingChats, setUploadingChats] = useState(false);
  const [fetchingGithub, setFetchingGithub] = useState(false);
  const [fetchingLinkedin, setFetchingLinkedin] = useState(false);
  const [fetchingWebsite, setFetchingWebsite] = useState(false);
  const [synthesizing, setSynthesizing] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);

  // Status message
  const [statusMsg, setStatusMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [showIntakeStudio, setShowIntakeStudio] = useState(true);

  const loadProfile = () => {
    setLoading(true);
    setFetchError(null);
    fetchProfile()
      .then((p) => {
        setProfile(p);
        if (p?.identity?.github) setGithubInput(p.identity.github);
        if (p?.identity?.linkedin) setLinkedinInput(p.identity.linkedin);
        if (p?.identity?.website) setWebsiteInput(p.identity.website);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Profile load err:", err);
        setFetchError("Could not reach backend API at /api/profile.");
        setLoading(false);
      });
  };

  useEffect(() => {
    loadProfile();
  }, []);

  // 1. Multiple CV Upload
  const handleMultipleCVUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const fileList = Array.from(e.target.files);
    setUploadingCVs(true);
    setStatusMsg(null);
    try {
      const res = await uploadMultipleCVs(fileList);
      setUploadedCVs((prev) => [...prev, ...(res.cvs || [])]);
      setStatusMsg({
        type: "success",
        text: `Successfully parsed ${fileList.length} CV document(s). Ready to synthesize!`,
      });
    } catch (err: any) {
      setStatusMsg({ type: "error", text: err.message || "Failed to parse CV documents." });
    } finally {
      setUploadingCVs(false);
    }
  };

  // 2. Chat History Upload
  const handleChatUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const fileList = Array.from(e.target.files);
    setUploadingChats(true);
    setStatusMsg(null);
    try {
      const res = await uploadChatHistory(fileList);
      setChatInsights((prev) => [...prev, ...(res.insights || [])]);
      setStatusMsg({
        type: "success",
        text: `Extracted ${res.count || fileList.length} engineering conversation insight(s) from LLM chats.`,
      });
    } catch (err: any) {
      setStatusMsg({ type: "error", text: err.message || "Failed to parse chat history." });
    } finally {
      setUploadingChats(false);
    }
  };

  // 3. GitHub Profile Parsing
  const handleParseGithub = async () => {
    if (!githubInput.trim()) return;
    setFetchingGithub(true);
    setStatusMsg(null);
    try {
      const res = await parseGitHub(githubInput.trim());
      setGithubData(res.github);
      setStatusMsg({
        type: "success",
        text: `Synced GitHub: Found ${res.github?.repositories?.length || 0} public repositories!`,
      });
    } catch (err: any) {
      setStatusMsg({ type: "error", text: err.message || "Failed to fetch GitHub profile." });
    } finally {
      setFetchingGithub(false);
    }
  };

  // 4. LinkedIn Profile Parsing
  const handleParseLinkedin = async () => {
    if (!linkedinInput.trim() && !linkedinRawText.trim()) return;
    setFetchingLinkedin(true);
    setStatusMsg(null);
    try {
      const res = await parseLinkedIn(linkedinInput.trim(), linkedinRawText.trim());
      setLinkedinData(res.linkedin);
      setStatusMsg({
        type: "success",
        text: "Parsed LinkedIn data and extracted headline & skills successfully!",
      });
    } catch (err: any) {
      setStatusMsg({ type: "error", text: err.message || "Failed to parse LinkedIn." });
    } finally {
      setFetchingLinkedin(false);
    }
  };

  // 5. Personal Website Scraping
  const handleScrapeWebsite = async () => {
    if (!websiteInput.trim()) return;
    setFetchingWebsite(true);
    setStatusMsg(null);
    try {
      const res = await parsePersonalWebsite(websiteInput.trim());
      setWebsiteData(res.website);
      setStatusMsg({
        type: "success",
        text: `Scraped portfolio website: "${res.website?.title || websiteInput}"`,
      });
    } catch (err: any) {
      setStatusMsg({ type: "error", text: err.message || "Failed to scrape website." });
    } finally {
      setFetchingWebsite(false);
    }
  };

  // 6. Master Synthesizer (Merge Everything)
  const handleSynthesize = async () => {
    setSynthesizing(true);
    setStatusMsg(null);
    try {
      const res = await synthesizeMasterProfile({
        cv_sources: uploadedCVs,
        chat_sources: chatInsights,
        github_data: githubData,
        linkedin_data: linkedinData,
        website_data: websiteData,
      });
      setProfile(res.profile);
      setStatusMsg({
        type: "success",
        text: "⚡ Master Persona successfully synthesized and updated from all intake sources!",
      });
    } catch (err: any) {
      setStatusMsg({ type: "error", text: err.message || "Failed to synthesize profile." });
    } finally {
      setSynthesizing(false);
    }
  };

  // 7. Default Europass Download
  const handleDownloadEuropass = async () => {
    setDownloadingPdf(true);
    try {
      const blob = await downloadDefaultEuropassCV();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Europass_CV_MS_Mohamed_Sujahath.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      alert("Failed to compile Europass CV PDF: " + err.message);
    } finally {
      setDownloadingPdf(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-[#bcc9cd] flex flex-col items-center gap-3">
        <div className="w-6 h-6 border-2 border-[#4cd7f6] border-t-transparent rounded-full animate-spin"></div>
        <span>Loading Candidate Master Persona...</span>
      </div>
    );
  }

  if (fetchError || !profile) {
    return (
      <div className="p-12 text-center text-[#ffb4ab] flex flex-col items-center gap-3">
        <p>{fetchError || "Profile not loaded."}</p>
        <button
          onClick={loadProfile}
          className="px-4 py-2 bg-[#4cd7f6] text-[#003640] rounded-lg text-xs font-semibold hover:bg-white"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const { identity, core_skills, technical_stack, work_history, education } = profile;

  return (
    <div className="flex flex-col gap-6 p-6 max-w-7xl mx-auto">
      {/* Top Banner / Identity Card */}
      <div className="p-6 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-[22px] font-bold text-[#e3e1ec]">{identity.full_name}</h1>
            <span className="text-xs px-2 py-0.5 rounded bg-[#4edea3]/10 border border-[#4edea3]/30 text-[#4edea3] font-mono">
              Available Immediately
            </span>
          </div>
          <p className="text-[14px] text-[#4cd7f6] mt-0.5 font-medium">{identity.professional_title}</p>
          <div className="flex flex-wrap items-center gap-4 mt-3 text-xs text-[#bcc9cd]">
            <span>📍 {identity.current_location} ({identity.nationality})</span>
            <span>📧 {identity.email}</span>
            <span>📱 {identity.phone}</span>
            {identity.website && (
              <a href={identity.website} target="_blank" rel="noopener noreferrer" className="text-[#4cd7f6] hover:underline flex items-center gap-1">
                <Globe className="w-3 h-3" />
                <span>Portfolio Website</span>
              </a>
            )}
            {identity.github && (
              <a href={identity.github} target="_blank" rel="noopener noreferrer" className="text-[#bcc9cd] hover:text-white flex items-center gap-1">
                <Github className="w-3 h-3" />
                <span>GitHub</span>
              </a>
            )}
          </div>
        </div>

        {/* Top Header Actions */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Default Europass Generator Button */}
          <button
            onClick={handleDownloadEuropass}
            disabled={downloadingPdf}
            className="px-4 py-2.5 rounded-lg bg-[#4edea3] text-[#003824] font-semibold text-xs hover:bg-white transition-all flex items-center gap-2 emerald-glow disabled:opacity-50"
            title="Generate and download official European Union standard A4 CV PDF"
          >
            <Download className="w-4 h-4" />
            <span>{downloadingPdf ? "Compiling..." : "Download Europass CV (A4 PDF)"}</span>
          </button>

          {/* Intake Studio Toggle */}
          <button
            onClick={() => setShowIntakeStudio(!showIntakeStudio)}
            className="px-4 py-2.5 rounded-lg bg-[#292931] border border-[#3d494c]/50 text-xs font-semibold text-[#e3e1ec] hover:border-[#4cd7f6] transition-colors flex items-center gap-2"
          >
            <Layers className="w-4 h-4 text-[#4cd7f6]" />
            <span>Multi-Source Intake Studio</span>
            {showIntakeStudio ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Global Status Message */}
      {statusMsg && (
        <div
          className={`p-3.5 rounded-lg flex items-center gap-2 text-xs font-mono ${
            statusMsg.type === "success"
              ? "bg-[#4edea3]/10 border border-[#4edea3]/30 text-[#4edea3]"
              : "bg-[#93000a]/20 border border-[#93000a]/40 text-[#ffb4ab]"
          }`}
        >
          {statusMsg.type === "success" ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          <span>{statusMsg.text}</span>
        </div>
      )}

      {/* MULTI-SOURCE INTAKE STUDIO (EXPANDABLE) */}
      {showIntakeStudio && (
        <div className="p-6 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-5">
          <div className="flex items-center justify-between pb-3 border-b border-[#3d494c]/20">
            <div>
              <h2 className="text-[15px] font-semibold text-[#e3e1ec] flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-[#4cd7f6]" />
                Multi-Source Ingestion &amp; Intelligence Fusion
              </h2>
              <p className="text-xs text-[#bcc9cd] mt-0.5">
                Upload multiple CVs, LLM conversations, and connect your LinkedIn, GitHub, and Personal Website.
              </p>
            </div>

            {/* Synthesize Button */}
            <button
              onClick={handleSynthesize}
              disabled={synthesizing}
              className="px-5 py-2.5 rounded-lg bg-[#4cd7f6] text-[#003640] font-semibold text-xs hover:bg-white transition-all cyan-glow flex items-center gap-2 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${synthesizing ? "animate-spin" : ""}`} />
              <span>{synthesizing ? "Analyzing & Fusing..." : "⚡ Analyze & Synthesize Master Persona"}</span>
            </button>
          </div>

          {/* 5-Source Intake Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* SOURCE 1: Multiple CVs */}
            <div className="p-4 rounded-xl bg-[#14151e] border border-[#3d494c]/40 flex flex-col justify-between gap-3">
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[#e3e1ec] flex items-center gap-1.5">
                    <FileText className="w-4 h-4 text-[#4cd7f6]" />
                    Multiple CVs Upload
                  </span>
                  <span className="text-[10px] font-mono text-[#4edea3]">PDF, DOCX, TXT</span>
                </div>
                <p className="text-[11px] text-[#bcc9cd]">
                  Upload one or multiple resumes to extract career milestones and metrics.
                </p>
              </div>

              {uploadedCVs.length > 0 && (
                <div className="max-h-24 overflow-y-auto flex flex-col gap-1 bg-[#1a1b22] p-2 rounded-lg border border-[#3d494c]/30 text-[11px]">
                  {uploadedCVs.map((cv, i) => (
                    <div key={i} className="flex items-center justify-between text-[#bcc9cd]">
                      <span className="truncate">{cv.source_file}</span>
                      <span className="text-[#4edea3] font-mono">Parsed</span>
                    </div>
                  ))}
                </div>
              )}

              <label className="w-full py-2 px-3 rounded-lg bg-[#1a1b22] hover:bg-[#292931] border border-[#3d494c]/50 text-xs font-semibold text-[#e3e1ec] cursor-pointer transition-colors flex items-center justify-center gap-2">
                <UploadCloud className="w-4 h-4 text-[#4cd7f6]" />
                <span>{uploadingCVs ? "Parsing CVs..." : "+ Select Multiple CVs"}</span>
                <input
                  type="file"
                  multiple
                  accept=".pdf,.docx,.txt"
                  onChange={handleMultipleCVUpload}
                  className="hidden"
                />
              </label>
            </div>

            {/* SOURCE 2: LLM Chat History */}
            <div className="p-4 rounded-xl bg-[#14151e] border border-[#3d494c]/40 flex flex-col justify-between gap-3">
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[#e3e1ec] flex items-center gap-1.5">
                    <MessageSquare className="w-4 h-4 text-[#d0bcff]" />
                    LLM Chat History
                  </span>
                  <span className="text-[10px] font-mono text-[#d0bcff]">JSON, MD, TXT</span>
                </div>
                <p className="text-[11px] text-[#bcc9cd]">
                  Upload ChatGPT or Claude conversation logs discussing your system design &amp; code.
                </p>
              </div>

              {chatInsights.length > 0 && (
                <div className="max-h-24 overflow-y-auto flex flex-col gap-1 bg-[#1a1b22] p-2 rounded-lg border border-[#3d494c]/30 text-[11px]">
                  {chatInsights.map((ci, i) => (
                    <div key={i} className="flex items-center justify-between text-[#bcc9cd]">
                      <span className="truncate">{ci.topic}</span>
                      <span className="text-[#d0bcff] font-mono">Extracted</span>
                    </div>
                  ))}
                </div>
              )}

              <label className="w-full py-2 px-3 rounded-lg bg-[#1a1b22] hover:bg-[#292931] border border-[#3d494c]/50 text-xs font-semibold text-[#e3e1ec] cursor-pointer transition-colors flex items-center justify-center gap-2">
                <UploadCloud className="w-4 h-4 text-[#d0bcff]" />
                <span>{uploadingChats ? "Extracting Insights..." : "+ Upload Chat History"}</span>
                <input
                  type="file"
                  multiple
                  accept=".json,.md,.txt"
                  onChange={handleChatUpload}
                  className="hidden"
                />
              </label>
            </div>

            {/* SOURCE 3: GitHub Profile Parser */}
            <div className="p-4 rounded-xl bg-[#14151e] border border-[#3d494c]/40 flex flex-col justify-between gap-3">
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[#e3e1ec] flex items-center gap-1.5">
                    <Github className="w-4 h-4 text-white" />
                    GitHub Profile Parser
                  </span>
                  <span className="text-[10px] font-mono text-[#4cd7f6]">Public API</span>
                </div>
                <p className="text-[11px] text-[#bcc9cd]">
                  Fetches repositories, descriptions, star counts, and language breakdown.
                </p>
              </div>

              <div className="flex flex-col gap-2">
                <input
                  type="text"
                  value={githubInput}
                  onChange={(e) => setGithubInput(e.target.value)}
                  placeholder="https://github.com/username"
                  className="w-full px-3 py-1.5 bg-[#1a1b22] text-[#e3e1ec] text-xs rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none font-mono"
                />
                <button
                  onClick={handleParseGithub}
                  disabled={fetchingGithub}
                  className="w-full py-1.5 px-3 rounded-lg bg-[#1a1b22] hover:bg-[#292931] border border-[#3d494c]/50 text-xs font-semibold text-[#4cd7f6] transition-colors flex items-center justify-center gap-1.5"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${fetchingGithub ? "animate-spin" : ""}`} />
                  <span>{fetchingGithub ? "Querying GitHub..." : "Sync Repositories"}</span>
                </button>
              </div>
            </div>

            {/* SOURCE 4: LinkedIn Profile Parser */}
            <div className="p-4 rounded-xl bg-[#14151e] border border-[#3d494c]/40 flex flex-col justify-between gap-3">
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[#e3e1ec] flex items-center gap-1.5">
                    <Linkedin className="w-4 h-4 text-[#0a66c2]" />
                    LinkedIn Profile Parser
                  </span>
                  <span className="text-[10px] font-mono text-[#0a66c2]">URL &amp; Bio</span>
                </div>
                <p className="text-[11px] text-[#bcc9cd]">
                  Enter LinkedIn profile URL or paste about summary to extract headline &amp; skills.
                </p>
              </div>

              <div className="flex flex-col gap-2">
                <input
                  type="text"
                  value={linkedinInput}
                  onChange={(e) => setLinkedinInput(e.target.value)}
                  placeholder="https://linkedin.com/in/username"
                  className="w-full px-3 py-1.5 bg-[#1a1b22] text-[#e3e1ec] text-xs rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none font-mono"
                />
                <button
                  onClick={handleParseLinkedin}
                  disabled={fetchingLinkedin}
                  className="w-full py-1.5 px-3 rounded-lg bg-[#1a1b22] hover:bg-[#292931] border border-[#3d494c]/50 text-xs font-semibold text-[#4cd7f6] transition-colors flex items-center justify-center gap-1.5"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${fetchingLinkedin ? "animate-spin" : ""}`} />
                  <span>{fetchingLinkedin ? "Parsing..." : "Parse LinkedIn"}</span>
                </button>
              </div>
            </div>

            {/* SOURCE 5: Personal Portfolio Website */}
            <div className="p-4 rounded-xl bg-[#14151e] border border-[#3d494c]/40 flex flex-col justify-between gap-3 md:col-span-2 lg:col-span-1">
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[#e3e1ec] flex items-center gap-1.5">
                    <Globe className="w-4 h-4 text-[#4edea3]" />
                    Personal Website / Portfolio
                  </span>
                  <span className="text-[10px] font-mono text-[#4edea3]">Live Scrape</span>
                </div>
                <p className="text-[11px] text-[#bcc9cd]">
                  Enter your personal website to scrape project descriptions and portfolio tags.
                </p>
              </div>

              <div className="flex flex-col gap-2">
                <input
                  type="text"
                  value={websiteInput}
                  onChange={(e) => setWebsiteInput(e.target.value)}
                  placeholder="https://yourportfolio.dev"
                  className="w-full px-3 py-1.5 bg-[#1a1b22] text-[#e3e1ec] text-xs rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none font-mono"
                />
                <button
                  onClick={handleScrapeWebsite}
                  disabled={fetchingWebsite}
                  className="w-full py-1.5 px-3 rounded-lg bg-[#1a1b22] hover:bg-[#292931] border border-[#3d494c]/50 text-xs font-semibold text-[#4edea3] transition-colors flex items-center justify-center gap-1.5"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${fetchingWebsite ? "animate-spin" : ""}`} />
                  <span>{fetchingWebsite ? "Scraping..." : "Scrape Website"}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* CANONICAL MASTER PERSONA DISPLAY */}

      {/* Executive Summary */}
      <div className="p-5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border">
        <h3 className="text-xs font-mono uppercase text-[#869397] mb-2">Executive Summary</h3>
        <p className="text-[13px] text-[#e3e1ec] leading-relaxed bg-[#1a1b22] p-4 rounded-lg border border-[#3d494c]/30">
          {profile.summary}
        </p>
      </div>

      {/* Skills Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div className="p-5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border">
          <h3 className="text-xs font-mono uppercase text-[#869397] mb-3 flex items-center gap-1.5">
            <Code className="w-4 h-4 text-[#4cd7f6]" /> Core Engineering Competencies
          </h3>
          <div className="flex flex-wrap gap-2">
            {core_skills.map((s, i) => (
              <span key={i} className="px-2.5 py-1 rounded bg-[#1e1f26] border border-[#3d494c]/40 text-xs text-[#e3e1ec]">
                {s}
              </span>
            ))}
          </div>
        </div>

        <div className="p-5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border">
          <h3 className="text-xs font-mono uppercase text-[#869397] mb-3 flex items-center gap-1.5">
            <Code className="w-4 h-4 text-[#4edea3]" /> Verified Technical Stack
          </h3>
          <div className="flex flex-wrap gap-2">
            {technical_stack.map((t, i) => (
              <span key={i} className="px-2.5 py-1 rounded bg-[#1e1f26] border border-[#3d494c]/40 text-xs text-[#4cd7f6] font-mono">
                {t}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Canonical Work History */}
      <div className="p-5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-4">
        <h3 className="text-xs font-mono uppercase text-[#869397] flex items-center gap-1.5">
          <Briefcase className="w-4 h-4 text-[#4cd7f6]" /> Canonical Work Experience
        </h3>
        <div className="flex flex-col gap-3">
          {work_history.map((w, i) => (
            <div key={i} className="p-4 rounded-lg bg-[#1a1b22] border border-[#3d494c]/30 text-xs">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="text-[14px] font-semibold text-[#e3e1ec]">{w.title}</h4>
                  <div className="text-[#4cd7f6] mt-0.5 font-medium">{w.company} &nbsp;•&nbsp; {w.location || w.branch}</div>
                </div>
                <span className="text-[11px] font-mono text-[#869397]">{w.duration}</span>
              </div>
              <ul className="mt-2.5 space-y-1 list-disc list-inside text-[#bcc9cd] leading-relaxed">
                {w.bullets.map((b, bi) => (
                  <li key={bi}>{b}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Verified Projects Portfolio (including synced GitHub repos) */}
      {profile.projects && profile.projects.length > 0 && (
        <div className="p-5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-mono uppercase text-[#869397] flex items-center gap-1.5">
              <Github className="w-4 h-4 text-[#4cd7f6]" /> Highlighted Engineering Projects &amp; Repositories
            </h3>
            <span className="text-[11px] font-mono text-[#4edea3]">{profile.projects.length} Projects Loaded</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {profile.projects.map((proj: any, i: number) => (
              <div key={i} className="p-4 rounded-lg bg-[#1a1b22] border border-[#3d494c]/30 text-xs flex flex-col justify-between gap-2">
                <div>
                  <h4 className="text-[13px] font-semibold text-[#e3e1ec]">{proj.title}</h4>
                  {proj.technologies && (
                    <div className="text-[#4cd7f6] font-mono text-[11px] mt-0.5">{proj.technologies}</div>
                  )}
                  {proj.bullets && proj.bullets.length > 0 && (
                    <p className="mt-2 text-[#bcc9cd] leading-relaxed">{proj.bullets[0]}</p>
                  )}
                </div>
                {proj.url && (
                  <a href={proj.url} target="_blank" rel="noopener noreferrer" className="text-[11px] font-mono text-[#4cd7f6] hover:underline flex items-center gap-1 self-start pt-1">
                    <span>View Repository</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Verified Education */}
      <div className="p-5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-4">
        <h3 className="text-xs font-mono uppercase text-[#869397] flex items-center gap-1.5">
          <GraduationCap className="w-4 h-4 text-[#d0bcff]" /> Verified Education
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {education.map((edu, i) => (
            <div key={i} className="p-4 rounded-lg bg-[#1a1b22] border border-[#3d494c]/30 text-xs">
              <h4 className="text-[14px] font-semibold text-[#e3e1ec]">{edu.degree}</h4>
              <div className="text-[#d0bcff] mt-0.5">{edu.institution} — {edu.location}</div>
              <div className="text-[#869397] font-mono mt-1 text-[11px]">{edu.duration}</div>
              <p className="mt-2 text-[#bcc9cd]">{edu.details}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
