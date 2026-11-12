import { CATEGORIES, money, toMajor, toMinor } from "../format";
import { Notice, Table } from "./ui";

export default function BudgetDraft({ draft, setDraft, currency, total }) {
  const amounts = Object.fromEntries(draft.categories.map((c) => [c.category, c.amount]));
  const sum = CATEGORIES.reduce((a, c) => a + (amounts[c] || 0), 0);
  const edit = (cat, v) =>
    setDraft({ ...draft, categories: draft.categories.map((c) => (c.category === cat ? { ...c, amount: Number.isFinite(toMinor(v)) ? toMinor(v) : 0 } : c)) });
  return (
    <div className="space-y-3">
      <Notice kind={draft.source === "gemini" ? "info" : "warn"}>
        {draft.source === "gemini" ? "Draft suggested by Gemini." : "Rule-based starting split (no AI draft available)."} Confidence: {draft.confidence}. Review and edit before approving.
      </Notice>
      <Table head={["Category", "Amount", "Why"]}>
        {draft.categories.map((c) => (
          <tr key={c.category}>
            <td className="td font-medium">{c.category}</td>
            <td className="td">
              <input className="inp w-32" type="number" min="0" step="0.01" value={toMajor(c.amount)} onChange={(e) => edit(c.category, e.target.value)} aria-label={`${c.category} amount`} />
            </td>
            <td className="px-3 py-2 text-sm text-slate-500">{c.explanation}</td>
          </tr>
        ))}
      </Table>
      <div className={`text-sm font-medium ${sum === total ? "text-green-700 dark:text-green-400" : "text-red-700 dark:text-red-400"}`}>
        Total {money(sum, currency)} of {money(total, currency)} {sum === total ? "✓" : "– must match the target"}
      </div>
      {draft.assumptions?.length > 0 && (
        <ul className="list-disc pl-5 text-sm text-slate-600 dark:text-slate-400">
          {draft.assumptions.map((a, i) => <li key={i}>{a}</li>)}
        </ul>
      )}
    </div>
  );
}
