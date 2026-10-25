"use client";

import React, { useEffect, useState } from "react";
import { Settings, Save, CheckCircle2 } from "lucide-react";
import { fetchSettings, saveSettings } from "../../lib/api";

export default function SettingsView() {
  const [settings, setSettings] = useState<any>({});
  const [geminiKey, setGeminiKey] = useState("");
  const [openaiKey, setOpenaiKey] = useState("");
  const [anthropicKey, setAnthropicKey] = useState("");
  const [hunterKey, setHunterKey] = useState("");
  const [apolloKey, setApolloKey] = useState("");
  const [smtpUser, setSmtpUser] = useState("");
  const [smtpPass, setSmtpPass] = useState("");
  const [provider, setProvider] = useState("gemini");
  const [safeMode, setSafeMode] = useState("True");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetchSettings().then((data) => {
      setSettings(data);
      setProvider(data.llm_provider || "gemini");
      setSafeMode(String(data.safe_mode) || "True");
      setSmtpUser(data.smtp_user || "");
    });
  }, []);

  const handleSave = async () => {
    const payload: Record<string, string> = {
      LLM_PROVIDER: provider,
      SAFE_MODE: safeMode,
      SMTP_USER: smtpUser,
    };
    if (geminiKey) payload["GEMINI_API_KEY"] = geminiKey;
    if (openaiKey) payload["OPENAI_API_KEY"] = openaiKey;
    if (anthropicKey) payload["ANTHROPIC_API_KEY"] = anthropicKey;
    if (hunterKey) payload["HUNTER_API_KEY"] = hunterKey;
    if (apolloKey) payload["APOLLO_API_KEY"] = apolloKey;
    if (smtpPass) payload["SMTP_PASSWORD"] = smtpPass;

    await saveSettings(payload);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="flex flex-col gap-5 p-6 max-w-4xl mx-auto">
      <div className="p-5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#3d494c]/20">
          <div className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-[#4cd7f6]" />
            <h1 className="text-[18px] font-semibold text-[#e3e1ec]">Engine &amp; API Configuration</h1>
          </div>
          {saved && (
            <span className="flex items-center gap-1 text-xs text-[#4edea3] font-mono">
              <CheckCircle2 className="w-3.5 h-3.5" /> Saved!
            </span>
          )}
        </div>

        {/* LLM Provider */}
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
          <h3 className="text-xs font-mono uppercase text-[#869397]">API Credentials</h3>

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

        {/* SMTP Configuration */}
        <div className="pt-2 border-t border-[#3d494c]/20 flex flex-col gap-3">
          <h3 className="text-xs font-mono uppercase text-[#869397]">SMTP Email Dispatch Setup</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            <div>
              <label className="text-[#bcc9cd] block mb-1">Gmail / SMTP Username</label>
              <input
                type="email"
                placeholder="your.email@gmail.com"
                value={smtpUser}
                onChange={(e) => setSmtpUser(e.target.value)}
                className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none font-mono"
              />
            </div>

            <div>
              <label className="text-[#bcc9cd] block mb-1">Google App Password (16 characters)</label>
              <input
                type="password"
                placeholder="xxxx xxxx xxxx xxxx"
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
