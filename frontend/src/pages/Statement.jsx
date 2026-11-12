import { useOutletContext } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Download, Printer } from "lucide-react";
import { useFetch } from "../hooks";
import { fdt, money, toMajor } from "../format";
import { Card, ErrorBox, Loading, Stat, StatusBadge, Table } from "../components/ui";

export default function Statement() {
  const { trip } = useOutletContext();
  const { data, error, loading, reload } = useFetch(`/trips/${trip.id}/statement`);
  if (loading) return <Loading />;
  if (error) return <ErrorBox error={error} onRetry={reload} />;
  const cur = data.trip.currency;

  const csv = () => {
    const rows = [["when", "type", "member", "source", "amount"], ...data.ledger.map((l) => [l.created_at, l.type, l.member, l.source_id, (l.amount / 100).toFixed(2)])];
    const blob = new Blob([rows.map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(",")).join("\n")], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${data.trip.name}-statement.csv`;
    a.click();
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end gap-2 print:hidden">
        <button className="btn" onClick={csv}><Download className="h-4 w-4" /> CSV</button>
        <button className="btn" onClick={() => window.print()}><Printer className="h-4 w-4" /> Print / PDF</button>
      </div>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat label="Planned budget" value={money(data.planned_budget, cur)} />
        <Stat label="Collected" value={money(data.collected, cur)} />
        <Stat label="Approved expenses" value={money(data.approved_expenses, cur)} />
        <Stat label="Balance" value={money(data.balance, cur)} hint="Verified contributions − approved expenses" />
      </div>
      <Card title="Budget vs actual">
        <div className="h-64">
          <ResponsiveContainer>
            <BarChart data={data.categories.map((c) => ({ name: c.category, Budget: toMajor(c.budget), Spent: toMajor(c.spent) }))}>
              <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis /><Tooltip /><Legend />
              <Bar dataKey="Budget" fill="#94a3b8" /><Bar dataKey="Spent" fill="#0d9488" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
      <Card title="Members">
        <Table head={["Name", "Target", "Paid", "Status"]}>
          {data.members.map((m) => <tr key={m.user_id}><td className="td">{m.name}</td><td className="td">{money(m.target_amount, cur)}</td><td className="td">{money(m.paid, cur)}</td><td className="td"><StatusBadge status={m.status} /></td></tr>)}
        </Table>
      </Card>
      <Card title="Transaction history">
        <Table head={["When", "Type", "Member", "Amount"]}>
          {data.ledger.map((l) => <tr key={l.id}><td className="td">{fdt(l.created_at)}</td><td className="td capitalize">{l.type}</td><td className="td">{l.member || "–"}</td><td className="td">{money(l.amount, l.currency)}</td></tr>)}
        </Table>
        {data.ledger.length === 0 && <div className="p-3 text-sm text-slate-500">The append-only ledger is empty.</div>}
      </Card>
    </div>
  );
}
