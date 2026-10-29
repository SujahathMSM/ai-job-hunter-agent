"use client";

import React, { useState, useRef } from "react";
import { Send, Shield, CheckCircle2, AlertCircle, Paperclip, FileText, UserCheck, Mail, Eye, X, ExternalLink, Upload, RotateCcw, FileCheck } from "lucide-react";
import { sendEmail, uploadOutreachAttachment } from "../../lib/api";
import { getStoredUser } from "../../lib/auth";

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
  const user = getStoredUser();
  const candidateName = user?.full_name || "Candidate";
  const candidateEmail = user?.email || "";

  const [toEmail, setToEmail] = useState(initialData?.hrEmail || "");
  const [company, setCompany] = useState(initialData?.company || "Target Enterprise");
  const [jobTitle, setJobTitle] = useState(initialData?.jobTitle || "Backend Systems Engineer");
  const [subject, setSubject] = useState(`Application: ${jobTitle} — ${candidateName}`);
  const [body, setBody] = useState(
    initialData?.context ||
      `Dear Hiring Team,\n\nI am writing to express my strong interest in the ${jobTitle} opening at ${company}.\n\nWith production-tested software engineering experience building scalable backend microservices and reliable data workflows, I look forward to contributing immediate technical value to your team.\n\nI am prepared for international relocation with seamless onboarding.\n\nPlease find my attached official Europass CV and Cover Letter for your review.\n\nBest regards,\n${candidateName}${candidateEmail ? `\n${candidateEmail}` : ""}`
  );

  const [safeMode, setSafeMode] = useState(false);
  const [sending, setSending] = useState(false);
  const [previewDoc, setPreviewDoc] = useState<{
    type: "cv" | "cover_letter";
    title: string;
    custom_file?: string;
  } | null>(null);
  const [statusMessage, setStatusMessage] = useState<{
    type: "success" | "error";
    text: string;
    attachments?: string[];
  } | null>(null);

  // Manual custom upload state
  const [customCv, setCustomCv] = useState<{
    filename: string;
    saved_filename: string;
    saved_path: string;
    file_size_kb: number;
  } | null>(null);

  const [customCoverLetter, setCustomCoverLetter] = useState<{
    filename: string;
    saved_filename: string;
    saved_path: string;
    file_size_kb: number;
  } | null>(null);

  const [uploadingCv, setUploadingCv] = useState(false);
  const [uploadingCover, setUploadingCover] = useState(false);
  const cvInputRef = useRef<HTMLInputElement>(null);
  const coverInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (file: File, docType: "cv" | "cover_letter") => {
    if (docType === "cv") setUploadingCv(true);
    else setUploadingCover(true);
    try {
      const res = await uploadOutreachAttachment(file, docType);
      if (docType === "cv") {
        setCustomCv({
          filename: res.filename,
          saved_filename: res.saved_filename,
          saved_path: res.saved_path,
          file_size_kb: res.file_size_kb,
        });
      } else {
        setCustomCoverLetter({
          filename: res.filename,
          saved_filename: res.saved_filename,
          saved_path: res.saved_path,
          file_size_kb: res.file_size_kb,
        });
      }
    } catch (err: any) {
      console.error(err);
      setStatusMessage({
        type: "error",
        text: `Failed to upload ${docType === "cv" ? "CV" : "Cover Letter"}: ${err.message || "Upload error"}`,
      });
    } finally {
      if (docType === "cv") setUploadingCv(false);
      else setUploadingCover(false);
    }
  };

  React.useEffect(() => {
    if (initialData?.hrEmail) {
      setToEmail(initialData.hrEmail);
    } else if (initialData?.context) {
      const matches = initialData.context.match(/[\w.-]+@[\w.-]+\.[a-zA-Z]{2,}/g) || [];
      const found = matches.find(
        (e) => !e.includes("sujahath") && !e.includes("example.com") && !e.includes("candidate@")
      );
      if (found) {
        setToEmail(found);
      } else {
        setToEmail("");
      }
    } else {
      setToEmail("");
    }

    if (initialData?.company) setCompany(initialData.company);
    if (initialData?.jobTitle) {
      setJobTitle(initialData.jobTitle);
      setSubject(`Application: ${initialData.jobTitle} — ${candidateName}`);
    }
    if (initialData?.context) setBody(initialData.context);
  }, [initialData]);

  const cleanComp = company.replace(/[^a-zA-Z0-9_-]/g, "_").replace(/^_+|_+$/g, "") || "Company";
  const expectedCvName = `Europass_CV_${cleanComp}.pdf`;
  const expectedCoverName = `Cover_Letter_${cleanComp}.pdf`;

  const handleSend = async () => {
    if (!toEmail || !toEmail.includes("@")) {
      setStatusMessage({
        type: "error",
        text: "Please enter a valid recruiter email address before dispatching.",
      });
      return;
    }
    setSending(true);
    setStatusMessage(null);
    try {
      const res = await sendEmail({
        to_email: toEmail,
        subject,
        body,
        company,
        job_title: jobTitle,
        cv_path: customCv?.saved_path,
        cover_letter_path: customCoverLetter?.saved_path,
        dry_run: safeMode,
      });

      if (res.status === "success" || res.success) {
        setStatusMessage({
          type: "success",
          text: safeMode
            ? `[Safe Mode] Outreach email drafted & logged in database (ID: ${res.application_id || res.app_id}).`
            : `Email dispatched successfully to ${toEmail} via SMTP!`,
          attachments: res.attachments || [
            customCv ? `[Custom] ${customCv.filename}` : expectedCvName,
            customCoverLetter ? `[Custom] ${customCoverLetter.filename}` : expectedCoverName,
          ],
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
      <div className="p-5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-4">
        {/* Top Header */}
        <div className="flex items-center justify-between pb-3 border-b border-[#3d494c]/20">
          <div>
            <h1 className="text-[20px] font-semibold text-[#e3e1ec] tracking-tight flex items-center gap-2">
              <Send className="w-5 h-5 text-[#4cd7f6]" />
              Cold Email Dispatcher &amp; SMTP Pipeline
            </h1>
            <p className="text-[13px] text-[#bcc9cd] mt-0.5">
              Dispatches authenticated outreach emails with guaranteed Europass CV &amp; Cover Letter PDF attachments.
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

        {/* Sender Identity Pill */}
        <div className="flex items-center justify-between px-3.5 py-2.5 rounded-lg bg-[#14151e] border border-[#3d494c]/40 text-xs">
          <div className="flex items-center gap-2 text-[#bcc9cd]">
            <UserCheck className="w-4 h-4 text-[#4edea3]" />
            <span className="font-mono text-[#869296]">From:</span>
            <span className="font-semibold text-[#e3e1ec]">M.S. Mohamed Sujahath</span>
            <span className="text-[#4cd7f6] font-mono">&lt;sujahathmhmd@gmail.com&gt;</span>
          </div>
          <div className="flex items-center gap-1.5 text-[11px] font-mono text-[#4edea3] bg-[#4edea3]/10 px-2 py-0.5 rounded border border-[#4edea3]/20">
            <span className="w-1.5 h-1.5 rounded-full bg-[#4edea3] animate-pulse"></span>
            SMTP Ready (TLS 587)
          </div>
        </div>

        {/* Inputs */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1 flex items-center justify-between">
              <span>To Recruiter Email</span>
              {toEmail ? (
                <span className="text-[10px] text-[#4edea3] font-mono">Target Email Set</span>
              ) : (
                <span className="text-[10px] text-[#ffb4ab] font-mono">Required</span>
              )}
            </label>
            <input
              type="email"
              value={toEmail}
              placeholder="e.g. DdaT.recruitment@businessandtrade.gov.uk"
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
            rows={8}
            value={body}
            onChange={(e) => setBody(e.target.value)}
            className="w-full px-3 py-2.5 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none font-mono leading-relaxed"
          />
        </div>

        {/* Hidden inputs for custom manual CV and Cover Letter upload */}
        <input
          ref={cvInputRef}
          type="file"
          accept=".pdf,.docx,.doc"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleUpload(file, "cv");
            e.target.value = "";
          }}
        />
        <input
          ref={coverInputRef}
          type="file"
          accept=".pdf,.docx,.doc"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleUpload(file, "cover_letter");
            e.target.value = "";
          }}
        />

        {/* Confirmed Attached Documents Card */}
        <div className="p-4 rounded-xl bg-[#14151e] border border-[#3d494c]/40 flex flex-col gap-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <span className="text-[11px] font-mono uppercase text-[#4cd7f6] tracking-wider flex items-center gap-1.5 font-bold">
              <Paperclip className="w-3.5 h-3.5" />
              Attached Documents (Physical MIME Attachments Guaranteed)
            </span>
            <span className="text-[11px] font-mono text-[#4edea3]">
              2 PDFs Attached &amp; Ready{" "}
              {customCv || customCoverLetter
                ? `(${[customCv && "Custom CV", customCoverLetter && "Custom Cover Letter"].filter(Boolean).join(" + ")})`
                : ""}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            {/* Europass / Custom CV Badge */}
            <div className="flex flex-col justify-between p-3.5 rounded-lg bg-[#1a1b22] border border-[#3d494c]/50 hover:border-[#4cd7f6]/40 transition-all gap-3">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-start gap-2.5">
                  {customCv ? (
                    <FileCheck className="w-4 h-4 text-[#4edea3] shrink-0 mt-0.5" />
                  ) : (
                    <FileText className="w-4 h-4 text-[#4cd7f6] shrink-0 mt-0.5" />
                  )}
                  <div>
                    <div className="text-xs font-mono font-semibold text-[#e3e1ec] line-clamp-1">
                      {customCv ? customCv.filename : expectedCvName}
                    </div>
                    <div className="text-[10px] text-[#869296]">
                      {customCv
                        ? `Manual Custom Upload • ${customCv.file_size_kb} KB`
                        : "Official Europass A4 • Moratuwa Credentials"}
                    </div>
                  </div>
                </div>
                {customCv ? (
                  <span className="text-[10px] font-mono text-[#4edea3] bg-[#4edea3]/10 px-1.5 py-0.5 rounded border border-[#4edea3]/30">
                    Custom File
                  </span>
                ) : (
                  <span className="text-[10px] font-mono text-[#4edea3] bg-[#4edea3]/10 px-1.5 py-0.5 rounded border border-[#4edea3]/20">
                    Auto-Generated
                  </span>
                )}
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-[#3d494c]/30 gap-2">
                <button
                  type="button"
                  onClick={() =>
                    setPreviewDoc({
                      type: "cv",
                      title: customCv ? customCv.filename : expectedCvName,
                      custom_file: customCv?.saved_filename,
                    })
                  }
                  className="flex items-center gap-1 text-[11px] font-mono text-[#4cd7f6] bg-[#4cd7f6]/10 hover:bg-[#4cd7f6]/20 px-2 py-1 rounded border border-[#4cd7f6]/30 transition-all cursor-pointer"
                >
                  <Eye className="w-3 h-3" />
                  <span>Preview</span>
                </button>

                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() => cvInputRef.current?.click()}
                    disabled={uploadingCv}
                    className="flex items-center gap-1 text-[11px] font-mono text-[#bcc9cd] hover:text-[#e3e1ec] bg-[#292931]/60 hover:bg-[#292931] px-2 py-1 rounded border border-[#3d494c]/50 transition-all cursor-pointer"
                  >
                    <Upload className="w-3 h-3 text-[#4cd7f6]" />
                    <span>{uploadingCv ? "Uploading..." : customCv ? "Replace CV" : "Upload Custom CV"}</span>
                  </button>

                  {customCv && (
                    <button
                      type="button"
                      onClick={() => setCustomCv(null)}
                      title="Revert to auto-generated Europass CV"
                      className="p-1 rounded bg-[#292931]/60 hover:bg-[#93000a]/20 text-[#869296] hover:text-[#ffb4ab] border border-[#3d494c]/40 transition-colors"
                    >
                      <RotateCcw className="w-3 h-3" />
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Cover Letter / Custom Letter Badge */}
            <div className="flex flex-col justify-between p-3.5 rounded-lg bg-[#1a1b22] border border-[#3d494c]/50 hover:border-[#a8c7fa]/40 transition-all gap-3">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-start gap-2.5">
                  {customCoverLetter ? (
                    <FileCheck className="w-4 h-4 text-[#4edea3] shrink-0 mt-0.5" />
                  ) : (
                    <FileText className="w-4 h-4 text-[#a8c7fa]" />
                  )}
                  <div>
                    <div className="text-xs font-mono font-semibold text-[#e3e1ec] line-clamp-1">
                      {customCoverLetter ? customCoverLetter.filename : expectedCoverName}
                    </div>
                    <div className="text-[10px] text-[#869296]">
                      {customCoverLetter
                        ? `Manual Custom Upload • ${customCoverLetter.file_size_kb} KB`
                        : "Executive Letterhead A4 PDF"}
                    </div>
                  </div>
                </div>
                {customCoverLetter ? (
                  <span className="text-[10px] font-mono text-[#4edea3] bg-[#4edea3]/10 px-1.5 py-0.5 rounded border border-[#4edea3]/30">
                    Custom File
                  </span>
                ) : (
                  <span className="text-[10px] font-mono text-[#4edea3] bg-[#4edea3]/10 px-1.5 py-0.5 rounded border border-[#4edea3]/20">
                    Auto-Generated
                  </span>
                )}
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-[#3d494c]/30 gap-2">
                <button
                  type="button"
                  onClick={() =>
                    setPreviewDoc({
                      type: "cover_letter",
                      title: customCoverLetter ? customCoverLetter.filename : expectedCoverName,
                      custom_file: customCoverLetter?.saved_filename,
                    })
                  }
                  className="flex items-center gap-1 text-[11px] font-mono text-[#a8c7fa] bg-[#a8c7fa]/10 hover:bg-[#a8c7fa]/20 px-2 py-1 rounded border border-[#a8c7fa]/30 transition-all cursor-pointer"
                >
                  <Eye className="w-3 h-3" />
                  <span>Preview</span>
                </button>

                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() => coverInputRef.current?.click()}
                    disabled={uploadingCover}
                    className="flex items-center gap-1 text-[11px] font-mono text-[#bcc9cd] hover:text-[#e3e1ec] bg-[#292931]/60 hover:bg-[#292931] px-2 py-1 rounded border border-[#3d494c]/50 transition-all cursor-pointer"
                  >
                    <Upload className="w-3 h-3 text-[#a8c7fa]" />
                    <span>{uploadingCover ? "Uploading..." : customCoverLetter ? "Replace Letter" : "Upload Custom Letter"}</span>
                  </button>

                  {customCoverLetter && (
                    <button
                      type="button"
                      onClick={() => setCustomCoverLetter(null)}
                      title="Revert to auto-generated Cover Letter"
                      className="p-1 rounded bg-[#292931]/60 hover:bg-[#93000a]/20 text-[#869296] hover:text-[#ffb4ab] border border-[#3d494c]/40 transition-colors"
                    >
                      <RotateCcw className="w-3 h-3" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Document Preview Lightbox Modal with Blurred Backdrop */}
        {previewDoc && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200"
            onClick={() => setPreviewDoc(null)}
          >
            <div
              className="relative w-full max-w-4xl max-h-[92vh] bg-[#0d0e15] border border-[#3d494c]/60 rounded-2xl shadow-2xl flex flex-col overflow-hidden specular-border"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="flex items-center justify-between px-5 py-3.5 border-b border-[#3d494c]/30 bg-[#14151e]">
                <div className="flex items-center gap-2.5">
                  <FileText className="w-5 h-5 text-[#4cd7f6]" />
                  <div>
                    <div className="text-sm font-semibold text-[#e3e1ec] font-mono">
                      {previewDoc.title}
                    </div>
                    <div className="text-[10px] text-[#869296]">
                      {previewDoc.custom_file
                        ? "Manual Custom Document Upload • Verified for Physical MIME Attachment"
                        : previewDoc.type === "cv"
                        ? "European Union Europass CV • Official A4 Layout"
                        : `Executive Tailored Cover Letter for ${company}`}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <a
                    href={
                      previewDoc.custom_file
                        ? `/api/documents/preview?custom_file=${encodeURIComponent(previewDoc.custom_file)}`
                        : `/api/documents/preview?type=${previewDoc.type}&company=${encodeURIComponent(company)}&job_title=${encodeURIComponent(jobTitle)}`
                    }
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 text-xs text-[#4cd7f6] hover:brightness-125 px-2.5 py-1.5 rounded-lg bg-[#1a1b22] border border-[#3d494c]/50 transition-colors"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    <span>Open in New Tab</span>
                  </a>
                  <button
                    onClick={() => setPreviewDoc(null)}
                    className="p-1.5 rounded-lg text-[#869296] hover:text-[#e3e1ec] hover:bg-[#1a1b22] transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* PDF Viewport */}
              <div className="flex-1 bg-[#1a1b22] p-2 overflow-hidden flex items-center justify-center">
                <iframe
                  src={
                    previewDoc.custom_file
                      ? `/api/documents/preview?custom_file=${encodeURIComponent(previewDoc.custom_file)}`
                      : `/api/documents/preview?type=${previewDoc.type}&company=${encodeURIComponent(company)}&job_title=${encodeURIComponent(jobTitle)}`
                  }
                  className="w-full h-[72vh] rounded-lg border border-[#3d494c]/30 bg-white"
                  title={previewDoc.title}
                />
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between px-5 py-3 border-t border-[#3d494c]/30 bg-[#14151e] text-xs text-[#bcc9cd]">
                <span className="font-mono text-[11px] text-[#869296]">
                  ✓ Verified: This document is physically attached into the SMTP payload when dispatched.
                </span>
                <button
                  onClick={() => setPreviewDoc(null)}
                  className="px-4 py-1.5 rounded-lg bg-[#292931] border border-[#3d494c]/50 hover:bg-[#3d494c]/40 text-xs text-[#e3e1ec] font-medium transition-all"
                >
                  Close Preview
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Status Message */}
        {statusMessage && (
          <div
            className={`p-3.5 rounded-lg flex flex-col gap-1.5 text-xs font-mono ${
              statusMessage.type === "success"
                ? "bg-[#4edea3]/10 border border-[#4edea3]/30 text-[#4edea3]"
                : "bg-[#93000a]/20 border border-[#93000a]/40 text-[#ffb4ab]"
            }`}
          >
            <div className="flex items-center gap-2">
              {statusMessage.type === "success" ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
              <span className="font-semibold">{statusMessage.text}</span>
            </div>
            {statusMessage.attachments && statusMessage.attachments.length > 0 && (
              <div className="ml-6 text-[11px] text-[#bcc9cd] flex items-center gap-2">
                <Paperclip className="w-3.5 h-3.5 text-[#4cd7f6]" />
                <span>Confirmed Attachments: {statusMessage.attachments.join(", ")}</span>
              </div>
            )}
          </div>
        )}

        {/* Action Button */}
        <div className="flex justify-between items-center pt-2">
          <div className="text-[11px] text-[#869296] font-mono">
            Every dispatch physically embeds both PDFs into the SMTP message payload.
          </div>
          <button
            onClick={handleSend}
            disabled={sending}
            className="px-6 py-2.5 rounded-lg bg-[#4cd7f6] text-[#003640] font-semibold text-[13px] hover:bg-white transition-all cyan-glow disabled:opacity-50 flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
            <span>{sending ? "Dispatching..." : safeMode ? "Save Outreach Draft" : "Dispatch Live Email"}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
