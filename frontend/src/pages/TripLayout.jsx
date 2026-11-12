import { NavLink, Outlet, useNavigate, useParams } from "react-router-dom";
import { useFetch } from "../hooks";
import { fdate } from "../format";
import { ErrorBox, Loading, Notice } from "../components/ui";

const tabs = [["", "Fund"], ["contributions", "Contributions"], ["expenses", "Expenses"], ["ai", "AI assistant"], ["statement", "Statement"]];

export default function TripLayout() {
  const { tripId } = useParams();
  const nav = useNavigate();
  const trip = useFetch(`/trips/${tripId}`);
  const all = useFetch("/trips");
  if (trip.loading) return <Loading />;
  if (trip.error) return <ErrorBox error={trip.error} onRetry={trip.reload} />;
  const t = trip.data;
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">{t.name}</h1>
          <div className="text-sm text-slate-500">{t.destination} · {fdate(t.start_date)} – {fdate(t.end_date)} · {t.members.length}/{t.group_size} members · <span className="capitalize">{t.role}</span></div>
        </div>
        <select className="inp w-auto" value={tripId} onChange={(e) => nav(`/app/trips/${e.target.value}`)} aria-label="Switch trip">
          {(all.data || [{ id: tripId, name: t.name }]).map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}
        </select>
      </div>
      {t.status !== "active" && <Notice kind="warn">This trip is {t.status}. Contributions and edits are disabled.</Notice>}
      <nav className="flex gap-1 overflow-x-auto border-b border-slate-200 dark:border-slate-800">
        {tabs.map(([to, label]) => (
          <NavLink key={to} to={to} end={to === ""} className={({ isActive }) => `whitespace-nowrap border-b-2 px-3 py-2 text-sm font-medium ${isActive ? "border-brand-600 text-brand-700 dark:text-brand-500" : "border-transparent text-slate-500"}`}>{label}</NavLink>
        ))}
      </nav>
      <Outlet context={{ trip: t, reload: trip.reload }} />
    </div>
  );
}
