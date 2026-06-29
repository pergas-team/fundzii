"use client";

import { useCallback, useEffect, useState } from "react";
import { AdminFilters } from "@/components/admin/AdminFilters";
import { AdminRequestTable } from "@/components/admin/AdminRequestTable";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { RoleGuard } from "@/components/layout/RoleGuard";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { listAdminRequests } from "@/lib/api/admin";
import type { AdminRequestFilters } from "@/types/admin";
import type { FinancingRequest } from "@/types/request";

const DEFAULT_FILTERS: AdminRequestFilters = { page: "1", page_size: "10", ordering: "-submitted_at" };

export default function AdminRequestsPage() {
  const [requests, setRequests] = useState<FinancingRequest[]>([]);
  const [filters, setFilters] = useState<AdminRequestFilters>(DEFAULT_FILTERS);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback((nextFilters: AdminRequestFilters) => {
    setLoading(true);
    setError("");
    listAdminRequests(nextFilters)
      .then((response) => {
        setRequests(response.results);
        setCount(response.count);
        setFilters(nextFilters);
      })
      .catch(() => setError("دریافت درخواست‌ها با خطا مواجه شد."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => load(DEFAULT_FILTERS), [load]);

  const page = Number(filters.page || "1");
  const pageSize = Number(filters.page_size || "10");
  const totalPages = Math.max(Math.ceil(count / pageSize), 1);

  return (
    <RoleGuard roles={["admin"]}>
      <DashboardShell mode="admin" title="درخواست‌ها" description="بررسی، فیلتر و ارجاع درخواست‌های تأمین مالی">
        <div className="grid gap-4">
          <AdminFilters onApply={(next) => load({ ...next, page: "1", page_size: String(pageSize) })} />
          {error ? (
            <p className="rounded-lg bg-destructive/10 px-4 py-3 font-medium text-destructive">{error}</p>
          ) : loading ? (
            <Skeleton className="h-72" />
          ) : requests.length ? (
            <>
              <div className="overflow-hidden rounded-xl border bg-card shadow-card">
                <AdminRequestTable requests={requests} framed={false} />
              </div>
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border bg-card p-3 text-sm shadow-card">
                <span className="text-muted-foreground">
                  نمایش صفحه {page} از {totalPages}، مجموع {count} درخواست
                </span>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => load({ ...filters, page: String(page - 1) })}>
                    قبلی
                  </Button>
                  <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => load({ ...filters, page: String(page + 1) })}>
                    بعدی
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <p className="rounded-xl border bg-card p-8 text-center text-muted-foreground shadow-card">
              درخواستی با این فیلترها پیدا نشد.
            </p>
          )}
        </div>
      </DashboardShell>
    </RoleGuard>
  );
}
