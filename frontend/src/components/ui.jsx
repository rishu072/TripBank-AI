import { AlertTriangle, CheckCircle2, Circle, Clock, Loader2, RotateCcw, XCircle, FileText } from "lucide-react";

export function Card({ title, action, children, className = "" }) {
  return (
    <section className={`card ${className}`}>
      {(title || action) && (
        <div className="mb-3 flex items-center justify-between gap-2">
          {title && <h2 className="text-base font-semibold">{title}</h2>}
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

export const Stat = ({ label, value, hint }) => (
  <div className="card">
    <div className="text-xs text-slate-500">{label}</div>
    <div className="mt-1 text-xl font-semibold">{value}</div>
    {hint && <div className="mt-1 text-xs text-slate-500">{hint}</div>}
  </div>
);

export const Progress = ({ value, label }) => (
  <div>
    <div className="h-2.5 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800" role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={100}>
      <div className="h-full bg-brand-600" style={{ width: `${Math.min(100, value)}%` }} />
    </div>
    {label && <div className="mt-1 text-xs text-slate-500">{label}</div>}
  </div>
);

export const Loading = ({ text = "Loading…" }) => (
  <div className="flex items-center gap-2 p-6 text-sm text-slate-500" role="status">
    <Loader2 className="h-4 w-4 animate-spin" /> {text}
  </div>
);

export const Empty = ({ title, hint, children }) => (
  <div className="rounded-xl border border-dashed border-slate-300 p-8 text-center dark:border-slate-700">
    <div className="font-medium">{title}</div>
    {hint && <div className="mt-1 text-sm text-slate-500">{hint}</div>}
    {children && <div className="mt-4 flex justify-center gap-2">{children}</div>}
  </div>
);

export const ErrorBox = ({ error, onRetry }) => {
  if (!error) return null;
  const denied = ["NOT_TRIP_MEMBER", "NOT_ORGANIZER", "NOT_ORDER_OWNER"].includes(error.code);
  return (
    <div className="flex items-start gap-3 rounded-xl border border-red-300 bg-red-50 p-4 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200" role="alert">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
      <div className="flex-1">
        <div className="font-medium">{denied ? "Permission denied" : error.code === "NETWORK_ERROR" ? "Network error" : "Something went wrong"}</div>
        <div>{error.message}</div>
        <div className="mt-1 text-xs opacity-70">Code: {error.code}</div>
      </div>
      {onRetry && (
        <button className="btn" onClick={onRetry}>
          <RotateCcw className="h-3.5 w-3.5" /> Retry
        </button>
      )}
    </div>
  );
};

export const Notice = ({ kind = "info", children }) => {
  const tone = { info: "border-sky-300 bg-sky-50 text-sky-900 dark:border-sky-900 dark:bg-sky-950 dark:text-sky-200", ok: "border-green-300 bg-green-50 text-green-900 dark:border-green-900 dark:bg-green-950 dark:text-green-200", warn: "border-amber-300 bg-amber-50 text-amber-900 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200" }[kind];
  return <div className={`rounded-lg border p-3 text-sm ${tone}`} role="status">{children}</div>;
};

const BADGES = {
  Paid: [CheckCircle2, "text-green-700 dark:text-green-400"],
  Verified: [CheckCircle2, "text-green-700 dark:text-green-400"],
  Approved: [CheckCircle2, "text-green-700 dark:text-green-400"],
  Partial: [Clock, "text-amber-700 dark:text-amber-400"],
  Processing: [Clock, "text-amber-700 dark:text-amber-400"],
  Draft: [FileText, "text-amber-700 dark:text-amber-400"],
  Pending: [Circle, "text-slate-500"],
  Failed: [XCircle, "text-red-700 dark:text-red-400"],
  Refunded: [RotateCcw, "text-slate-600 dark:text-slate-300"],
};

export function StatusBadge({ status }) {
  const label = status ? status[0].toUpperCase() + status.slice(1) : "Pending";
  const [Icon, tone] = BADGES[label] || BADGES.Pending;
  return (
    <span className={`inline-flex items-center gap-1 text-sm font-medium ${tone}`}>
      <Icon className="h-4 w-4" /> {label}
    </span>
  );
}

export const Field = ({ label, error, children }) => (
  <label className="block">
    <span className="lbl">{label}</span>
    {children}
    {error && <span className="mt-1 block text-xs text-red-600">{error}</span>}
  </label>
);

export const Table = ({ head, children }) => (
  <div className="overflow-x-auto">
    <table className="w-full">
      <thead className="border-b border-slate-200 dark:border-slate-800">
        <tr>{head.map((h) => <th key={h} className="th">{h}</th>)}</tr>
      </thead>
      <tbody className="divide-y divide-slate-100 dark:divide-slate-800">{children}</tbody>
    </table>
  </div>
);
