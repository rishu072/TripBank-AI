import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import api, { errOf } from "../api";
import { Card, ErrorBox, Field } from "../components/ui";

export default function JoinTrip() {
  const [q] = useSearchParams();
  const nav = useNavigate();
  const [code, setCode] = useState(q.get("code") || "");
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);
  const go = async (e) => {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      const { data } = await api.post("/trips/join", { code });
      nav(`/app/trips/${data.trip_id}`);
    } catch (x) {
      setErr(errOf(x));
      setBusy(false);
    }
  };
  return (
    <form onSubmit={go} className="mx-auto max-w-md space-y-4">
      <h1 className="text-2xl font-semibold">Join a trip</h1>
      <Card>
        <Field label="Invite code"><input className="inp uppercase" required value={code} onChange={(e) => setCode(e.target.value)} placeholder="XXXX-XXXX" /></Field>
      </Card>
      <ErrorBox error={err} />
      <button className="btn btn-p" disabled={busy}>{busy ? "Joining…" : "Join trip"}</button>
    </form>
  );
}
