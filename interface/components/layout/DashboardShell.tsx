import { AppSidebar } from "./AppSidebar";

export function DashboardShell({
  children,
  mode = "user",
  title,
  description,
  actions,
}: {
  children: React.ReactNode;
  mode?: "user" | "admin" | "operator";
  title?: string;
  description?: string;
  actions?: React.ReactNode;
}) {
  const hasHeader = Boolean(title);

  return (
    <main className="container py-6 lg:py-8">
      <div className="grid gap-6 lg:grid-cols-[256px_1fr]">
        <div className="hidden lg:block lg:min-w-0 lg:self-start">
          <AppSidebar mode={mode} className="sticky top-20" />
        </div>
        <section className="min-w-0">
          {hasHeader && (
            <div className="mb-6 flex flex-col gap-3 border-b pb-5 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <h1 className="text-2xl font-extrabold tracking-tight">{title}</h1>
                {description ? <p className="mt-1.5 text-sm text-muted-foreground">{description}</p> : null}
              </div>
              {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
            </div>
          )}
          <div className="animate-fade-in">{children}</div>
        </section>
      </div>
    </main>
  );
}
