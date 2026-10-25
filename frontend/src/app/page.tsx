"use client";

import React, { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import ProfileView from "../components/views/ProfileView";
import JobHunterView from "../components/views/JobHunterView";
import CVTailorView from "../components/views/CVTailorView";
import ColdEmailView from "../components/views/ColdEmailView";
import RecruiterFinderView from "../components/views/RecruiterFinderView";
import TrackerView from "../components/views/TrackerView";
import SettingsView from "../components/views/SettingsView";
import { fetchProfile, fetchApplications } from "../lib/api";
import { JobItem } from "../types";

export default function Home() {
  const [activeTab, setActiveTab] = useState("recruiters");
  const [candidateName, setCandidateName] = useState("M.S. Mohamed Sujahath");
  const [stats, setStats] = useState({
    matched: 74,
    tailored: 18,
    sent: 12,
  });

  // Cross-tab pipeline state
  const [selectedJobForTailor, setSelectedJobForTailor] = useState<any>(null);
  const [selectedOutreachData, setSelectedOutreachData] = useState<any>(null);

  useEffect(() => {
    fetchProfile()
      .then((p) => {
        if (p?.identity?.full_name) {
          setCandidateName(p.identity.full_name);
        }
      })
      .catch(console.error);

    fetchApplications()
      .then((data) => {
        const apps = data.applications || [];
        const sent = apps.filter((a) => a.status === "Applied").length;
        const drafted = apps.filter((a) => a.status === "Drafted").length;
        setStats({
          matched: Math.max(apps.length * 3, 25),
          tailored: Math.max(drafted + sent, 12),
          sent: sent,
        });
      })
      .catch(console.error);
  }, []);

  const handleSelectForTailor = (job: JobItem) => {
    setSelectedJobForTailor({
      job_title: job.job_title,
      company: job.company,
      location: job.location,
      description: job.full_description || job.description,
    });
    setActiveTab("tailor");
  };

  const handleSelectForOutreach = (job: JobItem) => {
    if (!job.hr_email && job.portal) {
      window.open(job.portal, "_blank");
      return;
    }
    setSelectedOutreachData({
      jobTitle: job.job_title,
      company: job.company,
      hrEmail: job.hr_email || "careers@company.com",
      context: job.full_description || job.description,
    });
    setActiveTab("outreach");
  };

  const handleRecruiterOutreach = (jobTitle: string, company: string, email: string, portal: string, desc: string) => {
    setSelectedOutreachData({
      jobTitle: jobTitle,
      company: company,
      hrEmail: email,
      context: desc,
    });
    setActiveTab("outreach");
  };

  const handleTailorToOutreach = (jobTitle: string, company: string, context: string) => {
    setSelectedOutreachData({
      jobTitle: jobTitle,
      company: company,
      context: context,
    });
    setActiveTab("outreach");
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#12131a] text-[#e3e1ec]">
      {/* Sidebar (Fixed 256px) */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} stats={stats} />

      {/* Main Workspace */}
      <div className="pl-64 flex flex-col flex-1 h-screen overflow-hidden">
        {/* Top Header */}
        <Header candidateName={candidateName} />

        {/* Scrollable View Container (Keeps views mounted so tab switching never wipes search state) */}
        <main className="flex-1 overflow-y-auto">
          <div className={activeTab === "profile" ? "block" : "hidden"}>
            <ProfileView />
          </div>
          <div className={activeTab === "hunter" ? "block" : "hidden"}>
            <JobHunterView
              onSelectForTailor={handleSelectForTailor}
              onSelectForOutreach={handleSelectForOutreach}
            />
          </div>
          <div className={activeTab === "tailor" ? "block" : "hidden"}>
            <CVTailorView
              initialJob={selectedJobForTailor}
              onProceedToOutreach={handleTailorToOutreach}
            />
          </div>
          <div className={activeTab === "outreach" ? "block" : "hidden"}>
            <ColdEmailView
              initialData={selectedOutreachData}
              onSentSuccess={() => {
                fetchApplications().then((d) => {
                  const apps = d.applications || [];
                  setStats((prev) => ({ ...prev, sent: prev.sent + 1 }));
                });
              }}
            />
          </div>
          <div className={activeTab === "recruiters" ? "block" : "hidden"}>
            <RecruiterFinderView onSelectForOutreach={handleRecruiterOutreach} />
          </div>
          <div className={activeTab === "tracker" ? "block" : "hidden"}>
            <TrackerView />
          </div>
          <div className={activeTab === "settings" ? "block" : "hidden"}>
            <SettingsView />
          </div>
        </main>
      </div>
    </div>
  );
}
