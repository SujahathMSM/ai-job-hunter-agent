"use client";

import React, { useEffect, useState } from "react";
import { UserCheck, UploadCloud, CheckCircle2, Briefcase, GraduationCap, Code } from "lucide-react";
import { CandidateProfile } from "../../types";
import { fetchProfile, uploadCVFile } from "../../lib/api";

export default function ProfileView() {
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  useEffect(() => {
    fetchProfile().then(setProfile).catch(console.error);
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    setUploading(true);
    setUploadStatus(null);
    try {
      const res = await uploadCVFile(file);
      setProfile(res.profile);
      setUploadStatus("CV successfully parsed and merged into Master Persona!");
    } catch (err: any) {
      setUploadStatus("Failed to parse CV. Ensure it is a valid PDF or DOCX file.");
    } finally {
      setUploading(false);
    }
  };

  if (!profile) {
    return <div className="p-8 text-center text-[#bcc9cd]">Loading Candidate Master Persona...</div>;
  }

  const { identity, core_skills, technical_stack, work_history, education } = profile;

  return (
    <div className="flex flex-col gap-5 p-6 max-w-7xl mx-auto">
      {/* Identity Card */}
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
          </div>
        </div>

        {/* CV Upload Button */}
        <div className="flex flex-col items-end gap-1.5">
          <label className="px-4 py-2 rounded-lg bg-[#292931] border border-[#3d494c]/50 text-xs font-semibold text-[#e3e1ec] hover:border-[#4cd7f6] cursor-pointer transition-colors flex items-center gap-2">
            <UploadCloud className="w-4 h-4 text-[#4cd7f6]" />
            <span>{uploading ? "Parsing CV..." : "Upload & Parse New CV"}</span>
            <input type="file" accept=".pdf,.docx,.txt" onChange={handleFileUpload} className="hidden" />
          </label>
          {uploadStatus && <span className="text-[11px] text-[#4edea3] font-mono">{uploadStatus}</span>}
        </div>
      </div>

      {/* Summary */}
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

      {/* Work History */}
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
                  <div className="text-[#4cd7f6] mt-0.5 font-medium">{w.company} &nbsp;•&nbsp; {w.location}</div>
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

      {/* Education */}
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
