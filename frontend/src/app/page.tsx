"use client";

import React, { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import ProfileView from "../components/views/ProfileView";
import JobHunterView from "../components/views/JobHunterView";
import CareerPortalsView from "../components/views/CareerPortalsView";
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

  const buildDefaultPitch = (jobTitle: string, company: string): string => {
    return `Dear ${company} Hiring Team,\n\nI am writing to express my enthusiastic interest in the ${jobTitle} opening at ${company}.\n\nAs a production-tested Backend Software Engineer with a BScEngHons from the University of Moratuwa (Sri Lanka's premier engineering institution), I specialize in high-throughput microservices, distributed data architectures, and PostgreSQL/TimescaleDB optimization. In my current engineering role at Blue Brand IP Institute, I overhauled asynchronous data pipelines, reducing polling failures from 80% to 0% and slashing system startup times by 90%.\n\nI am based in Sri Lanka and 100% prepared for immediate international relocation with zero onboarding delay.\n\nPlease find my attached Europass CV for your review. I would welcome the opportunity to discuss how my background can immediately drive value for ${company}.\n\nSincerely,\nM.S. Mohamed Sujahath\n+971 50 229 1865 | sujahathmhmd@gmail.com\nlinkedin.com/in/mohamed-sujahath | github.com/SujahathMSM`;
  };

  const handleSelectForTailor = (job: JobItem) => {
    setSelectedJobForTailor({
      job_title: job.job_title,
      company: job.company,
      location: job.location,
      hr_email: job.hr_email || "",
      description: job.full_description || job.description,
    });
    setActiveTab("tailor");
  };

  const handleSelectForOutreach = (job: JobItem) => {
    if (!job.hr_email && job.portal) {
      window.open(job.portal, "_blank");
      return;
    }
    const pitch = buildDefaultPitch(job.job_title, job.company);
    setSelectedOutreachData({
      jobTitle: job.job_title,
      company: job.company,
      hrEmail: job.hr_email || "",
      context: pitch,
    });
    setActiveTab("outreach");
  };

  const handleRecruiterOutreach = (jobTitle: string, company: string, email: string, portal: string, desc: string) => {
    const pitch = buildDefaultPitch(jobTitle, company);
    setSelectedOutreachData({
      jobTitle: jobTitle,
      company: company,
      hrEmail: email || "",
      context: pitch,
    });
    setActiveTab("outreach");
  };

  const handleTailorToOutreach = (jobTitle: string, company: string, context: string, hrEmail?: string) => {
    const finalHrEmail = hrEmail || selectedJobForTailor?.hr_email || "";
    setSelectedOutreachData({
      jobTitle: jobTitle,
      company: company,
      hrEmail: finalHrEmail,
      context: context,
    });
    setActiveTab("outreach");
  };

  const handlePortalRecruiters = (companyName: string) => {
    setActiveTab("recruiters");
  };

  const handlePortalTailor = (companyName: string, location: string) => {
    setSelectedJobForTailor({
      job_title: "Software Engineer / Backend Developer",
      company: companyName,
      location: location,
      hr_email: "",
      description: `Targeting engineering, IoT telemetry, and Python backend microservices at ${companyName}.`,
    });
    setActiveTab("tailor");
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
          <div className={activeTab === "portals" ? "block" : "hidden"}>
            <CareerPortalsView
              onSelectCompanyForRecruiters={handlePortalRecruiters}
              onSelectCompanyForTailor={handlePortalTailor}
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
