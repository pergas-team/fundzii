import { formatDate } from "@/lib/utils/formatDate";
import { translateStatus } from "@/lib/utils/statusLabels";
import type { RequestHistoryItem } from "@/types/workflow";

export function RequestTimeline({ history = [] }: { history?: RequestHistoryItem[] }) {
  if (!history.length) return <p className="text-sm text-muted-foreground">تاریخچه‌ای ثبت نشده است.</p>;
  return (
    <div className="relative grid gap-6 border-r-2 border-border pr-6">
      {history.map((item, index) => (
        <div key={item.id} className="relative">
          <span
            className={`absolute -right-[31px] top-0.5 grid h-4 w-4 place-items-center rounded-full ring-4 ring-card ${
              index === 0 ? "bg-accent" : "bg-primary"
            }`}
          />
          <p className="font-bold">{translateStatus(item.to_status)}</p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {formatDate(item.created_at)}
            {item.changed_by ? ` · ${item.changed_by}` : ""}
          </p>
          {item.note ? (
            <p className="mt-2 rounded-lg bg-muted/60 px-3 py-2 text-sm leading-6 text-muted-foreground">{item.note}</p>
          ) : null}
        </div>
      ))}
    </div>
  );
}
