import { FileText } from "lucide-react";
import type { ServiceContent } from "@/types/service";

export function RequiredDocuments({ contents }: { contents: ServiceContent[] }) {
  const items = contents.filter((content) => content.content_type === "required_documents");
  if (!items.length) return null;
  return (
    <section className="grid gap-3">
      <h2 className="flex items-center gap-2 text-lg font-bold">
        <FileText className="h-5 w-5 text-primary" />
        مدارک مورد نیاز
      </h2>
      {items.map((content) => (
        <article
          key={content.id}
          className="flex gap-3 rounded-xl border bg-card p-5 text-sm leading-7 text-muted-foreground shadow-card"
        >
          <span className="mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary">
            <FileText className="h-4 w-4" />
          </span>
          <div className="prose-content flex-1" dangerouslySetInnerHTML={{ __html: content.body }} />
        </article>
      ))}
    </section>
  );
}
