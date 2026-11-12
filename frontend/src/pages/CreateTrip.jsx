import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Sparkles } from "lucide-react";
import api, { errOf } from "../api";
import { toMinor } from "../format";
import BudgetDraft from "../components/BudgetDraft";
import { Card, ErrorBox, Field } from "../components/ui";

const CUR = import.meta.env.VITE_DEFAULT_CURRENCY || "USD";

export default function CreateTrip() {
  const nav = useNavigate();
  const [f, setF] = useState({ name: "", destination: "", start_date: "", end_date: "", group_size: 5, budget: "", currency: CUR, deadline: "", description: "", preferences: "" });
  const [draft, setDraft] = useState(null);
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const total = toMinor(f.budget);
  const days = f.start_date && f.end_date ? Math.max(1, Math.round((new Date(f.end_date) - new Date(f.start_date)) / 864e5) + 1) : 0;

  const suggest = async () => {
    setBusy(true);
    setErr(null);
    try {
      const { data } = await api.post("/ai/budget-plan", { destination: f.destination, people: Number(f.group_size), days, total, currency: f.currency, preferences: f.preferences });
      setDraft(data);
    } catch (e) {
      setErr(errOf(e));
    } finally {
      setBusy(false);
    }
  };

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      const { data } = await api.post("/trips", { name: f.name, destination: f.destination, start_date: f.start_date, end_date: f.end_date, group_size: Number(f.group_size), budget_total: total, currency: f.currency, deadline: f.deadline || null, description: f.description });
      const id = data.trip.id;
      if (draft && draft.categories.reduce((a, c) => a + c.amount, 0) === total) {
        await api.post(`/trips/${id}/budget`, { categories: Object.fromEntries(draft.categories.map((c) => [c.category, c.amount])) });
      }
      sessionStorage.setItem(`invite:${id}`, JSON.stringify(data.invite));
      nav(`/app/trips/${id}`);
    } catch (x) {
      setErr(errOf(x));
      setBusy(false);
    }
  };

  const ready = f.destination && days > 0 && total > 0;
  return (
    <form onSubmit={submit} className="mx-auto max-w-3xl space-y-4">
      <h1 className="text-2xl font-semibold">Create trip</h1>
      <Card>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Trip name"><input className="inp" required value={f.name} onChange={set("name")} /></Field>
          <Field label="Destination"><input className="inp" required value={f.destination} onChange={set("destination")} /></Field>
          <Field label="Start date"><input className="inp" type="date" required value={f.start_date} onChange={set("start_date")} /></Field>
          <Field label="End date"><input className="inp" type="date" required min={f.start_date} value={f.end_date} onChange={set("end_date")} /></Field>
          <Field label="Group size"><input className="inp" type="number" min="2" max="50" required value={f.group_size} onChange={set("group_size")} /></Field>
          <Field label="Target budget (total)"><input className="inp" type="number" min="1" step="0.01" required value={f.budget} onChange={set("budget")} /></Field>
          <Field label="Currency (3 letters)"><input className="inp uppercase" maxLength={3} minLength={3} required value={f.currency} onChange={set("currency")} /></Field>
          <Field label="Contribution deadline"><input className="inp" type="date" value={f.deadline} onChange={set("deadline")} /></Field>
          <div className="sm:col-span-2"><Field label="Description"><textarea className="inp" rows={2} value={f.description} onChange={set("description")} /></Field></div>
        </div>
      </Card>
      <Card title="AI budget draft" action={<button type="button" className="btn" disabled={!ready || busy} onClick={suggest}><Sparkles className="h-4 w-4" /> Suggest budget</button>}>
        <Field label="Preferences (optional)"><input className="inp" maxLength={500} placeholder="Beach hotel, scooter rental, local food" value={f.preferences} onChange={set("preferences")} /></Field>
        {draft && <div className="mt-3"><BudgetDraft draft={draft} setDraft={setDraft} currency={f.currency} total={total} /></div>}
        {!draft && <p className="mt-2 text-sm text-slate-500">Optional. You can also approve a budget later from the AI tab.</p>}
      </Card>
      <ErrorBox error={err} />
      <button className="btn btn-p" disabled={busy}>{busy ? "Working…" : "Create trip"}</button>
    </form>
  );
}
