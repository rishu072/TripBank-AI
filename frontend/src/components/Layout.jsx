import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { Compass, LayoutDashboard, LogOut, Menu, Plane, Plus, Settings, UserPlus, X } from "lucide-react";
import { useAuth } from "../auth";

const links = [
  ["/app", "Overview", LayoutDashboard, true],
  ["/app/trips", "My trips", Plane, true],
  ["/app/trips/new", "Create trip", Plus, true],
  ["/app/join", "Join trip", UserPlus, true],
  ["/app/settings", "Settings", Settings, true],
];

export default function Layout() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const nav = useNavigate();
  const item = ([to, label, Icon, end]) => (
    <NavLink key={to} to={to} end={end} onClick={() => setOpen(false)} className={({ isActive }) => `flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium ${isActive ? "bg-brand-600 text-white" : "hover:bg-slate-200 dark:hover:bg-slate-800"}`}>
      <Icon className="h-4 w-4" /> {label}
    </NavLink>
  );
  const side = (
    <div className="flex h-full flex-col gap-1 p-3">
      <div className="mb-3 flex items-center gap-2 px-2 text-lg font-bold text-brand-700 dark:text-brand-500">
        <Compass className="h-5 w-5" /> TripBank
      </div>
      {links.map(item)}
      <div className="mt-auto border-t border-slate-200 pt-3 dark:border-slate-800">
        <div className="truncate px-2 pb-2 text-xs text-slate-500">{user?.name}</div>
        <button className="btn w-full" onClick={() => { logout(); nav("/"); }}>
          <LogOut className="h-4 w-4" /> Log out
        </button>
      </div>
    </div>
  );
  return (
    <div className="min-h-screen md:flex">
      <aside className="hidden w-60 shrink-0 border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 md:block">{side}</aside>
      <div className="flex items-center justify-between border-b border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900 md:hidden">
        <div className="flex items-center gap-2 font-bold text-brand-700 dark:text-brand-500"><Compass className="h-5 w-5" /> TripBank</div>
        <button className="btn" onClick={() => setOpen(!open)} aria-label="Menu">{open ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}</button>
      </div>
      {open && <div className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 md:hidden">{side}</div>}
      <main className="min-w-0 flex-1 p-4 md:p-6"><Outlet /></main>
    </div>
  );
}
