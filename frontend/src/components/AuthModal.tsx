"use client";

import React, { useState, useEffect } from "react";
import { X, User, Lock, Mail, Users, Check, ArrowRight, UserPlus, LogIn, AlertCircle } from "lucide-react";
import { AuthUser, getStoredUser, setSession } from "../lib/auth";
import { loginUser, registerUser, fetchUsersList, switchCandidate } from "../lib/api";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUserChanged: (user: AuthUser) => void;
}

export default function AuthModal({ isOpen, onClose, onUserChanged }: AuthModalProps) {
  const [activeTab, setActiveTab] = useState<"switch" | "login" | "register">("switch");
  const [currentUser, setCurrentUser] = useState<AuthUser>(getStoredUser());
  const [usersList, setUsersList] = useState<AuthUser[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");

  useEffect(() => {
    if (isOpen) {
      setCurrentUser(getStoredUser());
      loadUsers();
      setError(null);
    }
  }, [isOpen]);

  const loadUsers = async () => {
    try {
      const res = await fetchUsersList();
      setUsersList(res.users || []);
    } catch (e: any) {
      console.error("Failed to load users:", e);
    }
  };

  if (!isOpen) return null;

  const handleSwitchUser = async (targetUserId: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await switchCandidate(targetUserId);
      setSession(res.user, res.token);
      setCurrentUser(res.user);
      onUserChanged(res.user);
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to switch candidate.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError("Please enter both email and password.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await loginUser(email, password);
      setSession(res.user, res.token);
      setCurrentUser(res.user);
      onUserChanged(res.user);
      onClose();
    } catch (err: any) {
      setError(err.message || "Invalid credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName || !email || !password) {
      setError("Please fill in all registration fields.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await registerUser(email, password, fullName);
      setSession(res.user, res.token);
      setCurrentUser(res.user);
      onUserChanged(res.user);
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to create candidate account.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
      <div
        className="relative w-full max-w-lg rounded-2xl bg-[#0d0e15] border border-[#3d494c]/40 shadow-2xl overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#3d494c]/30 bg-[#14151f]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#06b6d4] to-[#00a572] flex items-center justify-center text-[#003640] font-bold text-xs shadow-md">
              <User className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-[16px] font-semibold text-[#e3e1ec]">Candidate Session &amp; Accounts</h2>
              <p className="text-[11px] text-[#869397]">Multi-tenant profile switcher and secure sign-in</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[#869397] hover:text-[#e3e1ec] hover:bg-[#292931]/60 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="flex border-b border-[#3d494c]/20 bg-[#11121b] px-6 pt-2">
          <button
            onClick={() => { setActiveTab("switch"); setError(null); }}
            className={`pb-2.5 px-3 text-xs font-medium border-b-2 transition-all flex items-center gap-1.5 ${
              activeTab === "switch"
                ? "border-[#4cd7f6] text-[#4cd7f6]"
                : "border-transparent text-[#869397] hover:text-[#bcc9cd]"
            }`}
          >
            <Users className="w-3.5 h-3.5" />
            <span>Switch Profile ({usersList.length})</span>
          </button>
          <button
            onClick={() => { setActiveTab("login"); setError(null); }}
            className={`pb-2.5 px-3 text-xs font-medium border-b-2 transition-all flex items-center gap-1.5 ${
              activeTab === "login"
                ? "border-[#4cd7f6] text-[#4cd7f6]"
                : "border-transparent text-[#869397] hover:text-[#bcc9cd]"
            }`}
          >
            <LogIn className="w-3.5 h-3.5" />
            <span>Sign In</span>
          </button>
          <button
            onClick={() => { setActiveTab("register"); setError(null); }}
            className={`pb-2.5 px-3 text-xs font-medium border-b-2 transition-all flex items-center gap-1.5 ${
              activeTab === "register"
                ? "border-[#4cd7f6] text-[#4cd7f6]"
                : "border-transparent text-[#869397] hover:text-[#bcc9cd]"
            }`}
          >
            <UserPlus className="w-3.5 h-3.5" />
            <span>New Candidate</span>
          </button>
        </div>

        {/* Error notification */}
        {error && (
          <div className="mx-6 mt-4 p-3 rounded-lg bg-[#93000a]/30 border border-[#ffb4ab]/40 text-[#ffb4ab] text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Content Body */}
        <div className="p-6">
          {/* TAB 1: QUICK SWITCH CANDIDATE PROFILE */}
          {activeTab === "switch" && (
            <div className="flex flex-col gap-3">
              <p className="text-xs text-[#bcc9cd] mb-1">
                Select an active candidate account. Applications, Europass CVs, and SMTP credentials remain completely isolated per candidate:
              </p>

              <div className="flex flex-col gap-2 max-h-64 overflow-y-auto pr-1">
                {usersList.map((u) => {
                  const isActive = u.id === currentUser.id;
                  return (
                    <div
                      key={u.id}
                      onClick={() => !isActive && handleSwitchUser(u.id)}
                      className={`p-3 rounded-xl border flex items-center justify-between transition-all cursor-pointer ${
                        isActive
                          ? "bg-[#4cd7f6]/10 border-[#4cd7f6]/60 shadow-sm"
                          : "bg-[#14151f] border-[#3d494c]/30 hover:border-[#4cd7f6]/40 hover:bg-[#1a1b26]"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-9 h-9 rounded-lg flex items-center justify-center font-bold text-xs ${
                            isActive
                              ? "bg-[#4cd7f6] text-[#003640]"
                              : "bg-[#292931] text-[#bcc9cd]"
                          }`}
                        >
                          {u.full_name.split(" ").map((n) => n[0]).slice(0, 2).join("") || "C"}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold text-[#e3e1ec]">{u.full_name}</span>
                            {u.id === "default" && (
                              <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-[#4edea3]/20 text-[#4edea3] border border-[#4edea3]/30">
                                Primary Master
                              </span>
                            )}
                          </div>
                          <span className="text-[11px] text-[#869397] font-mono">{u.email}</span>
                        </div>
                      </div>

                      {isActive ? (
                        <span className="flex items-center gap-1 text-[11px] text-[#4cd7f6] font-mono font-medium">
                          <Check className="w-3.5 h-3.5" /> Active
                        </span>
                      ) : (
                        <button
                          disabled={loading}
                          className="px-2.5 py-1 text-[11px] rounded bg-[#292931] text-[#bcc9cd] hover:text-white hover:bg-[#4cd7f6] hover:text-[#003640] transition-colors flex items-center gap-1"
                        >
                          <span>Switch</span>
                          <ArrowRight className="w-3 h-3" />
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>

              <div className="pt-3 border-t border-[#3d494c]/20 flex justify-between items-center text-xs">
                <span className="text-[#869397]">Need another test candidate?</span>
                <button
                  onClick={() => { setActiveTab("register"); setError(null); }}
                  className="text-[#4cd7f6] hover:underline flex items-center gap-1 text-xs"
                >
                  <UserPlus className="w-3.5 h-3.5" />
                  <span>Register candidate</span>
                </button>
              </div>
            </div>
          )}

          {/* TAB 2: SIGN IN */}
          {activeTab === "login" && (
            <form onSubmit={handleLogin} className="flex flex-col gap-4">
              <div>
                <label className="text-xs font-mono uppercase text-[#bcc9cd] block mb-1.5">Candidate Email</label>
                <div className="relative">
                  <Mail className="w-4 h-4 absolute left-3 top-2.5 text-[#869397]" />
                  <input
                    type="email"
                    required
                    placeholder="candidate@gmail.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-xs rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-mono uppercase text-[#bcc9cd] block mb-1.5">Password</label>
                <div className="relative">
                  <Lock className="w-4 h-4 absolute left-3 top-2.5 text-[#869397]" />
                  <input
                    type="password"
                    required
                    placeholder="••••••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-xs rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none font-mono"
                  />
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 rounded-lg bg-[#4cd7f6] text-[#003640] font-semibold text-xs hover:bg-white transition-all flex items-center justify-center gap-1.5 cyan-glow"
                >
                  <LogIn className="w-3.5 h-3.5" />
                  <span>{loading ? "Authenticating..." : "Sign In & Load Profile"}</span>
                </button>
              </div>
            </form>
          )}

          {/* TAB 3: REGISTER NEW CANDIDATE */}
          {activeTab === "register" && (
            <form onSubmit={handleRegister} className="flex flex-col gap-3.5">
              <div>
                <label className="text-xs font-mono uppercase text-[#bcc9cd] block mb-1">Full Candidate Name</label>
                <div className="relative">
                  <User className="w-4 h-4 absolute left-3 top-2.5 text-[#869397]" />
                  <input
                    type="text"
                    required
                    placeholder="e.g. Alex Rivera"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-xs rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-mono uppercase text-[#bcc9cd] block mb-1">Email Address</label>
                <div className="relative">
                  <Mail className="w-4 h-4 absolute left-3 top-2.5 text-[#869397]" />
                  <input
                    type="email"
                    required
                    placeholder="alex.rivera@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-xs rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-mono uppercase text-[#bcc9cd] block mb-1">Account Password</label>
                <div className="relative">
                  <Lock className="w-4 h-4 absolute left-3 top-2.5 text-[#869397]" />
                  <input
                    type="password"
                    required
                    placeholder="At least 6 characters"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-xs rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none font-mono"
                  />
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 rounded-lg bg-[#4edea3] text-[#003822] font-semibold text-xs hover:bg-white transition-all flex items-center justify-center gap-1.5 shadow-md hover:shadow-lg"
                >
                  <UserPlus className="w-3.5 h-3.5" />
                  <span>{loading ? "Creating Candidate Profile..." : "Register & Start Intake"}</span>
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
