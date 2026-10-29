"use client";

import React from "react";
import {
  UserCheck,
  Radar,
  Building2,
  Sparkles,
  Send,
  UserSearch,
  KanbanSquare,
  Terminal,
  Settings as SettingsIcon,
  Zap,
  Globe,
  Laptop,
} from "lucide-react";

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  stats: {
    matched: number;
    tailored: number;
    sent: number;
  };
}

export default function Sidebar({ activeTab, setActiveTab, stats }: SidebarProps) {
  const navItems = [
    { id: "profile", label: "Profile & CV Intake", icon: UserCheck },
    { id: "hunter", label: "Live Job Hunter", icon: Radar },
    { id: "dubai", label: "Dubai Job Hunter", icon: Building2, badge: "UAE" },
    { id: "remote", label: "Global Remote Jobs", icon: Laptop, badge: "Worldwide" },
    { id: "portals", label: "Career Portals", icon: Globe, badge: "Direct" },
    { id: "tailor", label: "AI CV Tailor", icon: Sparkles },
    { id: "outreach", label: "Cold Email Dispatcher", icon: Send },
    { id: "recruiters", label: "Recruiter Finder", icon: UserSearch, badge: "99%" },
    { id: "tracker", label: "Application Tracker", icon: KanbanSquare },
  ];

  return (
    <aside className="fixed top-0 left-0 h-screen w-64 flex flex-col z-40 border-r border-[#3d494c]/30 bg-[#0d0e15] select-none">
      <div className="w-64 h-full flex flex-col justify-between p-4">
        {/* Brand Area */}
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-3 px-1 py-1">
            <div className="w-8 h-8 rounded-lg bg-[#292931] border border-[#3d494c]/50 flex items-center justify-center cyan-glow">
              <Zap className="w-4 h-4 text-[#4cd7f6]" />
            </div>
            <div>
              <div className="text-[15px] font-semibold tracking-tight text-[#e3e1ec]">NexusHunt AI</div>
              <div className="text-[10px] uppercase font-mono tracking-wider text-[#bcc9cd]">Autonomous Career Agent</div>
            </div>
          </div>

          {/* Global Agent Status Pill */}
          <div className="p-2.5 rounded-lg bg-[#1a1b22] border border-[#3d494c]/40 flex flex-col gap-1.5 specular-border">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#4cd7f6] pulse-glow"></span>
                <span className="text-[10px] font-mono tracking-wider text-[#4cd7f6] font-semibold">AGENT: ACTIVE</span>
              </div>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#292931] border border-[#3d494c]/40 text-[#bcc9cd]">v2.4</span>
            </div>
            <div className="text-[11px] text-[#bcc9cd] flex items-center justify-between pt-1 border-t border-[#3d494c]/20">
              <span>Target Geo:</span>
              <span className="text-[#4edea3] font-medium">Gulf &amp; Global Remote</span>
            </div>
          </div>

          {/* Nav Items */}
          <nav className="flex flex-col gap-1 mt-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg text-[13px] transition-all duration-150 text-left ${
                    isActive
                      ? "bg-[#292931] text-[#4cd7f6] border-l-2 border-[#4cd7f6] font-medium"
                      : "text-[#bcc9cd] hover:text-[#e3e1ec] hover:bg-[#1e1f26]/50"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? "text-[#4cd7f6]" : "text-[#869397]"}`} />
                  <span className="flex-1">{item.label}</span>
                  {item.badge && (
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#4cd7f6]/10 border border-[#4cd7f6]/30 text-[#4cd7f6]">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Footer Actions & Stats Micro Bar */}
        <div className="flex flex-col gap-3">
          <button
            onClick={() => setActiveTab("hunter")}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg bg-[#4cd7f6] text-[#003640] font-medium hover:bg-white transition-all duration-150 active:scale-[0.98] shadow-sm cyan-glow text-[13px]"
          >
            <Zap className="w-4 h-4" />
            <span>Run Agent Pipeline</span>
          </button>

          {/* Stats Bar */}
          <div className="grid grid-cols-3 gap-1 py-2 px-2 bg-[#1a1b22] rounded-lg border border-[#3d494c]/30 text-center font-mono text-[11px]">
            <div>
              <div className="text-[#e3e1ec] font-semibold">{stats.matched}</div>
              <div className="text-[9px] text-[#bcc9cd] tracking-wider uppercase">MATCHED</div>
            </div>
            <div className="border-x border-[#3d494c]/20">
              <div className="text-[#4cd7f6] font-semibold">{stats.tailored}</div>
              <div className="text-[9px] text-[#bcc9cd] tracking-wider uppercase">TAILORED</div>
            </div>
            <div>
              <div className="text-[#4edea3] font-semibold">{stats.sent}</div>
              <div className="text-[9px] text-[#bcc9cd] tracking-wider uppercase">SENT</div>
            </div>
          </div>

          {/* Settings Tab */}
          <div className="pt-2 border-t border-[#3d494c]/20 flex flex-col gap-1">
            <button
              onClick={() => setActiveTab("settings")}
              className={`flex items-center gap-3 px-3 py-1.5 rounded-lg text-[13px] transition-colors ${
                activeTab === "settings" ? "bg-[#292931] text-[#4cd7f6]" : "text-[#bcc9cd] hover:text-[#e3e1ec] hover:bg-[#1e1f26]/50"
              }`}
            >
              <SettingsIcon className="w-4 h-4 text-[#869397]" />
              <span>Settings &amp; Keys</span>
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}
