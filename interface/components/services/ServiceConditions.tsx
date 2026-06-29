import { AlertTriangle, ShieldCheck } from "lucide-react";
import type { ServiceContent } from "@/types/service";

export function ServiceConditions({ contents }: { contents: ServiceContent[] }) {
  const items = contents.filter((content) => content.content_type === "conditions" || content.content_type === "warning");
  if (!items.length) return null;
  return (
    <section className="grid gap-3">
      <h2 className="flex items-center gap-2 text-lg font-bold">
        <ShieldCheck className="h-5 w-5 text-primary" />
        شرایط و هشدارها
      </h2>
      {items.map((content) => {
        const isWarning = content.content_type === "warning";
        return (
          <article
            key={content.id}
            className={
              isWarning
                ? "rounded-xl border border-warning/30 bg-warning/10 p-5"
                : "rounded-xl border bg-card p-5 shadow-card"
            }
          >
            <h3 className="flex items-center gap-2 font-bold">
              {isWarning ? <AlertTriangle className="h-4 w-4 text-[hsl(28_70%_38%)]" /> : null}
              {content.title}
            </h3>
            <div className="prose-content mt-1.5" dangerouslySetInnerHTML={{ __html: content.body }} />
          </article>
        );
      })}
    </section>
  );
}
