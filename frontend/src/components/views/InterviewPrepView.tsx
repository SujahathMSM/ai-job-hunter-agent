"use client";

import React, { useState, useEffect } from "react";
import {
  MessageSquareCode,
  Sparkles,
  HelpCircle,
  CheckCircle2,
  AlertCircle,
  Copy,
  Check,
  Send,
  RefreshCw,
  Building2,
  Briefcase,
  MapPin,
  ChevronRight,
  Award,
  Zap,
  BookOpen,
  ArrowRight,
  ShieldCheck
} from "lucide-react";
import { generateInterviewPrep, evaluateInterviewAnswer, fetchProfile } from "../../lib/api";
import { CandidateProfile } from "../../types";

interface InterviewPrepViewProps {
  initialJob?: {
    job_title: string;
    company: string;
    location: string;
    description: string;
  };
  onSelectForTailor?: (jobTitle: string, company: string, location: string, desc: string) => void;
}

export default function InterviewPrepView({ initialJob, onSelectForTailor }: InterviewPrepViewProps) {
  const [jobTitle, setJobTitle] = useState(initialJob?.job_title || "Python Backend Systems Engineer");
  const [company, setCompany] = useState(initialJob?.company || "Quantum Infotech Solutions");
  const [location, setLocation] = useState(initialJob?.location || "Singapore");
  const [description, setDescription] = useState(
    initialJob?.description ||
      "Develop secure, scalable microservices in Python/FastAPI. Optimize PostgreSQL and time-series data pipelines. Maintain high availability and automated CI/CD testing."
  );

  const [loading, setLoading] = useState(false);
  const [activePrepTab, setActivePrepTab] = useState<"questions" | "talking_points" | "reverse_questions" | "skill_gap">("questions");
  const [pack, setPack] = useState<any>(null);
  const [candidateProfile, setCandidateProfile] = useState<CandidateProfile | null>(null);

  // Practice Answer State
  const [selectedQuestionId, setSelectedQuestionId] = useState<number>(1);
  const [practiceAnswers, setPracticeAnswers] = useState<Record<number, string>>({});
  const [evaluations, setEvaluations] = useState<Record<number, any>>({});
  const [evaluating, setEvaluating] = useState<Record<number, boolean>>({});
  const [copiedIndex, setCopiedIndex] = useState<string | null>(null);

  // Sync if initialJob passed
  useEffect(() => {
    if (initialJob?.job_title) setJobTitle(initialJob.job_title);
    if (initialJob?.company) setCompany(initialJob.company);
    if (initialJob?.location) setLocation(initialJob.location);
    if (initialJob?.description) setDescription(initialJob.description);
  }, [initialJob]);

  // Load candidate profile
  useEffect(() => {
    fetchProfile().then((p) => setCandidateProfile(p)).catch(() => {});
  }, []);

  const handleGeneratePack = async () => {
    setLoading(true);
    try {
      const data = await generateInterviewPrep(jobTitle, company, location, description);
      setPack(data);
      if (data?.role_questions?.length > 0) {
        setSelectedQuestionId(data.role_questions[0].id);
      }
    } catch (err) {
      console.error("Failed to generate prep pack:", err);
    } finally {
      setLoading(false);
    }
  };

  // Auto-generate on first mount if not yet loaded
  useEffect(() => {
    if (!pack && !loading) {
      handleGeneratePack();
    }
  }, []);

  const handleEvaluate = async (qId: number, questionText: string, qType: string) => {
    const answer = practiceAnswers[qId] || "";
    if (!answer.trim()) return;

    setEvaluating((prev) => ({ ...prev, [qId]: true }));
    try {
      const evalRes = await evaluateInterviewAnswer(questionText, qType, answer, jobTitle, company);
      setEvaluations((prev) => ({ ...prev, [qId]: evalRes }));
    } catch (err) {
      console.error("Evaluation error:", err);
    } finally {
      setEvaluating((prev) => ({ ...prev, [qId]: false }));
    }
  };

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(id);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const activeQuestion = pack?.role_questions?.find((q: any) => q.id === selectedQuestionId) || pack?.role_questions?.[0];

  return (
    <div className="flex flex-col gap-5 p-6 max-w-7xl mx-auto">
      {/* Top Banner Header */}
      <div className="p-4 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-[20px] font-semibold text-[#e3e1ec] tracking-tight flex items-center gap-2">
            <MessageSquareCode className="w-5 h-5 text-[#4cd7f6]" />
            AI Mock Interview Simulator &amp; Talking Points
          </h1>
          <p className="text-[13px] text-[#bcc9cd] mt-0.5">
            Role-specific STAR behavioral drills, system architecture challenges, and hiring manager reverse questions.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#4edea3]/10 border border-[#4edea3]/30 text-[#4edea3] text-[11px] font-mono">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>STAR Framework Certified</span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#4cd7f6]/10 border border-[#4cd7f6]/30 text-[#4cd7f6] text-[11px] font-mono">
            <Award className="w-3.5 h-3.5" />
            <span>Moratuwa Grounded Answers</span>
          </div>
        </div>
      </div>

      {/* Main Studio Grid: Parameters Deck & Simulation Console */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* LEFT COLUMN: Target Parameters (4 cols) */}
        <div className="lg:col-span-4 flex flex-col gap-4">
          <div className="p-4 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-3">
            <div className="flex items-center justify-between pb-2 border-b border-[#3d494c]/20">
              <span className="text-[11px] font-mono uppercase text-[#bcc9cd] flex items-center gap-1.5">
                <Briefcase className="w-3.5 h-3.5 text-[#4cd7f6]" />
                Interview Target Spec
              </span>
              <span className="text-[10px] font-mono text-[#869397]">Auto-linked</span>
            </div>

            <div className="flex flex-col gap-2.5">
              <div>
                <label className="text-[11px] font-mono uppercase text-[#869397] mb-1 block">Target Role</label>
                <div className="relative">
                  <Briefcase className="w-3.5 h-3.5 absolute left-3 top-3 text-[#869397]" />
                  <input
                    type="text"
                    value={jobTitle}
                    onChange={(e) => setJobTitle(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-[#14151f] border border-[#3d494c]/40 rounded-lg text-xs text-[#e3e1ec] focus:outline-none focus:border-[#4cd7f6]"
                    placeholder="e.g. Senior Backend Engineer"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-mono uppercase text-[#869397] mb-1 block">Company</label>
                <div className="relative">
                  <Building2 className="w-3.5 h-3.5 absolute left-3 top-3 text-[#869397]" />
                  <input
                    type="text"
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-[#14151f] border border-[#3d494c]/40 rounded-lg text-xs text-[#e3e1ec] focus:outline-none focus:border-[#4cd7f6]"
                    placeholder="e.g. Quantum Infotech"
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
                    className="w-full pl-9 pr-3 py-2 bg-[#14151f] border border-[#3d494c]/40 rounded-lg text-xs text-[#e3e1ec] focus:outline-none focus:border-[#4cd7f6]"
                    placeholder="e.g. Dubai / Remote"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-mono uppercase text-[#869397] mb-1 block">Job Description &amp; Scope</label>
                <textarea
                  rows={4}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full p-2.5 bg-[#14151f] border border-[#3d494c]/40 rounded-lg text-xs text-[#e3e1ec] focus:outline-none focus:border-[#4cd7f6] scrollbar-thin"
                  placeholder="Paste job requirements..."
                />
              </div>

              <button
                onClick={handleGeneratePack}
                disabled={loading}
                className="w-full py-2.5 px-3 rounded-lg bg-[#4cd7f6] text-[#003640] font-semibold text-xs hover:bg-white transition-all flex items-center justify-center gap-2 cyan-glow disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Analyzing JD &amp; Simulating...</span>
                  </>
                ) : (
                  <>
                    <Zap className="w-3.5 h-3.5" />
                    <span>Generate Prep Pack</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Quick Navigator Pill */}
          {pack?.role_questions && (
            <div className="p-3.5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-2">
              <span className="text-[11px] font-mono uppercase text-[#bcc9cd] flex items-center gap-1.5">
                <BookOpen className="w-3.5 h-3.5 text-[#4edea3]" />
                Questions Drill Index
              </span>
              <div className="flex flex-col gap-1.5">
                {pack.role_questions.map((q: any) => {
                  const isSelected = selectedQuestionId === q.id;
                  const isAnswered = !!practiceAnswers[q.id];
                  const hasEval = !!evaluations[q.id];
                  return (
                    <button
                      key={q.id}
                      onClick={() => {
                        setSelectedQuestionId(q.id);
                        setActivePrepTab("questions");
                      }}
                      className={`p-2 rounded-lg text-left text-xs transition-all flex items-center justify-between border ${
                        isSelected
                          ? "bg-[#292931] border-[#4cd7f6] text-[#4cd7f6]"
                          : "bg-[#14151f] border-[#3d494c]/30 text-[#bcc9cd] hover:text-[#e3e1ec]"
                      }`}
                    >
                      <div className="flex items-center gap-2 truncate">
                        <span className="w-5 h-5 rounded-full bg-[#1e1f26] border border-[#3d494c]/40 text-[10px] font-mono flex items-center justify-center">
                          {q.id}
                        </span>
                        <span className="truncate">{q.type}</span>
                      </div>
                      {hasEval ? (
                        <span className="text-[10px] font-mono text-[#4edea3] font-semibold">
                          {evaluations[q.id].score}/100
                        </span>
                      ) : isAnswered ? (
                        <span className="text-[10px] font-mono text-[#e3e1ec]">Drafted</span>
                      ) : (
                        <ChevronRight className="w-3.5 h-3.5 text-[#869397]" />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* RIGHT COLUMN: Interactive Prep Deck (8 cols) */}
        <div className="lg:col-span-8 flex flex-col gap-4">
          {/* Deck Action Tabs */}
          <div className="p-3.5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-1 p-1 bg-[#1a1b22] rounded-lg border border-[#3d494c]/40 text-xs">
              <button
                onClick={() => setActivePrepTab("questions")}
                className={`px-3 py-1.5 rounded-md font-medium transition-all flex items-center gap-1.5 ${
                  activePrepTab === "questions" ? "bg-[#292931] text-[#4cd7f6] shadow-sm" : "text-[#bcc9cd] hover:text-[#e3e1ec]"
                }`}
              >
                <MessageSquareCode className="w-3.5 h-3.5" />
                <span>STAR Simulator ({pack?.role_questions?.length || 5})</span>
              </button>

              <button
                onClick={() => setActivePrepTab("talking_points")}
                className={`px-3 py-1.5 rounded-md font-medium transition-all flex items-center gap-1.5 ${
                  activePrepTab === "talking_points" ? "bg-[#292931] text-[#4cd7f6] shadow-sm" : "text-[#bcc9cd] hover:text-[#e3e1ec]"
                }`}
              >
                <Award className="w-3.5 h-3.5" />
                <span>Talking Points (4)</span>
              </button>

              <button
                onClick={() => setActivePrepTab("reverse_questions")}
                className={`px-3 py-1.5 rounded-md font-medium transition-all flex items-center gap-1.5 ${
                  activePrepTab === "reverse_questions" ? "bg-[#292931] text-[#4cd7f6] shadow-sm" : "text-[#bcc9cd] hover:text-[#e3e1ec]"
                }`}
              >
                <HelpCircle className="w-3.5 h-3.5" />
                <span>Killer Reverse Questions</span>
              </button>
            </div>

            {onSelectForTailor && (
              <button
                onClick={() => onSelectForTailor(jobTitle, company, location, description)}
                className="px-3 py-1.5 rounded-lg bg-[#1a1b22] border border-[#3d494c]/40 text-[#4cd7f6] hover:bg-[#292931] text-xs flex items-center gap-1.5 transition-all"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Tailor CV for this Role</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* TAB 1: Questions & STAR Simulator */}
          {activePrepTab === "questions" && activeQuestion && (
            <div className="p-6 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-5 shadow-2xl">
              {/* Question Header */}
              <div className="flex flex-col gap-2 pb-4 border-b border-[#3d494c]/30">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#4cd7f6]/10 text-[#4cd7f6] border border-[#4cd7f6]/30">
                      Question {activeQuestion.id} of {pack?.role_questions?.length || 5}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#4edea3]/10 text-[#4edea3] border border-[#4edea3]/30">
                      {activeQuestion.type}
                    </span>
                  </div>

                  <button
                    onClick={() => handleCopy(activeQuestion.question, `q-${activeQuestion.id}`)}
                    className="text-[#bcc9cd] hover:text-[#e3e1ec] text-[11px] font-mono flex items-center gap-1"
                  >
                    {copiedIndex === `q-${activeQuestion.id}` ? <Check className="w-3 h-3 text-[#4edea3]" /> : <Copy className="w-3 h-3" />}
                    <span>{copiedIndex === `q-${activeQuestion.id}` ? "Copied" : "Copy"}</span>
                  </button>
                </div>

                <h2 className="text-[17px] font-semibold text-[#e3e1ec] leading-snug">
                  "{activeQuestion.question}"
                </h2>

                {activeQuestion.hiring_intent && (
                  <div className="p-2.5 rounded-lg bg-[#14151f] border border-[#3d494c]/30 text-xs text-[#bcc9cd] flex items-start gap-2">
                    <HelpCircle className="w-4 h-4 text-[#4cd7f6] shrink-0 mt-0.5" />
                    <div>
                      <strong className="text-[#e3e1ec]">What they are looking for: </strong>
                      {activeQuestion.hiring_intent}
                    </div>
                  </div>
                )}
              </div>

              {/* Recommended STAR Blueprint */}
              {activeQuestion.recommended_star_structure && (
                <div className="flex flex-col gap-1.5">
                  <div className="text-[11px] font-mono uppercase tracking-wider text-[#4edea3] font-semibold flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>Recommended STAR Architecture (Grounded in Your Background)</span>
                  </div>
                  <div className="p-3 rounded-lg bg-[#14151f] border border-[#4edea3]/20 text-xs text-[#bcc9cd] leading-relaxed">
                    {activeQuestion.recommended_star_structure}
                  </div>
                </div>
              )}

              {/* Practice Answer Area */}
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <label className="text-[11px] font-mono uppercase tracking-wider text-[#4cd7f6] font-semibold">
                    Your Practice Response (STAR Draft)
                  </label>
                  <span className="text-[10px] font-mono text-[#869397]">
                    {(practiceAnswers[activeQuestion.id] || "").split(/\s+/).filter(Boolean).length} words
                  </span>
                </div>

                <textarea
                  rows={4}
                  value={practiceAnswers[activeQuestion.id] || ""}
                  onChange={(e) =>
                    setPracticeAnswers((prev) => ({
                      ...prev,
                      [activeQuestion.id]: e.target.value,
                    }))
                  }
                  className="w-full p-3 bg-[#14151f] border border-[#3d494c]/40 rounded-lg text-xs text-[#e3e1ec] focus:outline-none focus:border-[#4cd7f6] font-sans leading-relaxed"
                  placeholder="Type your response using Situation, Task, Action, Result... (e.g. 'At Blue Brand IP Institute, our distributed telemetry ingestion was facing 80% polling failures...')"
                />

                <div className="flex items-center justify-between">
                  <button
                    onClick={() => {
                      // Insert starter template
                      const template = `Situation: At Blue Brand IP Institute, our backend platform was experiencing...\nTask: I was tasked with refactoring the telemetry data pipeline...\nAction: I implemented asynchronous FastAPI endpoints with TimescaleDB indexing and retry queues...\nResult: Slashed failure rate from 80% to 0% and reduced startup latency by 90%.`;
                      setPracticeAnswers((prev) => ({
                        ...prev,
                        [activeQuestion.id]: template,
                      }));
                    }}
                    className="text-[11px] font-mono text-[#bcc9cd] hover:text-[#4cd7f6] transition-colors"
                  >
                    Insert STAR Template
                  </button>

                  <button
                    onClick={() => handleEvaluate(activeQuestion.id, activeQuestion.question, activeQuestion.type)}
                    disabled={evaluating[activeQuestion.id] || !practiceAnswers[activeQuestion.id]?.trim()}
                    className="px-4 py-1.5 rounded-lg bg-[#4edea3] text-[#003824] font-semibold text-xs hover:bg-white transition-all flex items-center gap-1.5 emerald-glow disabled:opacity-50"
                  >
                    {evaluating[activeQuestion.id] ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        <span>Evaluating...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>Evaluate My Answer</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Evaluation Results Card */}
              {evaluations[activeQuestion.id] && (
                <div className="p-4 rounded-xl bg-[#14151f] border border-[#3d494c]/40 flex flex-col gap-3">
                  <div className="flex items-center justify-between pb-2 border-b border-[#3d494c]/30">
                    <div className="flex items-center gap-2">
                      <Award className="w-4 h-4 text-[#4edea3]" />
                      <span className="text-[13px] font-semibold text-[#e3e1ec]">
                        Senior Technical Reviewer Score:
                      </span>
                    </div>
                    <span className="text-sm font-mono font-bold text-[#4edea3] px-2.5 py-0.5 rounded bg-[#4edea3]/10 border border-[#4edea3]/30">
                      {evaluations[activeQuestion.id].score} / 100
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    <div className="p-2.5 rounded-lg bg-[#1e1f26] border border-[#4edea3]/30">
                      <div className="text-[11px] font-mono uppercase text-[#4edea3] font-semibold mb-1 flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" />
                        What Worked Well
                      </div>
                      <ul className="list-disc list-inside space-y-1 text-[#bcc9cd]">
                        {evaluations[activeQuestion.id].strengths?.map((s: string, idx: number) => (
                          <li key={idx}>{s}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="p-2.5 rounded-lg bg-[#1e1f26] border border-[#4cd7f6]/30">
                      <div className="text-[11px] font-mono uppercase text-[#4cd7f6] font-semibold mb-1 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" />
                        Key Opportunities to Tighten
                      </div>
                      <ul className="list-disc list-inside space-y-1 text-[#bcc9cd]">
                        {evaluations[activeQuestion.id].improvements?.map((imp: string, idx: number) => (
                          <li key={idx}>{imp}</li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {evaluations[activeQuestion.id].model_answer && (
                    <div className="p-3 rounded-lg bg-[#181924] border border-[#3d494c]/30 flex flex-col gap-1.5 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-mono uppercase text-[#e3e1ec] font-semibold flex items-center gap-1">
                          <Sparkles className="w-3 h-3 text-[#4cd7f6]" />
                          Exemplary Model Response (STAR Masterclass)
                        </span>
                        <button
                          onClick={() => handleCopy(evaluations[activeQuestion.id].model_answer, `model-${activeQuestion.id}`)}
                          className="text-[#bcc9cd] hover:text-[#e3e1ec] text-[10px] font-mono flex items-center gap-1"
                        >
                          {copiedIndex === `model-${activeQuestion.id}` ? <Check className="w-3 h-3 text-[#4edea3]" /> : <Copy className="w-3 h-3" />}
                          <span>{copiedIndex === `model-${activeQuestion.id}` ? "Copied" : "Copy"}</span>
                        </button>
                      </div>
                      <p className="text-[#bcc9cd] leading-relaxed italic">
                        "{evaluations[activeQuestion.id].model_answer}"
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: Strategic Candidate Talking Points */}
          {activePrepTab === "talking_points" && (
            <div className="p-6 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-4 shadow-2xl">
              <div className="flex items-center justify-between pb-3 border-b border-[#3d494c]/30">
                <div className="flex items-center gap-2">
                  <Award className="w-5 h-5 text-[#4cd7f6]" />
                  <h3 className="text-[16px] font-semibold text-[#e3e1ec]">
                    Core Candidate Talking Points (Elevator Pitches)
                  </h3>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#4edea3]/10 border border-[#4edea3]/30 text-[#4edea3]">
                  Anchored to Moratuwa Engineering
                </span>
              </div>

              <p className="text-xs text-[#bcc9cd]">
                Proactively inject these 4 strategic pillars into your conversation during introductions and technical discussions:
              </p>

              <div className="space-y-3">
                {pack?.candidate_talking_points?.map((tp: string, idx: number) => (
                  <div key={idx} className="p-3.5 rounded-lg bg-[#14151f] border border-[#3d494c]/30 flex items-start justify-between gap-3 text-xs">
                    <div className="flex items-start gap-2.5">
                      <span className="w-5 h-5 rounded-full bg-[#4cd7f6]/10 text-[#4cd7f6] border border-[#4cd7f6]/30 text-[10px] font-mono flex items-center justify-center shrink-0 mt-0.5">
                        {idx + 1}
                      </span>
                      <p className="text-[#e3e1ec] leading-relaxed font-sans">{tp}</p>
                    </div>
                    <button
                      onClick={() => handleCopy(tp, `tp-${idx}`)}
                      className="p-1.5 rounded bg-[#1e1f26] text-[#bcc9cd] hover:text-[#e3e1ec] shrink-0"
                    >
                      {copiedIndex === `tp-${idx}` ? <Check className="w-3.5 h-3.5 text-[#4edea3]" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 3: Killer Reverse Questions */}
          {activePrepTab === "reverse_questions" && (
            <div className="p-6 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-4 shadow-2xl">
              <div className="flex items-center justify-between pb-3 border-b border-[#3d494c]/30">
                <div className="flex items-center gap-2">
                  <HelpCircle className="w-5 h-5 text-[#4edea3]" />
                  <h3 className="text-[16px] font-semibold text-[#e3e1ec]">
                    Killer Reverse Questions to Ask the Hiring Team
                  </h3>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#4cd7f6]/10 border border-[#4cd7f6]/30 text-[#4cd7f6]">
                  High Hiring Manager Impact
                </span>
              </div>

              <p className="text-xs text-[#bcc9cd]">
                When the interviewer asks <em>"Do you have any questions for us?"</em>, asking these demonstrates principal-level architectural thinking and business seriousness:
              </p>

              <div className="space-y-3">
                {pack?.killer_questions_to_ask?.map((q: string, idx: number) => (
                  <div key={idx} className="p-3.5 rounded-lg bg-[#14151f] border border-[#3d494c]/30 flex items-start justify-between gap-3 text-xs">
                    <div className="flex items-start gap-2.5">
                      <span className="w-5 h-5 rounded-full bg-[#4edea3]/10 text-[#4edea3] border border-[#4edea3]/30 text-[10px] font-mono flex items-center justify-center shrink-0 mt-0.5">
                        {idx + 1}
                      </span>
                      <p className="text-[#e3e1ec] font-medium leading-relaxed font-sans">"{q}"</p>
                    </div>
                    <button
                      onClick={() => handleCopy(q, `kq-${idx}`)}
                      className="p-1.5 rounded bg-[#1e1f26] text-[#bcc9cd] hover:text-[#e3e1ec] shrink-0"
                    >
                      {copiedIndex === `kq-${idx}` ? <Check className="w-3.5 h-3.5 text-[#4edea3]" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
