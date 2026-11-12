import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import { Flag, RefreshCw, Sparkles } from "lucide-react";
import api, { errOf } from "../api";
import { fdt } from "../format";
import BudgetDraft from "../components/BudgetDraft";
import { Card, ErrorBox, Notice } from "../components/ui";

const prompts = ["How much funding remains?", "Who is pending?", "What is the available balance?", "Are we over budget?"];

export default function AIAssistant() {
  const { trip, reload } = useOutletContext();
  const org = trip.role === "organizer";
  const [prefs, setPrefs] = useState({ preferences: "", accommodation: "", transport: "" });
  const [draft, setDraft] = useState(null);
  const [saved, setSaved] = useState(false);
  const [q, setQ] = useState("");
  const [ans, setAns] = useState(null);
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState("");

  const run = async (name, fn) => {
    setBusy(name);
    setErr(null);
    try {
      await fn();
    } catch (e) {
      setErr(errOf(e));
    } finally {
      setBusy("");
    }
  };

  const plan = () => run("plan", async () => { setSaved(false); setDraft((await api.post("/ai/budget-plan", { trip_id: trip.id, ...prefs })).data); });
  const save = () => run("save", async () => {
    await api.post(`/trips/${trip.id}/budget`, { categories: Object.fromEntries(draft.categories.map((c) => [c.category, c.amount])) });
    setSaved(true);
    setDraft(null);
    reload();
  });
  const ask = (text) => run("ask", async () => { setQ(text); setAns({ ...(await api.post(`/trips/${trip.id}/ai/ask`, { question: text })).data, question: text }); });

  return (
    <div className="space-y-4">
      <ErrorBox error={err} />
      {saved && <Notice kind="ok">Official budget saved.</Notice>}
      <Card title="AI budget planner">
        <p className="mb-3 text-sm text-slate-600 dark:text-slate-400">AI suggestions are drafts. Only the organizer can approve one, and category totals must equal the target.</p>
        <div className="grid gap-3 sm:grid-cols-3">
          <input className="inp" placeholder="Preferences" maxLength={500} value={prefs.preferences} onChange={(e) => setPrefs({ ...prefs, preferences: e.target.value })} aria-label="Preferences" />
          <input className="inp" placeholder="Accommodation" maxLength={100} value={prefs.accommodation} onChange={(e) => setPrefs({ ...prefs, accommodation: e.target.value })} aria-label="Accommodation" />
          <input className="inp" placeholder="Transport" maxLength={100} value={prefs.transport} onChange={(e) => setPrefs({ ...prefs, transport: e.target.value })} aria-label="Transport" />
        </div>
        <div className="mt-3 flex gap-2">
          <button className="btn" onClick={plan} disabled={busy === "plan"}><Sparkles className="h-4 w-4" /> {busy === "plan" ? "Drafting…" : "Generate draft"}</button>
          {draft && <button className="btn" onClick={() => setDraft(null)}>Discard</button>}
        </div>
        {draft && (
          <div className="mt-4 space-y-3">
            <BudgetDraft draft={draft} setDraft={setDraft} currency={trip.currency} total={trip.budget_total} />
            <button className="btn btn-p" disabled={!org || busy === "save"} onClick={save}>{org ? "Approve as official budget" : "Organizer approval required"}</button>
          </div>
        )}
        {trip.budget && !draft && <p className="mt-3 text-sm text-slate-500">Official budget v{trip.budget.version} is active.</p>}
      </Card>
      <Card title="Ask about your trip money">
        <div className="flex flex-wrap gap-2">{prompts.map((p) => <button key={p} className="btn" onClick={() => ask(p)} disabled={busy === "ask"}>{p}</button>)}</div>
        <form className="mt-3 flex gap-2" onSubmit={(e) => { e.preventDefault(); q.trim().length > 1 && ask(q); }}>
          <input className="inp" value={q} maxLength={500} onChange={(e) => setQ(e.target.value)} placeholder="Ask a question" aria-label="Question" />
          <button className="btn btn-p" disabled={busy === "ask"}>{busy === "ask" ? "Checking…" : "Ask"}</button>
        </form>
        {ans && (
          <div className="mt-4 rounded-lg bg-slate-100 p-3 text-sm dark:bg-slate-800">
            <div>{ans.answer}</div>
            <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-slate-500">
              <span>{ans.source === "gemini" ? "Gemini" : "Rule-based"} · snapshot {fdt(ans.snapshot_at)}</span>
              <button className="inline-flex items-center gap-1 underline" onClick={() => ask(ans.question)}><RefreshCw className="h-3 w-3" /> Refresh</button>
              <button className="inline-flex items-center gap-1 underline" onClick={() => api.post(`/trips/${trip.id}/ai/insights/${ans.id}/report`).then(() => setAns({ ...ans, reported: true }))}><Flag className="h-3 w-3" /> {ans.reported ? "Reported" : "Report a problem"}</button>
            </div>
          </div>
        )}
        <p className="mt-3 text-xs text-slate-500">Answers explain verified trip facts. The AI cannot approve, move, or record money.</p>
      </Card>
    </div>
  );
}
