import { useState } from "react";
import { useNavigate, useOutletContext } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Copy, KeyRound, Trash2 } from "lucide-react";
import api, { errOf } from "../api";
import { useFetch } from "../hooks";
import { fdate, money, toMajor, toMinor } from "../format";
import { Card, ErrorBox, Loading, Notice, Progress, Stat, StatusBadge, Table } from "../components/ui";

export default function TripFund() {
  const { trip, reload } = useOutletContext();
  const nav = useNavigate();
  const fund = useFetch(`/trips/${trip.id}/fund`);
  const org = trip.role === "organizer";
  const [invite, setInvite] = useState(() => JSON.parse(sessionStorage.getItem(`invite:${trip.id}`) || "null"));
  const [err, setErr] = useState(null);
  const [edit, setEdit] = useState({});

  const act = async (fn) => {
    setErr(null);
    try {
      await fn();
      fund.reload();
      reload();
    } catch (e) {
      setErr(errOf(e));
    }
  };

  if (fund.loading) return <Loading />;
  if (fund.error) return <ErrorBox error={fund.error} onRetry={fund.reload} />;
  const f = fund.data;
  const cur = f.currency;
  const link = invite ? `${location.origin}/app/join?code=${invite.code}` : "";

  return (
    <div className="space-y-4">
      <ErrorBox error={err} />
      {trip.budget_stale && <Notice kind="warn">The approved budget no longer matches the target. Approve a new budget in the AI tab.</Notice>}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        <Stat label="Funding target" value={money(f.target, cur)} />
        <Stat label="Verified in" value={money(f.verified, cur)} />
        <Stat label="Remaining" value={money(f.remaining, cur)} />
        <Stat label="Approved spend" value={money(f.approved_spend, cur)} />
        <Stat label="Available" value={money(f.available, cur)} hint="Ledger figure, not a PayPal balance" />
      </div>
      <Card><Progress value={f.progress_pct} label={`${f.progress_pct}% funded · verified contributions only${trip.deadline ? ` · deadline ${fdate(trip.deadline)}` : ""}`} /></Card>
      <Card title="Members">
        <Table head={["Name", "Role", "Target", "Paid", "Remaining", "Status", ""]}>
          {f.members.map((m) => (
            <tr key={m.user_id}>
              <td className="td font-medium">{m.name}</td>
              <td className="td capitalize">{m.role}</td>
              <td className="td">
                {org && trip.status === "active" ? (
                  <input className="inp w-28" type="number" min="0" step="0.01" defaultValue={toMajor(m.target_amount)} onChange={(e) => setEdit({ ...edit, [m.user_id]: e.target.value })} onBlur={() => edit[m.user_id] !== undefined && act(async () => { await api.patch(`/trips/${trip.id}/members/${m.user_id}`, { target_amount: toMinor(edit[m.user_id]) }); setEdit({}); })} aria-label={`Target for ${m.name}`} />
                ) : money(m.target_amount, cur)}
              </td>
              <td className="td">{money(m.paid, cur)}</td>
              <td className="td">{money(m.remaining, cur)}</td>
              <td className="td"><StatusBadge status={m.status} /></td>
              <td className="td">{org && m.role !== "organizer" && <button className="btn btn-d" onClick={() => confirm(`Remove ${m.name}?`) && act(() => api.delete(`/trips/${trip.id}/members/${m.user_id}`))} aria-label={`Remove ${m.name}`}><Trash2 className="h-3.5 w-3.5" /></button>}</td>
            </tr>
          ))}
        </Table>
      </Card>
      <Card title="Paid vs target">
        <div className="h-64">
          <ResponsiveContainer>
            <BarChart data={f.members.map((m) => ({ name: m.name, Paid: toMajor(m.paid), Target: toMajor(m.target_amount) }))}>
              <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis /><Tooltip /><Legend />
              <Bar dataKey="Target" fill="#94a3b8" /><Bar dataKey="Paid" fill="#0d9488" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
      {org && trip.status === "active" && (
        <Card title="Invite">
          <div className="flex flex-wrap items-center gap-2">
            <button className="btn" onClick={() => act(async () => { const { data } = await api.post(`/trips/${trip.id}/invites`); sessionStorage.setItem(`invite:${trip.id}`, JSON.stringify(data)); setInvite(data); })}><KeyRound className="h-4 w-4" /> {invite ? "Rotate invite" : "Create invite"}</button>
            <button className="btn btn-d" onClick={() => act(async () => { await api.delete(`/trips/${trip.id}/invites`); sessionStorage.removeItem(`invite:${trip.id}`); setInvite(null); })}>Revoke</button>
          </div>
          {invite && (
            <div className="mt-3 space-y-1 text-sm">
              <div>Code: <b className="font-mono">{invite.code}</b> · expires {fdate(invite.expires_at)}</div>
              <div className="flex items-center gap-2 break-all text-slate-500">{link} <button className="btn" onClick={() => navigator.clipboard.writeText(link)} aria-label="Copy link"><Copy className="h-3.5 w-3.5" /></button></div>
            </div>
          )}
          <p className="mt-2 text-xs text-slate-500">Codes are stored hashed, so a code can only be shown when created or rotated.</p>
        </Card>
      )}
      <div className="flex flex-wrap gap-2">
        {org && trip.status === "active" && <button className="btn btn-d" onClick={() => confirm("Close this trip? This cannot be undone.") && act(() => api.post(`/trips/${trip.id}/close`))}>Close trip</button>}
        {!org && <button className="btn btn-d" onClick={() => confirm("Leave this trip?") && act(async () => { await api.delete(`/trips/${trip.id}/leave`); nav("/app/trips"); })}>Leave trip</button>}
      </div>
    </div>
  );
}
