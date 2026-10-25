"use client";

import React, { useState, useEffect } from "react";
import {
  Globe,
  ExternalLink,
  Search,
  Plus,
  Building2,
  MapPin,
  Mail,
  UserSearch,
  Sparkles,
  Trash2,
  CheckCircle2,
  AlertCircle,
  X,
  Briefcase,
  Layers,
  Cpu
} from "lucide-react";
import { fetchPortals, addPortal, deletePortal, CareerPortalItem } from "../../lib/api";

interface CareerPortalsViewProps {
  onSelectCompanyForRecruiters?: (companyName: string) => void;
  onSelectCompanyForTailor?: (companyName: string, location: string) => void;
}

export default function CareerPortalsView({
  onSelectCompanyForRecruiters,
  onSelectCompanyForTailor,
}: CareerPortalsViewProps) {
  const [portals, setPortals] = useState<CareerPortalItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedRegion, setSelectedRegion] = useState("ALL");
  const [showAddModal, setShowAddModal] = useState(false);

  // Form state
  const [formName, setFormName] = useState("");
  const [formUrl, setFormUrl] = useState("");
  const [formRegion, setFormRegion] = useState("GULF");
  const [formCountry, setFormCountry] = useState("United Arab Emirates");
  const [formIndustry, setFormIndustry] = useState("Energy, Oil & Gas");
  const [formAtsType, setFormAtsType] = useState("Enterprise Career Portal");
  const [formHrEmail, setFormHrEmail] = useState("");
  const [formNotes, setFormNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const loadPortals = async () => {
    setLoading(true);
    try {
      const data = await fetchPortals(selectedRegion, searchQuery);
      setPortals(data);
    } catch (err) {
      console.error("Error loading portals:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPortals();
  }, [selectedRegion]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadPortals();
  };

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName.trim() || !formUrl.trim()) {
      setFeedback({ type: "error", text: "Company Name and Portal URL are required." });
      return;
    }
    setSubmitting(true);
    setFeedback(null);
    try {
      await addPortal({
        name: formName.trim(),
        portal_url: formUrl.trim(),
        region: formRegion,
        country: formCountry.trim(),
        industry: formIndustry.trim(),
        ats_type: formAtsType.trim(),
        hr_email: formHrEmail.trim(),
        notes: formNotes.trim(),
      });
      setFeedback({ type: "success", text: `Successfully added ${formName} to career portals!` });
      setFormName("");
      setFormUrl("");
      setFormHrEmail("");
      setFormNotes("");
      setShowAddModal(false);
      loadPortals();
    } catch (err: any) {
      setFeedback({ type: "error", text: err.message || "Failed to add portal." });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Remove ${name} from your custom portals?`)) return;
    try {
      await deletePortal(id);
      loadPortals();
    } catch (err) {
      console.error(err);
    }
  };

  const filteredPortals = portals.filter((p) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      p.name.toLowerCase().includes(q) ||
      p.portal_url.toLowerCase().includes(q) ||
      p.industry.toLowerCase().includes(q) ||
      p.country.toLowerCase().includes(q)
    );
  });

  const gulfCount = portals.filter((p) => p.region === "GULF").length;
  const sgCount = portals.filter((p) => p.region === "SINGAPORE").length;
  const ukCount = portals.filter((p) => p.region === "UK_EUROPE").length;
  const globalCount = portals.filter((p) => p.region === "GLOBAL").length;

  return (
    <div className="flex flex-col gap-5 p-6 max-w-7xl mx-auto">
      {/* Top Banner & Control Deck */}
      <div className="p-5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div>
            <h1 className="text-[20px] font-semibold text-[#e3e1ec] tracking-tight flex items-center gap-2">
              <Globe className="w-5 h-5 text-[#4cd7f6]" />
              Enterprise Career Portals &amp; Direct Gateways
            </h1>
            <p className="text-[13px] text-[#bcc9cd] mt-0.5">
              Direct recruitment portals for 50+ Gulf energy conglomerates (ADNOC, Aramco, Masdar, NEOM, ACWA Power), sovereign tech groups, and migratable corridors.
            </p>
          </div>

          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 rounded-lg bg-[#4cd7f6] text-[#003640] font-semibold text-xs hover:bg-white transition-all cyan-glow flex items-center gap-1.5 self-start md:self-auto"
          >
            <Plus className="w-4 h-4" />
            <span>Add Career Portal</span>
          </button>
        </div>

        {/* Search & Region Filters */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-3 pt-3 border-t border-[#3d494c]/20">
          {/* Search Box */}
          <form onSubmit={handleSearchSubmit} className="relative w-full md:w-96">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-[#869296]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter by company, industry, or domain (e.g. adnoc, aramco)..."
              className="w-full pl-9 pr-4 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none"
            />
          </form>

          {/* Region Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto">
            {[
              { id: "ALL", label: `All Portals (${portals.length})` },
              { id: "GULF", label: `Gulf Energy & Mega (${gulfCount})` },
              { id: "SINGAPORE", label: `Singapore (${sgCount})` },
              { id: "UK_EUROPE", label: `UK & Europe (${ukCount})` },
              { id: "GLOBAL", label: `Global / Aus (${globalCount})` },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setSelectedRegion(tab.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all whitespace-nowrap ${
                  selectedRegion === tab.id
                    ? "bg-[#292931] text-[#4cd7f6] border border-[#4cd7f6]/40 font-semibold"
                    : "text-[#bcc9cd] hover:text-[#e3e1ec] hover:bg-[#1a1b22]"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Global Feedback Alert */}
        {feedback && (
          <div
            className={`p-3 rounded-lg flex items-center gap-2 text-xs font-mono ${
              feedback.type === "success"
                ? "bg-[#4edea3]/10 border border-[#4edea3]/30 text-[#4edea3]"
                : "bg-[#93000a]/20 border border-[#93000a]/40 text-[#ffb4ab]"
            }`}
          >
            {feedback.type === "success" ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
            <span>{feedback.text}</span>
          </div>
        )}
      </div>

      {/* Portals Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <div key={n} className="p-5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/20 animate-pulse h-48"></div>
          ))}
        </div>
      ) : filteredPortals.length === 0 ? (
        <div className="p-12 text-center rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 flex flex-col items-center gap-2">
          <Building2 className="w-8 h-8 text-[#869296]" />
          <h3 className="text-sm font-semibold text-[#e3e1ec]">No Career Portals Match Your Filter</h3>
          <p className="text-xs text-[#bcc9cd]">Try clearing your search query or add a custom portal.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredPortals.map((portal) => (
            <div
              key={portal.id}
              className="p-5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 hover:border-[#4cd7f6]/50 transition-all flex flex-col justify-between gap-4 specular-border relative group"
            >
              {/* Card Top: Title & Badges */}
              <div className="flex flex-col gap-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-md bg-[#1a1b22] border border-[#3d494c]/50 flex items-center justify-center text-[#4cd7f6]">
                      <Building2 className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-[#e3e1ec] leading-snug line-clamp-1">{portal.name}</h3>
                      <div className="flex items-center gap-1.5 text-[11px] text-[#bcc9cd] mt-0.5">
                        <MapPin className="w-3 h-3 text-[#4edea3]" />
                        <span>{portal.country}</span>
                      </div>
                    </div>
                  </div>

                  {portal.is_custom === 1 && (
                    <button
                      onClick={() => handleDelete(portal.id, portal.name)}
                      className="text-[#869296] hover:text-[#ffb4ab] p-1 rounded transition-colors"
                      title="Delete Custom Portal"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                {/* Badges */}
                <div className="flex flex-wrap items-center gap-1.5 pt-1">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1a1b22] border border-[#3d494c]/40 text-[#4cd7f6]">
                    {portal.industry}
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1a1b22] border border-[#3d494c]/40 text-[#869296]">
                    {portal.ats_type}
                  </span>
                </div>

                {/* Direct Link Display */}
                <a
                  href={portal.portal_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs font-mono text-[#4cd7f6] hover:underline flex items-center gap-1.5 truncate pt-1"
                >
                  <Globe className="w-3.5 h-3.5 flex-shrink-0" />
                  <span className="truncate">{portal.portal_url.replace(/^https?:\/\//, "")}</span>
                  <ExternalLink className="w-3 h-3 flex-shrink-0 opacity-70" />
                </a>

                {/* Notes */}
                {portal.notes && (
                  <p className="text-[12px] text-[#bcc9cd] line-clamp-2 leading-relaxed pt-1 border-t border-[#3d494c]/20">
                    {portal.notes}
                  </p>
                )}

                {/* HR Email Contact Pattern */}
                {portal.hr_email && (
                  <div className="flex items-center gap-1.5 text-[11px] font-mono text-[#4edea3] bg-[#4edea3]/10 px-2 py-1 rounded border border-[#4edea3]/20">
                    <Mail className="w-3 h-3 flex-shrink-0" />
                    <span className="truncate">{portal.hr_email}</span>
                  </div>
                )}
              </div>

              {/* Card Actions */}
              <div className="grid grid-cols-3 gap-2 pt-3 border-t border-[#3d494c]/20">
                <a
                  href={portal.portal_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="py-1.5 px-2 rounded-lg bg-[#1a1b22] hover:bg-[#292931] border border-[#3d494c]/50 text-[#e3e1ec] text-[11px] font-semibold flex items-center justify-center gap-1 transition-colors"
                >
                  <span>Open Portal</span>
                  <ExternalLink className="w-3 h-3" />
                </a>

                <button
                  onClick={() => onSelectCompanyForRecruiters && onSelectCompanyForRecruiters(portal.name.split(" ")[0])}
                  className="py-1.5 px-2 rounded-lg bg-[#1a1b22] hover:bg-[#292931] border border-[#3d494c]/50 text-[#4cd7f6] text-[11px] font-semibold flex items-center justify-center gap-1 transition-colors"
                  title="Find recruiters at this company"
                >
                  <UserSearch className="w-3 h-3" />
                  <span>Recruiters</span>
                </button>

                <button
                  onClick={() =>
                    onSelectCompanyForTailor &&
                    onSelectCompanyForTailor(portal.name.split(" ")[0], portal.country)
                  }
                  className="py-1.5 px-2 rounded-lg bg-[#1a1b22] hover:bg-[#292931] border border-[#3d494c]/50 text-[#4edea3] text-[11px] font-semibold flex items-center justify-center gap-1 transition-colors"
                  title="Tailor CV for this company"
                >
                  <Sparkles className="w-3 h-3" />
                  <span>Tailor CV</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal: Add Custom Career Portal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg rounded-xl bg-[#0d0e15] border border-[#3d494c]/50 specular-border p-6 flex flex-col gap-4 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-[#3d494c]/30">
              <h2 className="text-base font-semibold text-[#e3e1ec] flex items-center gap-2">
                <Plus className="w-4 h-4 text-[#4cd7f6]" />
                Add Career Portal Bookmark
              </h2>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-[#869296] hover:text-[#e3e1ec] p-1 rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleAddSubmit} className="flex flex-col gap-3">
              <div>
                <label className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1 block">
                  Company / Organization Name *
                </label>
                <input
                  type="text"
                  required
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder="e.g. ADNOC, Emirates, Aramco, GovTech"
                  className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none"
                />
              </div>

              <div>
                <label className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1 block">
                  Portal URL * (e.g. jobs.adnoc.ae/us/en)
                </label>
                <input
                  type="text"
                  required
                  value={formUrl}
                  onChange={(e) => setFormUrl(e.target.value)}
                  placeholder="e.g. jobs.adnoc.ae/us/en or https://..."
                  className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1 block">Target Region</label>
                  <select
                    value={formRegion}
                    onChange={(e) => setFormRegion(e.target.value)}
                    className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none"
                  >
                    <option value="GULF">GULF (UAE/KSA/Qatar)</option>
                    <option value="SINGAPORE">Singapore</option>
                    <option value="UK_EUROPE">UK &amp; Europe</option>
                    <option value="GLOBAL">Global Remote</option>
                  </select>
                </div>

                <div>
                  <label className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1 block">Country</label>
                  <input
                    type="text"
                    value={formCountry}
                    onChange={(e) => setFormCountry(e.target.value)}
                    placeholder="e.g. UAE, Saudi Arabia, Singapore"
                    className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1 block">Industry</label>
                  <input
                    type="text"
                    value={formIndustry}
                    onChange={(e) => setFormIndustry(e.target.value)}
                    placeholder="e.g. Energy, AI, Cloud, Fintech"
                    className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none"
                  />
                </div>

                <div>
                  <label className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1 block">ATS Platform Type</label>
                  <input
                    type="text"
                    value={formAtsType}
                    onChange={(e) => setFormAtsType(e.target.value)}
                    placeholder="e.g. Phenom, Workday, SuccessFactors"
                    className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1 block">
                  HR / Recruitment Email (Optional)
                </label>
                <input
                  type="email"
                  value={formHrEmail}
                  onChange={(e) => setFormHrEmail(e.target.value)}
                  placeholder="e.g. careers@company.com"
                  className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none font-mono"
                />
              </div>

              <div>
                <label className="text-[11px] font-mono uppercase text-[#bcc9cd] mb-1 block">Notes / Intelligence</label>
                <textarea
                  rows={2}
                  value={formNotes}
                  onChange={(e) => setFormNotes(e.target.value)}
                  placeholder="e.g. Direct portal for industrial telemetry and backend software openings."
                  className="w-full px-3 py-2 bg-[#1a1b22] text-[#e3e1ec] text-[13px] rounded-lg border border-[#3d494c]/50 focus:border-[#4cd7f6] focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-[#3d494c]/30">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-lg bg-[#1a1b22] text-[#bcc9cd] text-xs font-semibold hover:bg-[#292931]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-5 py-2 rounded-lg bg-[#4cd7f6] text-[#003640] text-xs font-semibold hover:bg-white cyan-glow disabled:opacity-50"
                >
                  {submitting ? "Saving..." : "Save Portal"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
