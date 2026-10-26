"use client";

import React, { useEffect, useState } from "react";
import { Settings, Save, CheckCircle2, Shield, Mail, Key } from "lucide-react";
import { fetchSettings, saveSettings, fetchUserSettings, saveUserSettings, UserSettings } from "../../lib/api";

export default function SettingsView() {
  const [settings, setSettings] = useState<any>({});
  const [geminiKey, setGeminiKey] = useState("");
  const [openaiKey, setOpenaiKey] = useState("");
  const [anthropicKey, setAnthropicKey] = useState("");
  const [hunterKey, setHunterKey] = useState("");
  const [apolloKey, setApolloKey] = useState("");
  const [provider, setProvider] = useState("gemini");
  const [safeMode, setSafeMode] = useState("True");

  // Multi-tenant private SMTP state
  const [senderName, setSenderName] = useState("");
  const [smtpHost, setSmtpHost] = useState("smtp.gmail.com");
  const [smtpPort, setSmtpPort] = useState(587);
  const [smtpUser, setSmtpUser] = useState("");
  const [smtpPass, setSmtpPass] = useState("");
  const [hasStoredPassword, setHasStoredPassword] = useState(false);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchSettings().catch(() => ({} as any)),
      fetchUserSettings("default").catch(() => ({} as Partial<UserSettings>))
    ]).then(([sysData, userData]) => {
      setSettings(sysData);
      setProvider(sysData.llm_provider || "gemini");
      setSafeMode(String(sysData.safe_mode) || "True");

      if (userData) {
        setSenderName(userData.sender_name || sysData.sender_name || "M.S. Mohamed Sujahath");
        setSmtpHost(userData.smtp_host || sysData.smtp_host || "smtp.gmail.com");
        setSmtpPort(userData.smtp_port || 587);
        setSmtpUser(userData.smtp_user || sysData.smtp_user || "");
        setHasStoredPassword(Boolean(userData.has_password));
      }
      setLoading(false);
    });
  }, []);

  const handleSave = async () => {
    // 1. Save System Keys / LLM Engine
    const payload: Record<string, string> = {
      LLM_PROVIDER: provider,
      SAFE_MODE: safeMode,
    };
    if (geminiKey) payload["GEMINI_API_KEY"] = geminiKey;
    if (openaiKey) payload["OPENAI_API_KEY"] = openaiKey;
    if (anthropicKey) payload["ANTHROPIC_API_KEY"] = anthropicKey;
    if (hunterKey) payload["HUNTER_API_KEY"] = hunterKey;
    if (apolloKey) payload["APOLLO_API_KEY"] = apolloKey;

    await saveSettings(payload);

    // 2. Save User-Isolated Private SMTP Credentials to SQLite
    await saveUserSettings({
      user_id: "default",
      smtp_host: smtpHost,
      smtp_port: smtpPort,
      smtp_user: smtpUser,
      smtp_password: smtpPass,
      sender_name: senderName,
    });

    if (smtpPass) {
      setHasStoredPassword(true);
      setSmtpPass("");
    }
    setSaved(true);
    setTimeout(() => setSaved(false), 3500);
  };

  return (
    <div className="flex flex-col gap-5 p-6 max-w-4xl mx-auto">
      <div className="p-5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#3d494c]/20">
          <div className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-[#4cd7f6]" />
            <div>
              <h1 className="text-[18px] font-semibold text-[#e3e1ec]">Engine &amp; User Configuration</h1>
              <p className="text-[11px] text-[#869397]">Production-ready multi-tenant settings with encrypted credentials</p>
            </div>
          </div>
          {saved && (
            <span className="flex items-center gap-1 text-xs text-[#4edea3] font-mono bg-[#4edea3]/10 px-2.5 py-1 rounded-md border border-[#4edea3]/30">
              <CheckCircle2 className="w-3.5 h-3.5" /> Saved to Multi-Tenant DB!
            </span>
          )}
        </div>

        {/* LLM Provider & Safe Mode */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-mono uppercase text-[#bcc9cd] block mb-1">Primary LLM Provider</label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-xs rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none"
            >
              <option value="gemini">Google Gemini 2.5 Flash (Recommended - Native)</option>
              <option value="openai">OpenAI GPT-4o</option>
              <option value="claude">Anthropic Claude 3.5 Sonnet</option>
              <option value="local">Local DeepSeek / Ollama</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-mono uppercase text-[#bcc9cd] block mb-1">Outreach Safety Gate</label>
            <select
              value={safeMode}
              onChange={(e) => setSafeMode(e.target.value)}
              className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-xs rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none"
            >
              <option value="True">Safe Mode: Review &amp; Draft Only</option>
              <option value="False">Live Dispatch: Send Email Directly</option>
            </select>
          </div>
        </div>

        {/* API Keys */}
        <div className="pt-2 border-t border-[#3d494c]/20 flex flex-col gap-3">
          <div className="flex items-center gap-1.5">
            <Key className="w-4 h-4 text-[#4cd7f6]" />
            <h3 className="text-xs font-mono uppercase text-[#869397]">API Credentials</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            <div>
              <label className="text-[#bcc9cd] block mb-1">Google Gemini API Key</label>
              <input
                type="password"
                placeholder="AIzaSy..."
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
                className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none font-mono"
              />
            </div>

            <div>
              <label className="text-[#bcc9cd] block mb-1">OpenAI API Key (Optional)</label>
              <input
                type="password"
                placeholder="sk-proj-..."
                value={openaiKey}
                onChange={(e) => setOpenaiKey(e.target.value)}
                className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none font-mono"
              />
            </div>

            <div>
              <label className="text-[#bcc9cd] block mb-1">Hunter.io Free API Key</label>
              <input
                type="password"
                placeholder="Verified Recruiter Discovery Key"
                value={hunterKey}
                onChange={(e) => setHunterKey(e.target.value)}
                className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none font-mono"
              />
            </div>

            <div>
              <label className="text-[#bcc9cd] block mb-1">Apollo.io API Key (Optional)</label>
              <input
                type="password"
                placeholder="Apollo Global Contact Key"
                value={apolloKey}
                onChange={(e) => setApolloKey(e.target.value)}
                className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none font-mono"
              />
            </div>
          </div>
        </div>

        {/* Multi-Tenant Private SMTP Configuration */}
        <div className="pt-2 border-t border-[#3d494c]/20 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <Mail className="w-4 h-4 text-[#4cd7f6]" />
              <h3 className="text-xs font-mono uppercase text-[#869397]">Candidate SMTP Dispatch Configuration</h3>
            </div>
            <span className="text-[10px] text-[#4edea3] font-mono flex items-center gap-1">
              <Shield className="w-3 h-3" /> Isolated Per User
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            <div>
              <label className="text-[#bcc9cd] block mb-1">Sender Display Name</label>
              <input
                type="text"
                placeholder="M.S. Mohamed Sujahath"
                value={senderName}
                onChange={(e) => setSenderName(e.target.value)}
                className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none"
              />
            </div>

            <div>
              <label className="text-[#bcc9cd] block mb-1">SMTP Username / Email</label>
              <input
                type="email"
                placeholder="your.email@gmail.com"
                value={smtpUser}
                onChange={(e) => setSmtpUser(e.target.value)}
                className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none font-mono"
              />
            </div>

            <div>
              <label className="text-[#bcc9cd] block mb-1">SMTP Server Host</label>
              <input
                type="text"
                placeholder="smtp.gmail.com"
                value={smtpHost}
                onChange={(e) => setSmtpHost(e.target.value)}
                className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none font-mono"
              />
            </div>

            <div>
              <label className="text-[#bcc9cd] block mb-1">
                SMTP App Password {hasStoredPassword && <span className="text-[#4edea3] text-[10px] ml-1 font-mono">(✓ Stored securely)</span>}
              </label>
              <input
                type="password"
                placeholder={hasStoredPassword ? "•••••••••••••••• (Leave blank to keep current)" : "xxxx xxxx xxxx xxxx"}
                value={smtpPass}
                onChange={(e) => setSmtpPass(e.target.value)}
                className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none font-mono"
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end pt-3">
          <button
            onClick={handleSave}
            className="px-5 py-2 rounded-lg bg-[#4cd7f6] text-[#003640] font-semibold text-xs hover:bg-white transition-all flex items-center gap-1.5 cyan-glow"
          >
            <Save className="w-3.5 h-3.5" />
            <span>Save Configuration</span>
          </button>
        </div>
      </div>
    </div>
  );
}
