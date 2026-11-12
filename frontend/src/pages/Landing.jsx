import { Link } from "react-router-dom";
import { BarChart3, Bot, Compass, ShieldCheck, Users, Wallet } from "lucide-react";
import { useAuth } from "../auth";

const features = [
  [Users, "One trip workspace", "Organizer and members share the same plan, targets and verified progress."],
  [Wallet, "Verified contributions", "Only server-verified payments change the totals. A browser redirect never counts."],
  [Bot, "AI that explains", "Gemini drafts budgets and explains progress; it never moves money."],
  [BarChart3, "Budget vs actual", "Approved expenses are tracked by category against the official budget."],
  [ShieldCheck, "Transparent ledger", "An append-only record from first estimate to final statement."],
];
const steps = ["Create", "Invite", "Plan", "Contribute", "Reconcile"];
const faqs = [
  ["Is this real money?", "No. The demo uses PayPal Sandbox test accounts. Nothing here moves real funds."],
  ["Can members pay domestically in India?", "PayPal India does not accept domestic payments for India accounts, so a live INR launch needs an India-enabled provider and a reviewed settlement model."],
  ["Does the AI approve spending?", "Never. The organizer and deterministic backend rules control every approval."],
];

export default function Landing() {
  const { user } = useAuth();
  return (
    <div>
      <header className="mx-auto flex max-w-5xl items-center justify-between p-4">
        <div className="flex items-center gap-2 text-lg font-bold text-brand-700 dark:text-brand-500"><Compass className="h-5 w-5" /> TripBank</div>
        <div className="flex gap-2">
          {user ? <Link className="btn btn-p" to="/app">Open app</Link> : <><Link className="btn" to="/login">Log in</Link><Link className="btn btn-p" to="/register">Sign up</Link></>}
        </div>
      </header>
      <section className="mx-auto max-w-5xl px-4 py-14 text-center">
        <span className="rounded-full border border-amber-400 px-3 py-1 text-xs text-amber-700 dark:text-amber-400">Hackathon demo · PayPal Sandbox</span>
        <h1 className="mt-4 text-4xl font-bold md:text-5xl">Plan together. Contribute smartly.</h1>
        <p className="mx-auto mt-3 max-w-xl text-slate-600 dark:text-slate-400">SplitWise AI – TripBank gives every group trip one shared financial workspace with clear, verified records.</p>
        <div className="mt-6 flex justify-center gap-3">
          <Link className="btn btn-p" to={user ? "/app/trips/new" : "/register"}>Create a Trip</Link>
          <Link className="btn" to={user ? "/app/join" : "/login"}>Join a Trip</Link>
        </div>
      </section>
      <section className="mx-auto grid max-w-5xl gap-3 px-4 sm:grid-cols-2 lg:grid-cols-3">
        {features.map(([Icon, t, d]) => (
          <div key={t} className="card"><Icon className="h-5 w-5 text-brand-600" /><div className="mt-2 font-semibold">{t}</div><p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{d}</p></div>
        ))}
      </section>
      <section className="mx-auto max-w-5xl px-4 py-10">
        <h2 className="mb-4 text-xl font-semibold">How it works</h2>
        <ol className="flex flex-wrap gap-3">
          {steps.map((s, i) => <li key={s} className="card flex items-center gap-2 text-sm"><span className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-600 text-xs text-white">{i + 1}</span>{s}</li>)}
        </ol>
      </section>
      <section className="mx-auto max-w-3xl px-4 pb-10">
        <h2 className="mb-4 text-xl font-semibold">FAQ</h2>
        {faqs.map(([q, a]) => <details key={q} className="card mb-2"><summary className="cursor-pointer font-medium">{q}</summary><p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{a}</p></details>)}
      </section>
      <footer className="border-t border-slate-200 p-6 text-center text-sm text-slate-500 dark:border-slate-800">Plan together. Contribute smartly. Travel stress-free.</footer>
    </div>
  );
}
