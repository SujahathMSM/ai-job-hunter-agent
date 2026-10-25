"use client";

import React, { useEffect, useState } from "react";
import { KanbanSquare, ExternalLink, RefreshCw, CheckCircle2 } from "lucide-react";
import { ApplicationItem } from "../../types";
import { fetchApplications, updateAppStatus } from "../../lib/api";

export default function TrackerView() {
  const [apps, setApps] = useState<ApplicationItem[]>([]);
  const [metrics, setMetrics] = useState<any>({});
  const [loading, setLoading] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await fetchApplications();
      setApps(data.applications || []);
      setMetrics(data.metrics || {});
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleStatusChange = async (id: number, newStatus: string) => {
    try {
      await updateAppStatus(id, newStatus);
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex flex-col gap-5 p-6 max-w-7xl mx-auto">
      {/* Metrics Banner */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5">
        <div className="p-4 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border">
          <span className="text-[10px] font-mono uppercase text-[#bcc9cd]">Drafted Applications</span>
          <div className="text-[22px] font-bold text-[#4cd7f6] mt-1">{metrics.Drafted || 0}</div>
        </div>
        <div className="p-4 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border">
          <span className="text-[10px] font-mono uppercase text-[#bcc9cd]">Sent / Dispatched</span>
          <div className="text-[22px] font-bold text-[#4edea3] mt-1">{metrics.Applied || 0}</div>
        </div>
        <div className="p-4 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border">
          <span className="text-[10px] font-mono uppercase text-[#bcc9cd]">Interview Invites</span>
          <div className="text-[22px] font-bold text-[#d0bcff] mt-1">{metrics.Interview || 0}</div>
        </div>
        <div className="p-4 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border">
          <span className="text-[10px] font-mono uppercase text-[#bcc9cd]">Offers Received</span>
          <div className="text-[22px] font-bold text-[#acedff] mt-1">{metrics.Offer || 0}</div>
        </div>
      </div>

      {/* Main Table Container */}
      <div className="p-5 rounded-xl bg-[#0d0e15] border border-[#3d494c]/30 specular-border flex flex-col gap-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#3d494c]/20">
          <div className="flex items-center gap-2">
            <KanbanSquare className="w-5 h-5 text-[#4cd7f6]" />
            <h2 className="text-[16px] font-semibold text-[#e3e1ec]">Tracked Application Pipeline</h2>
          </div>
          <button
            onClick={loadData}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#1a1b22] border border-[#3d494c]/40 text-xs text-[#bcc9cd] hover:text-[#e3e1ec] transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>

        {apps.length === 0 ? (
          <div className="p-12 text-center text-[#bcc9cd] text-sm">
            No applications logged yet. Once you dispatch emails or save drafts, they will appear here.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-sans">
              <thead className="bg-[#1a1b22] text-[#869397] uppercase font-mono text-[10px] border-b border-[#3d494c]/30">
                <tr>
                  <th className="py-2.5 px-3">Company</th>
                  <th className="py-2.5 px-3">Role</th>
                  <th className="py-2.5 px-3">Location</th>
                  <th className="py-2.5 px-3">Contact</th>
                  <th className="py-2.5 px-3">Date</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Update Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#3d494c]/20">
                {apps.map((app) => (
                  <tr key={app.id} className="hover:bg-[#1e1f26]/40 transition-colors">
                    <td className="py-3 px-3 font-semibold text-[#e3e1ec]">{app.company}</td>
                    <td className="py-3 px-3 text-[#bcc9cd]">{app.job_title}</td>
                    <td className="py-3 px-3 text-[#869397]">{app.location}</td>
                    <td className="py-3 px-3 font-mono text-[#4cd7f6]">{app.hr_email || "Portal"}</td>
                    <td className="py-3 px-3 text-[#869397]">{app.date_applied?.slice(0, 10)}</td>
                    <td className="py-3 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-mono font-medium ${
                          app.status === "Applied"
                            ? "bg-[#4edea3]/10 text-[#4edea3] border border-[#4edea3]/30"
                            : app.status === "Interview"
                            ? "bg-[#d0bcff]/10 text-[#d0bcff] border border-[#d0bcff]/30"
                            : "bg-[#4cd7f6]/10 text-[#4cd7f6] border border-[#4cd7f6]/30"
                        }`}
                      >
                        {app.status}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right">
                      <select
                        value={app.status}
                        onChange={(e) => handleStatusChange(app.id, e.target.value)}
                        className="px-2 py-1 bg-[#1a1b22] text-[#e3e1ec] text-xs rounded border border-[#3d494c]/40 focus:outline-none"
                      >
                        <option value="Drafted">Drafted</option>
                        <option value="Applied">Applied</option>
                        <option value="Interview">Interview</option>
                        <option value="Rejected">Rejected</option>
                        <option value="Offer">Offer</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
