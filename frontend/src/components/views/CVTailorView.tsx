"use client";

import React, { useState } from "react";
import { Sparkles, Download, FileText, CheckCircle2, ArrowRight } from "lucide-react";
import { tailorResume, downloadEuropassPDF } from "../../lib/api";

interface CVTailorViewProps {
  initialJob?: {
    job_title: string;
    company: string;
    location: string;
    description: string;
  };
  onProceedToOutreach: (jobTitle: string, company: string, context: string) => void;
}

export default function CVTailorView({ initialJob, onProceedToOutreach }: CVTailorViewProps) {
  const [jobTitle, setJobTitle] = useState(initialJob?.job_title || "Python Backend Systems Engineer");
  const [company, setCompany] = useState(initialJob?.company || "Careem");
  const [location, setLocation] = useState(initialJob?.location || "Dubai, United Arab Emirates");
  const [jdText, setJdText] = useState(initialJob?.description || "High-throughput backend engineering role in Python/FastAPI, distributed systems, PostgreSQL, and AWS.");

  const [tailoring, setTailoring] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [tailoredData, setTailoredData] = useState<any>(null);
  const [coverLetter, setCoverLetter] = useState<string>("");

  const handleTailor = async () => {
    setTailoring(true);
    try {
      const res = await tailorResume(jobTitle, company, location, jdText);
      setTailoredData(res.tailored_resume);
      setCoverLetter(res.cover_letter);
    } catch (err) {
      console.error(err);
    } finally {
      setTailoring(false);
    }
  };

  const handleDownloadPDF = async () => {
    if (!tailoredData) return;
    setDownloading(true);
    try {
      const blob = await downloadEuropassPDF(tailoredData);
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

  return (
    <div className="flex flex-col gap-5 p-6 max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="p-4 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-[20px] font-semibold text-[#e3e1ec] tracking-tight flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-[#4cd7f6]" />
              AI CV Tailor &amp; Europass PDF Generator
            </h1>
            <p className="text-[13px] text-[#bcc9cd] mt-0.5">
              Aligns your projects, metrics, and skills to the target job description and compiles standard Europass A4 PDFs.
            </p>
          </div>
          <span className="text-[11px] font-mono px-2 py-1 rounded bg-[#4cd7f6]/10 border border-[#4cd7f6]/30 text-[#4cd7f6]">
            Europass Standard (A4)
          </span>
        </div>

        {/* Form Inputs */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2 border-t border-[#3d494c]/20">
          <div>
            <label className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1 block">Target Title</label>
            <input
              type="text"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none"
            />
          </div>
          <div>
            <label className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1 block">Company</label>
            <input
              type="text"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none"
            />
          </div>
          <div>
            <label className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1 block">Location</label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none"
            />
          </div>
        </div>

        <div>
          <label className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1 block">Job Description &amp; Technical Keywords</label>
          <textarea
            rows={3}
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none font-mono"
          />
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <button
            onClick={handleTailor}
            disabled={tailoring}
            className="px-5 py-2 rounded-lg bg-[#4cd7f6] text-[#003640] font-semibold text-[13px] hover:bg-white transition-all cyan-glow disabled:opacity-50 flex items-center gap-2"
          >
            <Sparkles className="w-4 h-4" />
            <span>{tailoring ? "Tailoring Content..." : "Tailor CV & Cover Letter"}</span>
          </button>
        </div>
      </div>

      {/* Generated Content Side-by-Side */}
      {tailoredData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Left: Tailored CV Preview */}
          <div className="p-5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col justify-between">
            <div className="flex flex-col gap-4">
              <div className="flex items-center justify-between pb-3 border-b border-[#3d494c]/30">
                <div className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-[#4cd7f6]" />
                  <h3 className="text-[16px] font-semibold text-[#e3e1ec]">Tailored Europass CV</h3>
                </div>
                <button
                  onClick={handleDownloadPDF}
                  disabled={downloading}
                  className="px-3 py-1.5 rounded-lg bg-[#4edea3] text-[#003824] font-semibold text-xs hover:bg-white transition-all flex items-center gap-1.5 emerald-glow"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>{downloading ? "Building..." : "Download A4 PDF"}</span>
                </button>
              </div>

              <div>
                <span className="text-[10px] font-mono uppercase text-[#869397]">Tailored Title</span>
                <div className="text-[15px] font-semibold text-[#4cd7f6] mt-0.5">{tailoredData.tailored_title}</div>
              </div>

              <div>
                <span className="text-[10px] font-mono uppercase text-[#869397]">Professional Summary</span>
                <p className="text-[12px] text-[#bcc9cd] mt-1 leading-relaxed bg-[#1a1b22] p-3 rounded-lg border border-[#3d494c]/30">
                  {tailoredData.tailored_summary}
                </p>
              </div>

              <div>
                <span className="text-[10px] font-mono uppercase text-[#869397]">Highlighted Production Projects</span>
                <div className="flex flex-col gap-2 mt-1">
                  {tailoredData.projects?.slice(0, 3).map((p: any, i: number) => (
                    <div key={i} className="p-3 bg-[#1a1b22] rounded-lg border border-[#3d494c]/30 text-xs">
                      <strong className="text-[#e3e1ec]">{p.title}</strong>
                      <div className="text-[#4cd7f6] font-mono text-[11px] mt-0.5">{p.technologies}</div>
                      <ul className="mt-1.5 space-y-1 list-disc list-inside text-[#bcc9cd]">
                        {p.bullets?.map((b: string, bi: number) => (
                          <li key={bi}>{b}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Right: Tailored Cover Letter Preview */}
          <div className="p-5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col justify-between">
            <div className="flex flex-col gap-4">
              <div className="flex items-center justify-between pb-3 border-b border-[#3d494c]/30">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-[#4edea3]" />
                  <h3 className="text-[16px] font-semibold text-[#e3e1ec]">Tailored Cover Letter</h3>
                </div>
                <button
                  onClick={() => onProceedToOutreach(jobTitle, company, coverLetter)}
                  className="px-3 py-1.5 rounded-lg bg-[#4cd7f6] text-[#003640] font-semibold text-xs hover:bg-white transition-all flex items-center gap-1.5 cyan-glow"
                >
                  <span>Use in Email Dispatch</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="bg-[#1a1b22] p-4 rounded-lg border border-[#3d494c]/30 text-[12px] text-[#e3e1ec] font-mono whitespace-pre-wrap leading-relaxed max-h-[500px] overflow-y-auto">
                {coverLetter || "Click 'Tailor CV & Cover Letter' above to generate."}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
