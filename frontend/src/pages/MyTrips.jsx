import { useState } from "react";
import { Link } from "react-router-dom";
import { useFetch } from "../hooks";
import { fdate, money, tripPhase } from "../format";
import { Empty, ErrorBox, Loading, Progress } from "../components/ui";

export default function MyTrips() {
  const { data, error, loading, reload } = useFetch("/trips");
  const [tab, setTab] = useState("active");
  if (loading) return <Loading />;
  if (error) return <ErrorBox error={error} onRetry={reload} />;
  const list = data.filter((t) => tripPhase(t) === tab);
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between"><h1 className="text-2xl font-semibold">My trips</h1><Link className="btn btn-p" to="/app/trips/new">Create trip</Link></div>
      <div className="flex gap-2">{["active", "upcoming", "completed"].map((k) => <button key={k} className={`btn capitalize ${tab === k ? "btn-p" : ""}`} onClick={() => setTab(k)}>{k}</button>)}</div>
      {list.length === 0 ? <Empty title={`No ${tab} trips`} /> : (
        <div className="grid gap-3 md:grid-cols-2">
          {list.map((t) => (
            <Link key={t.id} to={`/app/trips/${t.id}`} className="card block hover:border-brand-500">
              <div className="flex justify-between"><div className="font-semibold">{t.name}</div><span className="text-xs capitalize text-slate-500">{t.role}</span></div>
              <div className="text-sm text-slate-500">{t.destination} · {fdate(t.start_date)} – {fdate(t.end_date)} · {t.member_count}/{t.group_size} members</div>
              <div className="mt-3"><Progress value={t.budget_total ? Math.round((t.verified * 100) / t.budget_total) : 0} label={`${money(t.verified, t.currency)} of ${money(t.budget_total, t.currency)} verified`} /></div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
