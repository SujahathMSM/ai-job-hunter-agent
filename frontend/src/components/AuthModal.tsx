"use client";

import React, { useState, useEffect } from "react";
import { X, User, Lock, Mail, Users, Check, ArrowRight, UserPlus, LogIn, AlertCircle, Sparkles } from "lucide-react";
import { AuthUser, getStoredUser, setSession } from "../lib/auth";
import { loginUser, registerUser, fetchUsersList, switchCandidate, googleAuth, fetchGoogleConfig } from "../lib/api";

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
  const [googleClientId, setGoogleClientId] = useState<string>("");

  // Form states
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");

  // Google Sign-In prompt modal state
  const [showGooglePrompt, setShowGooglePrompt] = useState(false);
  const [googleEmail, setGoogleEmail] = useState("");
  const [googleName, setGoogleName] = useState("");

  useEffect(() => {
    if (isOpen) {
      setCurrentUser(getStoredUser());
      loadUsers();
      setError(null);
      fetchGoogleConfig()
        .then((cfg) => {
          if (cfg.google_client_id) {
            setGoogleClientId(cfg.google_client_id);
          }
        })
        .catch(() => {});
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

  const handleGoogleSubmit = async (customEmail?: string, customName?: string) => {
    const targetEmail = (customEmail || googleEmail || "").trim();
    const targetName = (customName || googleName || "").trim();

    if (!targetEmail || !targetEmail.includes("@")) {
      setError("Please provide a valid Google account email.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      // Send demo/OAuth token with candidate email & name
      const tokenPayload = `demo_google_${targetEmail}:${targetName || targetEmail.split("@")[0]}`;
      const res = await googleAuth(tokenPayload, googleClientId || undefined);
      setSession(res.user, res.token);
      setCurrentUser(res.user);
      onUserChanged(res.user);
      setShowGooglePrompt(false);
      onClose();
    } catch (err: any) {
      setError(err.message || "Google authentication failed.");
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
              <p className="text-[11px] text-[#869397]">Multi-tenant profile switcher, Google OAuth &amp; secure login</p>
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
            onClick={() => { setActiveTab("switch"); setError(null); setShowGooglePrompt(false); }}
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
            onClick={() => { setActiveTab("login"); setError(null); setShowGooglePrompt(false); }}
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
            onClick={() => { setActiveTab("register"); setError(null); setShowGooglePrompt(false); }}
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
            <div className="flex flex-col gap-4">
              {/* GOOGLE SIGN IN BUTTON */}
              <button
                type="button"
                disabled={loading}
                onClick={() => setShowGooglePrompt(true)}
                className="w-full py-2.5 px-4 rounded-xl bg-[#1a1b22] hover:bg-[#252733] border border-[#3d494c]/50 hover:border-[#4cd7f6]/60 text-[#e3e1ec] font-medium text-xs flex items-center justify-center transition-all shadow-sm active:scale-[0.98]"
              >
                <svg className="w-4 h-4 mr-2.5" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                  />
                </svg>
                <span>Continue with Google</span>
              </button>

              <div className="flex items-center my-0.5">
                <div className="flex-1 border-t border-[#3d494c]/30"></div>
                <span className="px-3 text-[10px] font-mono uppercase text-[#869397]">Or with email &amp; password</span>
                <div className="flex-1 border-t border-[#3d494c]/30"></div>
              </div>

              <form onSubmit={handleLogin} className="flex flex-col gap-3.5">
                <div>
                  <label className="text-xs font-mono uppercase text-[#bcc9cd] block mb-1">Candidate Email</label>
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
                  <label className="text-xs font-mono uppercase text-[#bcc9cd] block mb-1">Password</label>
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

                <div className="pt-1">
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
            </div>
          )}

          {/* TAB 3: REGISTER NEW CANDIDATE */}
          {activeTab === "register" && (
            <div className="flex flex-col gap-4">
              {/* GOOGLE SIGN UP BUTTON */}
              <button
                type="button"
                disabled={loading}
                onClick={() => setShowGooglePrompt(true)}
                className="w-full py-2.5 px-4 rounded-xl bg-[#1a1b22] hover:bg-[#252733] border border-[#3d494c]/50 hover:border-[#4edea3]/60 text-[#e3e1ec] font-medium text-xs flex items-center justify-center transition-all shadow-sm active:scale-[0.98]"
              >
                <svg className="w-4 h-4 mr-2.5" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                  />
                </svg>
                <span>Sign up with Google (1-Click)</span>
              </button>

              <div className="flex items-center my-0.5">
                <div className="flex-1 border-t border-[#3d494c]/30"></div>
                <span className="px-3 text-[10px] font-mono uppercase text-[#869397]">Or register manually</span>
                <div className="flex-1 border-t border-[#3d494c]/30"></div>
              </div>

              <form onSubmit={handleRegister} className="flex flex-col gap-3">
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

                <div className="pt-1">
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
            </div>
          )}
        </div>

        {/* GOOGLE ONE-CLICK ACCOUNT PICKER MODAL OVERLAY */}
        {showGooglePrompt && (
          <div className="absolute inset-0 bg-[#0d0e15]/95 backdrop-blur-md z-20 flex flex-col p-6 animate-fadeIn justify-between">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-[#3d494c]/30">
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5" viewBox="0 0 24 24">
                    <path
                      fill="#4285F4"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="#34A853"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="#FBBC05"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                    />
                    <path
                      fill="#EA4335"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                    />
                  </svg>
                  <h3 className="text-sm font-semibold text-[#e3e1ec]">Sign in with Google</h3>
                </div>
                <button
                  onClick={() => setShowGooglePrompt(false)}
                  className="p-1 rounded-lg text-[#869397] hover:text-[#e3e1ec]"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <p className="text-xs text-[#bcc9cd] mt-3">
                Choose a Google account or enter your Gmail to authenticate and link your private candidate persona:
              </p>

              {/* Fast 1-Click candidate options */}
              <div className="flex flex-col gap-2 mt-4">
                <button
                  type="button"
                  onClick={() => handleGoogleSubmit("sujahathmhmd@gmail.com", "M.S. Mohamed Sujahath")}
                  className="p-3 rounded-xl bg-[#14151f] hover:bg-[#1f212f] border border-[#3d494c]/40 hover:border-[#4cd7f6] flex items-center justify-between text-left transition-all"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-[#4cd7f6] text-[#003640] font-bold text-xs flex items-center justify-center">
                      MS
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-[#e3e1ec]">M.S. Mohamed Sujahath</p>
                      <p className="text-[11px] text-[#869397] font-mono">sujahathmhmd@gmail.com</p>
                    </div>
                  </div>
                  <span className="text-[10px] text-[#4edea3] font-mono px-2 py-0.5 rounded bg-[#4edea3]/10 border border-[#4edea3]/30">
                    Verified
                  </span>
                </button>
              </div>

              {/* Custom Google Account Entry */}
              <div className="mt-4 pt-3 border-t border-[#3d494c]/20 flex flex-col gap-2.5">
                <label className="text-[11px] font-mono uppercase text-[#bcc9cd]">Or use another Google account</label>
                <input
                  type="email"
                  placeholder="name@gmail.com"
                  value={googleEmail}
                  onChange={(e) => setGoogleEmail(e.target.value)}
                  className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-xs rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none font-mono"
                />
                <input
                  type="text"
                  placeholder="Candidate Full Name (optional)"
                  value={googleName}
                  onChange={(e) => setGoogleName(e.target.value)}
                  className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-xs rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none"
                />
              </div>
            </div>

            <div className="flex gap-2 pt-4 border-t border-[#3d494c]/20">
              <button
                type="button"
                onClick={() => setShowGooglePrompt(false)}
                className="w-1/3 py-2 rounded-lg bg-[#292931] text-[#bcc9cd] text-xs font-medium hover:text-white"
              >
                Back
              </button>
              <button
                type="button"
                disabled={loading}
                onClick={() => handleGoogleSubmit()}
                className="w-2/3 py-2 rounded-lg bg-[#4cd7f6] text-[#003640] text-xs font-semibold hover:bg-white flex items-center justify-center gap-1.5 transition-all"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>{loading ? "Authenticating..." : "Continue with Google"}</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
