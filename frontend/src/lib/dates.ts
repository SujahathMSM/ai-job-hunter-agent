// Formats a posting's date for display. Never invents a date: if the source gave no
// parseable date, the backend's own label (e.g. "Posted within 14d") is shown as-is.
export function formatDatePosted(dateStr?: string): string {
  if (!dateStr) return "Date not given";
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;

  const formattedDate = d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  const diffHours = Math.floor((Date.now() - d.getTime()) / (1000 * 60 * 60));
  const diffDays = Math.floor(diffHours / 24);
  if (diffHours < 1) return `${formattedDate} · Just now`;
  if (diffHours < 24) return `${formattedDate} · ${diffHours}h ago`;
  if (diffDays === 1) return `${formattedDate} · Yesterday`;
  if (diffDays <= 30) return `${formattedDate} · ${diffDays}d ago`;
  return formattedDate;
}
