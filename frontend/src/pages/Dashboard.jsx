import { Link } from "react-router-dom";
import { useAuth } from "../auth";
import { useFetch } from "../hooks";
import { fdate, fdt, money, tripPhase } from "../format";
import { Card, Empty, ErrorBox, Loading, Progress, Stat, StatusBadge, Table } from "../components/ui";

export default function Dashboard() {
  const { user } = useAuth();
  const { data, error, loading, reload } = useFetch("/users/me/dashboard");
  if (loading) return <Loading />;
  if (error) return <ErrorBox error={error} onRetry={reload} />;
  const trips = data.trips;
  const next = trips.filter((t) => tripPhase(t) === "upcoming").sort((a, b) => a.start_date.localeCompare(b.start_date))[0];
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Hi, {user.name.split(" ")[0]}</h1>
      {trips.length === 0 ? (
        <Empty title="No trips yet" hint="Create a trip or join one with an invite code.">
          <Link className="btn btn-p" to="/app/trips/new">Create trip</Link>
          <Link className="btn" to="/app/join">Join trip</Link>
        </Empty>
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-3">
            <Stat label="Trips" value={trips.length} hint={`${trips.filter((t) => t.role === "organizer").length} as organizer`} />
            <Stat label="Next trip" value={next ? next.name : "–"} hint={next ? fdate(next.start_date) : "None upcoming"} />
            <Stat label="Contributions needed" value={trips.filter((t) => t.my_paid < t.my_target).length} hint="trips where you still owe" />
          </div>
          <Card title="Your trips">
            <div className="space-y-4">
              {trips.map((t) => (
                <Link key={t.id} to={`/app/trips/${t.id}`} className="block rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-slate-800">
                  <div className="flex justify-between text-sm"><span className="font-medium">{t.name}</span><span className="text-slate-500">{money(t.verified, t.currency)} / {money(t.budget_total, t.currency)}</span></div>
                  <Progress value={t.budget_total ? Math.round((t.verified * 100) / t.budget_total) : 0} label={`You: ${money(t.my_paid, t.currency)} of ${money(t.my_target, t.currency)}`} />
                </Link>
              ))}
            </div>
          </Card>
          <Card title="Recent activity">
            {data.activity.length === 0 ? <div className="text-sm text-slate-500">No ledger activity yet.</div> : (
              <Table head={["When", "Trip", "Type", "Amount"]}>
                {data.activity.map((a) => (
                  <tr key={a.id}><td className="td">{fdt(a.created_at)}</td><td className="td">{a.trip_name}</td><td className="td"><StatusBadge status={a.type === "contribution" ? "Verified" : a.type === "reversal" ? "Refunded" : "Approved"} /> <span className="text-slate-500">{a.type}</span></td><td className="td">{money(a.amount, a.currency)}</td></tr>
                ))}
              </Table>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
