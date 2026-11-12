import { useRef, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { PayPalButtons, PayPalScriptProvider } from "@paypal/react-paypal-js";
import api, { errOf } from "../api";
import { useFetch } from "../hooks";
import { fdt, money, toMajor, toMinor } from "../format";
import { Card, ErrorBox, Loading, Notice, StatusBadge, Table } from "../components/ui";

const CLIENT_ID = import.meta.env.VITE_PAYPAL_CLIENT_ID;

export default function Contributions() {
  const { trip, reload } = useOutletContext();
  const mine = useFetch(`/trips/${trip.id}/contributions`, { scope: "mine" });
  const group = useFetch(`/trips/${trip.id}/contributions`, { scope: "group" });
  const meRow = trip.members.find((m) => m.user_id === trip.my_user_id) || trip.members[0];
  const remaining = meRow.remaining;
  const [amount, setAmount] = useState(String(toMajor(remaining) || ""));
  const [state, setState] = useState({ kind: "idle" });
  const orderRef = useRef(null);
  const minor = toMinor(amount);
  const valid = Number.isFinite(minor) && minor > 0 && minor <= remaining && trip.status === "active";

  const refresh = () => { mine.reload(); group.reload(); reload(); };

  if (mine.loading || group.loading) return <Loading />;
  if (mine.error) return <ErrorBox error={mine.error} onRetry={mine.reload} />;

  return (
    <div className="space-y-4">
      <Card title="Contribute">
        <div className="mb-3 text-sm text-slate-600 dark:text-slate-400">Target {money(meRow.target_amount, trip.currency)} · Paid {money(meRow.paid, trip.currency)} · Remaining {money(remaining, trip.currency)}</div>
        <div className="flex flex-wrap items-end gap-2">
          <div><span className="lbl">Amount ({trip.currency})</span><input className="inp w-40" type="number" min="0.01" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} aria-label="Contribution amount" /></div>
          {[1000, 2000].map((q) => <button key={q} className="btn" onClick={() => setAmount(String(Math.min(q, toMajor(remaining))))}>{money(q * 100, trip.currency)}</button>)}
          <button className="btn" onClick={() => setAmount(String(toMajor(remaining)))}>Remaining</button>
        </div>
        {!valid && amount && <div className="mt-2 text-sm text-red-600">Enter an amount up to your remaining target.</div>}
        <div className="mt-4 max-w-sm">
          {!CLIENT_ID ? <Notice kind="warn">Set VITE_PAYPAL_CLIENT_ID in frontend/.env to enable Sandbox checkout.</Notice> : (
            <PayPalScriptProvider key={trip.currency} options={{ clientId: CLIENT_ID, currency: trip.currency, intent: "capture" }}>
              <PayPalButtons
                style={{ layout: "vertical" }}
                disabled={!valid}
                forceReRender={[minor, trip.currency]}
                createOrder={async () => {
                  setState({ kind: "starting" });
                  try {
                    const { data } = await api.post(`/trips/${trip.id}/payment-orders`, { amount: minor }, { headers: { "Idempotency-Key": crypto.randomUUID() } });
                    orderRef.current = data.order_id;
                    return data.provider_order_id;
                  } catch (e) {
                    setState({ kind: "error", err: errOf(e) });
                    throw e;
                  }
                }}
                onApprove={async () => {
                  setState({ kind: "processing" });
                  try {
                    const { data } = await api.post(`/payments/${orderRef.current}/capture`);
                    setState({ kind: data.duplicate ? "duplicate" : "verified", receipt: data });
                    refresh();
                  } catch (e) {
                    setState({ kind: "error", err: errOf(e) });
                    refresh();
                  }
                }}
                onCancel={() => { setState({ kind: "cancelled" }); refresh(); }}
                onError={() => setState((s) => (s.kind === "error" ? s : { kind: "error", err: { code: "PAYMENT_DECLINED", message: "The payment was declined or interrupted." } }))}
              />
            </PayPalScriptProvider>
          )}
        </div>
        <p className="mt-2 text-xs text-slate-500">Sandbox mode – test payment only. Your contribution shows as Verified only after the server confirms the capture.</p>
        {state.kind === "processing" && <div className="mt-3"><Notice>Processing: confirming the capture on the server…</Notice></div>}
        {state.kind === "cancelled" && <div className="mt-3"><Notice kind="warn">Checkout cancelled. Nothing was charged.</Notice></div>}
        {state.kind === "error" && <div className="mt-3"><ErrorBox error={state.err} /></div>}
        {(state.kind === "verified" || state.kind === "duplicate") && (
          <div className="mt-3"><Notice kind="ok">
            {state.kind === "duplicate" ? "This payment was already recorded; totals did not change twice. " : "Verified. "}
            Receipt: {money(state.receipt.amount, state.receipt.currency)} · ref {state.receipt.provider_ref} · {fdt(state.receipt.captured_at)}
          </Notice></div>
        )}
      </Card>
      <Card title="My payments">
        <Table head={["Date", "Amount", "Status", "Reference"]}>
          {mine.data.orders.map((o) => <tr key={o.id}><td className="td">{fdt(o.created_at)}</td><td className="td">{money(o.amount, o.currency)}</td><td className="td"><StatusBadge status={o.status} /></td><td className="td text-slate-500">{o.id.slice(-8)}</td></tr>)}
          {mine.data.contributions.map((c) => <tr key={c.id}><td className="td">{fdt(c.captured_at)}</td><td className="td">{money(c.amount, c.currency)}</td><td className="td"><StatusBadge status={c.status} /></td><td className="td text-slate-500">{c.provider_ref}</td></tr>)}
        </Table>
        {mine.data.orders.length + mine.data.contributions.length === 0 && <div className="p-3 text-sm text-slate-500">No payments yet.</div>}
      </Card>
      <Card title="Group contributions">
        <Table head={["Member", "Date", "Amount", "Status"]}>
          {group.data?.contributions.map((c, i) => <tr key={i}><td className="td">{c.member}</td><td className="td">{fdt(c.captured_at)}</td><td className="td">{money(c.amount, c.currency)}</td><td className="td"><StatusBadge status={c.status} /></td></tr>)}
        </Table>
        {group.data?.contributions.length === 0 && <div className="p-3 text-sm text-slate-500">No verified contributions yet.</div>}
      </Card>
    </div>
  );
}
