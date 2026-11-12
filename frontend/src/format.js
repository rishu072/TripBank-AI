export const money = (minor, cur = "INR") =>
  new Intl.NumberFormat(cur === "INR" ? "en-IN" : undefined, { style: "currency", currency: cur }).format((minor || 0) / 100);
export const toMinor = (v) => Math.round(parseFloat(v) * 100);
export const toMajor = (minor) => (minor || 0) / 100;
export const fdate = (s) => (s ? new Date(s).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" }) : "–");
export const fdt = (s) => (s ? new Date(s).toLocaleString() : "–");
export const CATEGORIES = ["Stay", "Transport", "Food", "Activities", "Local travel", "Reserve"];
export const tripPhase = (t) => {
  if (t.status === "closed" || t.status === "archived") return "completed";
  return new Date(t.start_date) > new Date() ? "upcoming" : "active";
};
