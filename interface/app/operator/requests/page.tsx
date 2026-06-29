"use client";

import { useEffect, useState } from "react";
import { AdminFilters } from "@/components/admin/AdminFilters";
import { AdminRequestTable } from "@/components/admin/AdminRequestTable";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { RoleGuard } from "@/components/layout/RoleGuard";
import { listAdminRequests } from "@/lib/api/admin";
import type { FinancingRequest } from "@/types/request";

export default function OperatorRequestsPage() {
  const [requests, setRequests] = useState<FinancingRequest[]>([]);
  function load(filters = {}) {
    listAdminRequests(filters).then((response) => setRequests(response.results)).catch(() => setRequests([]));
  }
  useEffect(() => load(), []);
  return (
    <RoleGuard roles={["admin", "operator"]}>
      <DashboardShell mode="operator" title="درخواست‌های اپراتور">
        <div className="grid gap-4">
          <AdminFilters onApply={load} />
          <AdminRequestTable requests={requests} basePath="/operator/requests" />
        </div>
      </DashboardShell>
    </RoleGuard>
  );
}
