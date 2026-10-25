"use client";

import React, { useState } from "react";
import { Send, Shield, CheckCircle2, AlertCircle } from "lucide-react";
import { sendEmail, draftEmail } from "../../lib/api";

interface ColdEmailViewProps {
  initialData?: {
    jobTitle?: string;
    company?: string;
    hrEmail?: string;
    context?: string;
  };
  onSentSuccess?: () => void;
}

export default function ColdEmailView({ initialData, onSentSuccess }: ColdEmailViewProps) {
  const [toEmail, setToEmail] = useState(initialData?.hrEmail || "careers@company.com");
  const [company, setCompany] = useState(initialData?.company || "Target Enterprise");
  const [jobTitle, setJobTitle] = useState(initialData?.jobTitle || "Backend Systems Engineer");
  const [subject, setSubject] = useState(`Application: ${jobTitle} — M.S. Mohamed Sujahath`);
  const [body, setBody] = useState(
    initialData?.context ||
      `Dear Hiring Team,\n\nI am writing to express my strong interest in the ${jobTitle} opening at ${company}.\n\nAs a Backend Software Engineer with 2+ years of production experience owning Python/FastAPI architectures, distributed telemetry, and PostgreSQL/TimescaleDB systems, I eliminated polling failures from ~80% to 0% and reduced controller cold-start latency by 90%.\n\nI am based in Sri Lanka and 100% prepared for immediate international relocation with zero visa or onboarding friction.\n\nPlease find my attached Europass CV for your review.\n\nBest regards,\nM.S. Mohamed Sujahath\n+971 50 229 1865 | sujahathmhmd@gmail.com`
  );

  const [safeMode, setSafeMode] = useState(true);
  const [sending, setSending] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  React.useEffect(() => {
    if (initialData?.hrEmail) setToEmail(initialData.hrEmail);
    if (initialData?.company) setCompany(initialData.company);
    if (initialData?.jobTitle) {
      setJobTitle(initialData.jobTitle);
      setSubject(`Application: ${initialData.jobTitle} — M.S. Mohamed Sujahath`);
    }
    if (initialData?.context) setBody(initialData.context);
  }, [initialData]);

  const handleSend = async () => {
    setSending(true);
    setStatusMessage(null);
    try {
      const res = await sendEmail({
        to_email: toEmail,
        subject,
        body,
        company,
        job_title: jobTitle,
        dry_run: safeMode,
      });

      if (res.status === "success") {
        setStatusMessage({
          type: "success",
          text: safeMode
            ? `[Safe Mode] Outreach email drafted & logged in database (ID: ${res.application_id}). No real email sent.`
            : `Email dispatched successfully to ${toEmail} via SMTP!`,
        });
        if (onSentSuccess) onSentSuccess();
      } else {
        setStatusMessage({ type: "error", text: res.message || "Failed to send email." });
      }
    } catch (err: any) {
      setStatusMessage({ type: "error", text: err.message || "Dispatch error." });
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex flex-col gap-5 p-6 max-w-5xl mx-auto">
      <div className="p-4 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-[20px] font-semibold text-[#e3e1ec] tracking-tight flex items-center gap-2">
              <Send className="w-5 h-5 text-[#4cd7f6]" />
              Cold Email Dispatcher &amp; SMTP Pipeline
            </h1>
            <p className="text-[13px] text-[#bcc9cd] mt-0.5">
              Draft, customize, and dispatch verified cold emails with attached Europass CVs directly to recruiters.
            </p>
          </div>

          {/* Safe Mode Switch */}
          <div className="flex items-center gap-2 bg-[#1a1b22] px-3 py-1.5 rounded-lg border border-[#3d494c]/40">
            <Shield className={`w-4 h-4 ${safeMode ? "text-[#4edea3]" : "text-[#ffb4ab]"}`} />
            <span className="text-xs font-mono text-[#e3e1ec]">Safe Mode:</span>
            <button
              onClick={() => setSafeMode(!safeMode)}
              className={`text-xs font-bold px-2 py-0.5 rounded transition-all ${
                safeMode ? "bg-[#4edea3]/20 text-[#4edea3]" : "bg-[#93000a]/20 text-[#ffb4ab]"
              }`}
            >
              {safeMode ? "ON (Draft Only)" : "OFF (Live SMTP)"}
            </button>
          </div>
        </div>

        {/* Inputs */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2 border-t border-[#3d494c]/20">
          <div>
            <label className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1 block">To Recruiter Email</label>
            <input
              type="email"
              value={toEmail}
              onChange={(e) => setToEmail(e.target.value)}
              className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none font-mono"
            />
          </div>
          <div>
            <label className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1 block">Company Name</label>
            <input
              type="text"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none"
            />
          </div>
          <div>
            <label className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1 block">Target Title</label>
            <input
              type="text"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none"
            />
          </div>
        </div>

        <div>
          <label className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1 block">Subject Line</label>
          <input
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none"
          />
        </div>

        <div>
          <label className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1 block">Email Message Body</label>
          <textarea
            rows={10}
            value={body}
            onChange={(e) => setBody(e.target.value)}
            className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none font-mono leading-relaxed"
          />
        </div>

        {statusMessage && (
          <div
            className={`p-3 rounded-lg flex items-center gap-2 text-xs font-mono ${
              statusMessage.type === "success"
                ? "bg-[#4edea3]/10 border border-[#4edea3]/30 text-[#4edea3]"
                : "bg-[#93000a]/20 border border-[#93000a]/40 text-[#ffb4ab]"
            }`}
          >
            {statusMessage.type === "success" ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
            <span>{statusMessage.text}</span>
          </div>
        )}

        <div className="flex justify-end gap-3 pt-2">
          <button
            onClick={handleSend}
            disabled={sending}
            className="px-6 py-2 rounded-lg bg-[#4cd7f6] text-[#003640] font-semibold text-[13px] hover:bg-white transition-all cyan-glow disabled:opacity-50 flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
            <span>{sending ? "Sending..." : safeMode ? "Save Outreach Draft" : "Dispatch Live Email"}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
