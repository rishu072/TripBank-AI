import { useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { Compass } from "lucide-react";
import api, { errOf } from "../api";
import { useAuth } from "../auth";
import { Field, Notice } from "../components/ui";

function Shell({ title, children }) {
  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="card w-full max-w-sm">
        <Link to="/" className="mb-4 flex items-center gap-2 font-bold text-brand-700 dark:text-brand-500"><Compass className="h-5 w-5" /> TripBank</Link>
        <h1 className="mb-4 text-xl font-semibold">{title}</h1>
        {children}
      </div>
    </div>
  );
}

function useForm(initial, submit) {
  const [v, setV] = useState(initial);
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);
  const on = (k) => (e) => setV({ ...v, [k]: e.target.value });
  const go = async (e) => {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      await submit(v);
    } catch (x) {
      setErr(errOf(x));
    } finally {
      setBusy(false);
    }
  };
  return { v, on, go, err, busy };
}

const Err = ({ err }) => err && <div className="text-sm text-red-600" role="alert">{err.message}</div>;

export function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();
  const f = useForm({ email: "", password: "" }, async (v) => { await login(v); nav(loc.state?.from || "/app", { replace: true }); });
  return (
    <Shell title="Log in">
      <form onSubmit={f.go} className="space-y-3">
        <Field label="Email"><input className="inp" type="email" required value={f.v.email} onChange={f.on("email")} /></Field>
        <Field label="Password"><input className="inp" type="password" required value={f.v.password} onChange={f.on("password")} /></Field>
        <Err err={f.err} />
        <button className="btn btn-p w-full" disabled={f.busy}>{f.busy ? "Signing in…" : "Log in"}</button>
        <div className="flex justify-between text-sm"><Link className="text-brand-700 dark:text-brand-500" to="/forgot-password">Forgot password?</Link><Link className="text-brand-700 dark:text-brand-500" to="/register">Create account</Link></div>
      </form>
    </Shell>
  );
}

export function Register() {
  const { register } = useAuth();
  const nav = useNavigate();
  const f = useForm({ name: "", email: "", password: "" }, async (v) => { await register(v); nav("/app", { replace: true }); });
  return (
    <Shell title="Create your account">
      <form onSubmit={f.go} className="space-y-3">
        <Field label="Name"><input className="inp" required value={f.v.name} onChange={f.on("name")} /></Field>
        <Field label="Email"><input className="inp" type="email" required value={f.v.email} onChange={f.on("email")} /></Field>
        <Field label="Password (8+ characters)"><input className="inp" type="password" minLength={8} maxLength={72} required value={f.v.password} onChange={f.on("password")} /></Field>
        <Err err={f.err} />
        <button className="btn btn-p w-full" disabled={f.busy}>{f.busy ? "Creating…" : "Sign up"}</button>
        <div className="text-sm"><Link className="text-brand-700 dark:text-brand-500" to="/login">Already have an account?</Link></div>
      </form>
    </Shell>
  );
}

export function Forgot() {
  const [sent, setSent] = useState(false);
  const f = useForm({ email: "" }, async (v) => { await api.post("/auth/forgot-password", v); setSent(true); });
  return (
    <Shell title="Reset password">
      {sent ? <Notice kind="ok">If the account exists, a reset link has been issued. In development the link is printed in the API log.</Notice> : (
        <form onSubmit={f.go} className="space-y-3">
          <Field label="Email"><input className="inp" type="email" required value={f.v.email} onChange={f.on("email")} /></Field>
          <Err err={f.err} />
          <button className="btn btn-p w-full" disabled={f.busy}>Send reset link</button>
        </form>
      )}
      <div className="mt-3 text-sm"><Link className="text-brand-700 dark:text-brand-500" to="/login">Back to login</Link></div>
    </Shell>
  );
}

export function Reset() {
  const [q] = useSearchParams();
  const nav = useNavigate();
  const f = useForm({ new_password: "" }, async (v) => { await api.post("/auth/reset-password", { token: q.get("token") || "", ...v }); nav("/login"); });
  return (
    <Shell title="Choose a new password">
      <form onSubmit={f.go} className="space-y-3">
        <Field label="New password"><input className="inp" type="password" minLength={8} maxLength={72} required value={f.v.new_password} onChange={f.on("new_password")} /></Field>
        <Err err={f.err} />
        <button className="btn btn-p w-full" disabled={f.busy}>Update password</button>
      </form>
    </Shell>
  );
}
