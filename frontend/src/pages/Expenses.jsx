import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import api, { errOf } from "../api";
import { useFetch } from "../hooks";
import { CATEGORIES, fdate, money, toMinor } from "../format";
import { Card, Empty, ErrorBox, Field, Loading, StatusBadge, Table } from "../components/ui";

const blank = { title: "", category: "Stay", amount: "", date: new Date().toISOString().slice(0, 10), paid_by: "", description: "", receipt_url: "" };

export default function Expenses() {
  const { trip } = useOutletContext();
  const org = trip.role === "organizer";
  const list = useFetch(`/trips/${trip.id}/expenses`);
  const [f, setF] = useState(blank);
  const [file, setFile] = useState(null);
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const upload = async () => {
    const { data: s } = await api.post(`/trips/${trip.id}/uploads/signature`);
    const fd = new FormData();
    fd.append("file", file);
    ["api_key", "timestamp", "signature", "folder"].forEach((k) => fd.append(k, s[k]));
    const r = await fetch(`https://api.cloudinary.com/v1_1/${s.cloud_name}/auto/upload`, { method: "POST", body: fd });
    if (!r.ok) throw { response: { data: { error: { code: "UPLOAD_FAILED", message: "Receipt upload failed" } } } };
    return (await r.json()).secure_url;
  };

  const add = async (e) => {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      const receipt_url = file ? await upload() : null;
      await api.post(`/trips/${trip.id}/expenses`, { ...f, amount: toMinor(f.amount), receipt_url });
      setF(blank);
      setFile(null);
      list.reload();
    } catch (x) {
      setErr(errOf(x));
    } finally {
      setBusy(false);
    }
  };

  const approve = async (id) => {
    setErr(null);
    try {
      await api.patch(`/trips/${trip.id}/expenses/${id}/approve`);
      list.reload();
    } catch (x) {
      setErr(errOf(x));
    }
  };

  return (
    <div className="space-y-4">
      <ErrorBox error={err} />
      {org && trip.status === "active" && (
        <Card title="Record expense">
          <form onSubmit={add} className="grid gap-3 sm:grid-cols-3">
            <Field label="Title"><input className="inp" required value={f.title} onChange={set("title")} /></Field>
            <Field label="Category"><select className="inp" value={f.category} onChange={set("category")}>{CATEGORIES.map((c) => <option key={c}>{c}</option>)}</select></Field>
            <Field label={`Amount (${trip.currency})`}><input className="inp" type="number" min="0.01" step="0.01" required value={f.amount} onChange={set("amount")} /></Field>
            <Field label="Date"><input className="inp" type="date" required value={f.date} onChange={set("date")} /></Field>
            <Field label="Paid by"><input className="inp" value={f.paid_by} onChange={set("paid_by")} /></Field>
            <Field label="Receipt (optional)"><input className="inp" type="file" accept="image/*,application/pdf" onChange={(e) => setFile(e.target.files[0] || null)} /></Field>
            <div className="sm:col-span-3"><Field label="Description"><input className="inp" value={f.description} onChange={set("description")} /></Field></div>
            <div><button className="btn btn-p" disabled={busy}>{busy ? "Saving…" : "Add draft"}</button></div>
          </form>
        </Card>
      )}
      <Card title="Expenses">
        {list.loading ? <Loading /> : list.error ? <ErrorBox error={list.error} onRetry={list.reload} /> : list.data.length === 0 ? <Empty title="No expenses yet" hint={org ? "Add a draft, then approve it." : "Approved expenses appear here."} /> : (
          <Table head={["Title", "Category", "Date", "Amount", "Status", "Receipt", ""]}>
            {list.data.map((e) => (
              <tr key={e.id}>
                <td className="td font-medium">{e.title}</td><td className="td">{e.category}</td><td className="td">{fdate(e.date)}</td><td className="td">{money(e.amount, e.currency)}</td>
                <td className="td"><StatusBadge status={e.approval_status} /></td>
                <td className="td">{e.receipt_url ? <a className="text-brand-700 underline dark:text-brand-500" href={e.receipt_url} target="_blank" rel="noreferrer">View</a> : "–"}</td>
                <td className="td">{org && e.approval_status === "draft" && <button className="btn" onClick={() => approve(e.id)}>Approve</button>}</td>
              </tr>
            ))}
          </Table>
        )}
        <p className="mt-2 text-xs text-slate-500">Only approved expenses reduce the available balance.</p>
      </Card>
    </div>
  );
}
