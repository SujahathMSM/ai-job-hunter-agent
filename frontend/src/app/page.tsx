"use client";

import React, { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import ProfileView from "../components/views/ProfileView";
import JobHunterView from "../components/views/JobHunterView";
import GlobalRemoteJobsView from "../components/views/GlobalRemoteJobsView";
import CareerPortalsView from "../components/views/CareerPortalsView";
import CVTailorView from "../components/views/CVTailorView";
import ColdEmailView from "../components/views/ColdEmailView";
import RecruiterFinderView from "../components/views/RecruiterFinderView";
import TrackerView from "../components/views/TrackerView";
import SettingsView from "../components/views/SettingsView";
import AuthModal from "../components/AuthModal";
import { fetchProfile, fetchApplications } from "../lib/api";
import { getStoredUser, clearSession, AuthUser } from "../lib/auth";
import { JobItem } from "../types";

export default function Home() {
  const [activeTab, setActiveTab] = useState("remote");
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(getStoredUser());
  const [candidateName, setCandidateName] = useState(currentUser?.full_name || "M.S. Mohamed Sujahath");
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [stats, setStats] = useState({
    matched: 74,
    tailored: 18,
    sent: 12,
  });

  const VALID_TABS = ["profile", "hunter", "remote", "portals", "tailor", "outreach", "recruiters", "tracker", "settings"];

  const navigateToTab = (tab: string, pushHistory = true) => {
    if (!VALID_TABS.includes(tab)) return;
    setActiveTab(tab);
    if (typeof window !== "undefined") {
      const targetHash = `#${tab}`;
      if (window.location.hash !== targetHash) {
        if (pushHistory) {
          window.history.pushState({ tab }, "", targetHash);
        } else {
          window.history.replaceState({ tab }, "", targetHash);
        }
      }
    }
  };

  // Cross-tab pipeline state
  const [selectedJobForTailor, setSelectedJobForTailor] = useState<any>(null);
  const [selectedOutreachData, setSelectedOutreachData] = useState<any>(null);

  useEffect(() => {
    // Synchronize browser history / URL hash with active tab so browser back/forward stays in app
    if (typeof window !== "undefined") {
      const initialHash = window.location.hash.replace("#", "");
      if (initialHash && VALID_TABS.includes(initialHash)) {
        setActiveTab(initialHash);
      } else {
        window.history.replaceState({ tab: "remote" }, "", "#remote");
        setActiveTab("remote");
      }

      const onPopState = (e: PopStateEvent) => {
        const curHash = window.location.hash.replace("#", "");
        if (curHash && VALID_TABS.includes(curHash)) {
          setActiveTab(curHash);
        } else if (e.state?.tab && VALID_TABS.includes(e.state.tab)) {
          setActiveTab(e.state.tab);
        }
      };

      window.addEventListener("popstate", onPopState);
      return () => window.removeEventListener("popstate", onPopState);
    }
  }, []);

  const loadUserData = (user?: AuthUser | null) => {
    const active = user !== undefined ? user : getStoredUser();
    setCurrentUser(active);

    if (active) {
      setCandidateName(active.full_name || "Candidate");
      fetchProfile(active.id)
        .then((p) => {
          if (p?.identity?.full_name) {
            setCandidateName(p.identity.full_name);
          }
        })
        .catch(console.error);

      fetchApplications(active.id)
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
    } else {
      setCandidateName("Guest");
      setStats({
        matched: 0,
        tailored: 0,
        sent: 0,
      });
    }
  };

  const handleLogout = () => {
    clearSession();
    loadUserData(null);
  };

  useEffect(() => {
    loadUserData();
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
    navigateToTab("tailor");
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
    navigateToTab("outreach");
  };

  const handleRecruiterOutreach = (jobTitle: string, company: string, email: string, portal: string, desc: string) => {
    const pitch = buildDefaultPitch(jobTitle, company);
    setSelectedOutreachData({
      jobTitle: jobTitle,
      company: company,
      hrEmail: email || "",
      context: pitch,
    });
    navigateToTab("outreach");
  };

  const handleTailorToOutreach = (jobTitle: string, company: string, context: string, hrEmail?: string) => {
    const finalHrEmail = hrEmail || selectedJobForTailor?.hr_email || "";
    setSelectedOutreachData({
      jobTitle: jobTitle,
      company: company,
      hrEmail: finalHrEmail,
      context: context,
    });
    navigateToTab("outreach");
  };

  const handlePortalRecruiters = (companyName: string) => {
    navigateToTab("recruiters");
  };

  const handlePortalTailor = (companyName: string, location: string) => {
    setSelectedJobForTailor({
      job_title: "Software Engineer / Backend Developer",
      company: companyName,
      location: location,
      hr_email: "",
      description: `Targeting engineering, IoT telemetry, and Python backend microservices at ${companyName}.`,
    });
    navigateToTab("tailor");
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#12131a] text-[#e3e1ec]">
      {/* Sidebar (Fixed 256px) */}
      <Sidebar activeTab={activeTab} setActiveTab={navigateToTab} stats={stats} />

      {/* Main Workspace */}
      <div className="pl-64 flex flex-col flex-1 h-screen overflow-hidden">
        {/* Top Header */}
        <Header
          candidateName={candidateName}
          currentUser={currentUser}
          onOpenAuth={() => setIsAuthOpen(true)}
          onLogout={handleLogout}
        />

        {/* Scrollable View Container (Keeps views mounted so tab switching never wipes search state) */}
        <main className="flex-1 overflow-y-auto">
          <div className={activeTab === "profile" ? "block" : "hidden"}>
            <ProfileView key={currentUser?.id || "guest"} />
          </div>
          <div className={activeTab === "hunter" ? "block" : "hidden"}>
            <JobHunterView
              key={currentUser?.id || "guest"}
              onSelectForTailor={handleSelectForTailor}
              onSelectForOutreach={handleSelectForOutreach}
            />
          </div>
          <div className={activeTab === "remote" ? "block" : "hidden"}>
            <GlobalRemoteJobsView
              key={currentUser?.id || "guest"}
              onSelectForTailor={handleSelectForTailor}
              onSelectForOutreach={handleSelectForOutreach}
              onSelectForRecruiters={(company, title) => {
                setActiveTab("recruiters");
              }}
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
              key={currentUser?.id || "guest"}
              initialJob={selectedJobForTailor}
              onProceedToOutreach={handleTailorToOutreach}
            />
          </div>
          <div className={activeTab === "outreach" ? "block" : "hidden"}>
            <ColdEmailView
              key={currentUser?.id || "guest"}
              initialData={selectedOutreachData}
              onSentSuccess={() => {
                const uid = currentUser?.id || "default";
                fetchApplications(uid).then((d) => {
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
            <TrackerView key={currentUser?.id || "guest"} />
          </div>
          <div className={activeTab === "settings" ? "block" : "hidden"}>
            <SettingsView key={currentUser?.id || "guest"} />
          </div>
        </main>
      </div>

      {/* Candidate Auth & Session Switcher Modal */}
      <AuthModal
        isOpen={isAuthOpen}
        currentUser={currentUser}
        onClose={() => setIsAuthOpen(false)}
        onUserChanged={(user) => loadUserData(user)}
        onLogout={handleLogout}
      />
    </div>
  );
}
