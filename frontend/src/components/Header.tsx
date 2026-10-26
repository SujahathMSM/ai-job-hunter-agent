"use client";

import React, { useState, useRef, useEffect } from "react";
import { Search, StopCircle, Rocket, Users, ChevronDown, LogOut, LogIn, UserCheck } from "lucide-react";
import { AuthUser } from "../lib/auth";

interface HeaderProps {
  onSearch?: (term: string) => void;
  candidateName: string;
  currentUser: AuthUser | null;
  onOpenAuth?: () => void;
  onLogout?: () => void;
}

export default function Header({ candidateName, currentUser, onOpenAuth, onLogout }: HeaderProps) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

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

        {/* Candidate Profile Avatar & Account Menu */}
        {currentUser ? (
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-[#14151f] border border-[#3d494c]/40 hover:border-[#4cd7f6]/60 hover:bg-[#1a1b26] transition-all group"
              title="Account options & switcher"
            >
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#06b6d4] to-[#00a572] flex items-center justify-center font-bold text-xs text-[#003640] shadow-sm">
                {candidateName.split(" ").map((n) => n[0]).slice(0, 2).join("") || "MS"}
              </div>
              <div className="flex flex-col text-left">
                <span className="text-[12px] text-[#e3e1ec] font-medium group-hover:text-[#4cd7f6] transition-colors line-clamp-1 max-w-[130px]">
                  {candidateName || "Candidate"}
                </span>
                <span className="text-[9px] text-[#4edea3] font-mono flex items-center gap-1">
                  <UserCheck className="w-2.5 h-2.5" /> Active
                </span>
              </div>
              <ChevronDown className={`w-3.5 h-3.5 text-[#869397] group-hover:text-[#4cd7f6] transition-transform ${dropdownOpen ? "rotate-180" : ""}`} />
            </button>

            {dropdownOpen && (
              <div className="absolute right-0 mt-2 w-56 rounded-xl bg-[#0d0e15] border border-[#3d494c]/50 shadow-2xl overflow-hidden py-1.5 z-50 animate-fadeIn">
                <div className="px-3.5 py-2 border-b border-[#3d494c]/30">
                  <p className="text-xs font-semibold text-[#e3e1ec] truncate">{currentUser.full_name}</p>
                  <p className="text-[11px] text-[#869397] font-mono truncate">{currentUser.email}</p>
                </div>

                <div className="py-1">
                  <button
                    onClick={() => {
                      setDropdownOpen(false);
                      onOpenAuth?.();
                    }}
                    className="w-full px-3.5 py-2 text-left text-xs text-[#e3e1ec] hover:bg-[#1f212f] hover:text-[#4cd7f6] flex items-center gap-2 transition-colors"
                  >
                    <Users className="w-3.5 h-3.5 text-[#4cd7f6]" />
                    <span>Switch Candidate Account</span>
                  </button>

                  <button
                    onClick={() => {
                      setDropdownOpen(false);
                      onLogout?.();
                    }}
                    className="w-full px-3.5 py-2 text-left text-xs text-[#ffb4ab] hover:bg-[#93000a]/20 flex items-center gap-2 transition-colors border-t border-[#3d494c]/20"
                  >
                    <LogOut className="w-3.5 h-3.5 text-[#ffb4ab]" />
                    <span>Log Out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <button
            onClick={onOpenAuth}
            className="px-3 py-1.5 rounded-xl bg-[#4cd7f6]/10 border border-[#4cd7f6]/40 hover:bg-[#4cd7f6] hover:text-[#003640] text-[#4cd7f6] font-medium text-xs flex items-center gap-1.5 transition-all shadow-sm"
          >
            <LogIn className="w-3.5 h-3.5" />
            <span>Sign In / Register</span>
          </button>
        )}
      </div>
    </header>
  );
}
