"use client";

import { DashboardShell } from "@/components/layout/DashboardShell";
import { RoleGuard } from "@/components/layout/RoleGuard";
import { RequestList } from "@/components/requests/RequestList";
import { useRequests } from "@/hooks/useRequests";

export default function MyRequestsPage() {
  const { requests, isLoading, error } = useRequests();
  return (
    <RoleGuard roles={["applicant", "investor", "vendor", "admin", "operator"]}>
      <DashboardShell title="درخواست‌های من" description="درخواست‌های ثبت‌شده و وضعیت جاری آن‌ها">
        {isLoading ? <p className="text-muted-foreground">در حال بارگذاری...</p> : error ? <p className="text-destructive">{error}</p> : <RequestList requests={requests} />}
      </DashboardShell>
    </RoleGuard>
  );
}
