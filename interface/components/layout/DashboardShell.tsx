import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
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
    <SidebarProvider>
      <AppSidebar mode={mode} />
      <SidebarInset>
        <div className="container py-6 lg:py-8">
          {/* Mobile sidebar trigger — always visible on small screens */}
          {!hasHeader && (
            <div className="mb-4 flex items-center lg:hidden">
              <SidebarTrigger />
            </div>
          )}
          {hasHeader && (
            <div className="mb-6 flex flex-col gap-3 border-b pb-5 sm:flex-row sm:items-end sm:justify-between">
              <div className="flex items-center gap-3">
                <SidebarTrigger className="lg:hidden" />
                <div>
                  <h1 className="text-2xl font-extrabold tracking-tight">{title}</h1>
                  {description ? (
                    <p className="mt-1.5 text-sm text-muted-foreground">{description}</p>
                  ) : null}
                </div>
              </div>
              {actions ? (
                <div className="flex flex-wrap items-center gap-2">{actions}</div>
              ) : null}
            </div>
          )}
          <div className="animate-fade-in">{children}</div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
