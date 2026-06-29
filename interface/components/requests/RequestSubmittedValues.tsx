import { formatCurrency } from "@/lib/utils/formatCurrency";
import { resolveFileUrl } from "@/lib/utils/fileUrl";
import type { RequestFieldValue } from "@/types/request";

export function RequestSubmittedValues({ values = [] }: { values?: RequestFieldValue[] }) {
  if (!values.length) return <p className="text-sm text-muted-foreground">مقداری ثبت نشده است.</p>;
  return (
    <dl className="grid gap-3">
      {values.map((item) => (
        <div key={item.field} className="rounded-md border p-3">
          <dt className="text-sm font-semibold">{item.label}</dt>
          <dd className="mt-1 text-sm text-muted-foreground">
            {item.file ? (
              <a className="text-primary" href={resolveFileUrl(item.file)} target="_blank">مشاهده فایل</a>
            ) : item.type === "money" ? (
              formatCurrency(item.value)
            ) : typeof item.value === "boolean" ? (
              item.value ? "بله" : "خیر"
            ) : (
              String(item.value ?? "-")
            )}
          </dd>
        </div>
      ))}
    </dl>
  );
}
