import { useState } from "react";
import api, { errOf } from "../api";
import { applyTheme, useAuth } from "../auth";
import { Card, ErrorBox, Field, Notice } from "../components/ui";

export default function Settings() {
  const { user, setUser } = useAuth();
  const [p, setP] = useState({ name: user.name, avatar_url: user.avatar_url || "", theme: user.theme, email: !!user.notifications?.email });
  const [pw, setPw] = useState({ current_password: "", new_password: "" });
  const [msg, setMsg] = useState(null);
  const [err, setErr] = useState(null);

  const run = async (body, done) => {
    setErr(null);
    setMsg(null);
    try {
      const { data } = await api.patch("/users/me", body);
      if (data.access_token) localStorage.setItem("tb_token", data.access_token);
      setUser(data);
      applyTheme(data.theme);
      setMsg(done);
    } catch (e) {
      setErr(errOf(e));
    }
  };

  return (
    <div className="mx-auto max-w-xl space-y-4">
      <h1 className="text-2xl font-semibold">Settings</h1>
      {msg && <Notice kind="ok">{msg}</Notice>}
      <ErrorBox error={err} />
      <Card title="Profile">
        <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); run({ name: p.name, avatar_url: p.avatar_url || null, theme: p.theme, notifications: { email: p.email } }, "Profile saved"); }}>
          <Field label="Name"><input className="inp" required value={p.name} onChange={(e) => setP({ ...p, name: e.target.value })} /></Field>
          <Field label="Email"><input className="inp" disabled value={user.email} /></Field>
          <Field label="Avatar URL"><input className="inp" value={p.avatar_url} onChange={(e) => setP({ ...p, avatar_url: e.target.value })} /></Field>
          <Field label="Theme">
            <select className="inp" value={p.theme} onChange={(e) => setP({ ...p, theme: e.target.value })}><option value="system">System</option><option value="light">Light</option><option value="dark">Dark</option></select>
          </Field>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={p.email} onChange={(e) => setP({ ...p, email: e.target.checked })} /> Email notifications</label>
          <button className="btn btn-p">Save profile</button>
        </form>
      </Card>
      <Card title="Change password">
        <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); run(pw, "Password updated"); setPw({ current_password: "", new_password: "" }); }}>
          <Field label="Current password"><input className="inp" type="password" required value={pw.current_password} onChange={(e) => setPw({ ...pw, current_password: e.target.value })} /></Field>
          <Field label="New password"><input className="inp" type="password" minLength={8} maxLength={72} required value={pw.new_password} onChange={(e) => setPw({ ...pw, new_password: e.target.value })} /></Field>
          <button className="btn btn-p">Update password</button>
        </form>
      </Card>
    </div>
  );
}
