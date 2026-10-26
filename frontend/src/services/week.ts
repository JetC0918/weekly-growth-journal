/** Monday of the week containing `date`, as YYYY-MM-DD (local time). */
export function weekStartOf(date: Date = new Date()): string {
  const d = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const day = (d.getDay() + 6) % 7; // Mon=0
  d.setDate(d.getDate() - day);
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${mm}-${dd}`;
}

/** Monday of the week immediately after the supplied review week. */
export function nextWeekStart(weekStart: string): string {
  const [year = 1970, month = 1, day = 1] = weekStart.split("-").map(Number);
  return weekStartOf(new Date(year, month - 1, day + 7));
}

export function formatWeek(weekStart: string): string {
  const [y = 1970, m = 1, d = 1] = weekStart.split("-").map(Number);
  const start = new Date(y, m - 1, d);
  const end = new Date(y, m - 1, d + 6);
  const fmt = (x: Date) => x.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  return `${fmt(start)} – ${fmt(end)}, ${end.getFullYear()}`;
}
