export function formatCurrency(value: unknown) {
  const amount = Number(String(value ?? "").replaceAll(",", ""));
  if (!Number.isFinite(amount)) return "-";
  return new Intl.NumberFormat("fa-IR").format(amount) + " تومان";
}
