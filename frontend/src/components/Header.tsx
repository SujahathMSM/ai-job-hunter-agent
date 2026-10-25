"use client";

import React from "react";
import { Search, StopCircle, Rocket, Bell, SlidersHorizontal } from "lucide-react";

interface HeaderProps {
  onSearch?: (term: string) => void;
  candidateName: string;
}

export default function Header({ candidateName }: HeaderProps) {
  return (
    <header className="sticky top-0 right-0 w-full z-30 flex justify-between items-center h-14 px-6 border-b border-[#3d494c]/30 bg-[#0d0e15]/90 backdrop-blur-md specular-border">
      {/* Search Bar */}
      <div className="flex items-center gap-4 w-1/2 max-w-xl">
        <div className="relative w-full">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-[#869397]" />
          <input
            type="text"
            placeholder="Search engineering roles, stacks (FastAPI, TimescaleDB, Docker), recruiters..."
            className="w-full pl-9 pr-14 py-1.5 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:outline-none focus:border-[#4cd7f6] focus:ring-1 focus:ring-[#4cd7f6] placeholder:text-[#869397]/70 transition-all font-sans"
          />
          <div className="absolute right-2.5 top-2 px-1.5 py-0.5 rounded bg-[#292931] border border-[#3d494c]/40 text-[10px] font-mono text-[#bcc9cd]">
            ⌘K
          </div>
        </div>
      </div>

      {/* Trailing Action Cluster */}
      <div className="flex items-center gap-3">
        <button className="px-3 py-1.5 text-[12px] rounded-lg bg-[#292931]/60 border border-[#3d494c]/40 text-[#bcc9cd] hover:text-[#e3e1ec] hover:bg-[#292931] transition-colors flex items-center gap-1.5 active:scale-[0.98]">
          <StopCircle className="w-3.5 h-3.5 text-[#ffb4ab]" />
          <span>Stop Runner</span>
        </button>

        <button className="px-3.5 py-1.5 text-[12px] font-medium rounded-lg bg-[#4cd7f6] text-[#003640] hover:bg-white transition-all flex items-center gap-1.5 active:scale-[0.98] cyan-glow">
          <Rocket className="w-3.5 h-3.5" />
          <span>Deploy Agent</span>
        </button>

        <div className="h-4 w-px bg-[#3d494c]/40 mx-1"></div>

        {/* Candidate Profile Avatar */}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#06b6d4] to-[#00a572] flex items-center justify-center font-bold text-xs text-[#003640]">
            {candidateName.split(" ").map((n) => n[0]).slice(0, 2).join("") || "MS"}
          </div>
          <span className="text-[12px] text-[#e3e1ec] font-medium hidden sm:inline">
            {candidateName || "Candidate"}
          </span>
        </div>
      </div>
    </header>
  );
}
