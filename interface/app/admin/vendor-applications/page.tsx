"use client";

import { useEffect, useState } from "react";
import { FileSearch } from "lucide-react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { RoleGuard } from "@/components/layout/RoleGuard";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { listAdminVendorApplications, updateAdminVendorApplication } from "@/lib/api/admin";
import type { PaginatedResponse, VendorApplication, VendorApplicationFilters } from "@/types/admin";

const STATUS_OPTIONS: { value: VendorApplication["status"]; label: string }[] = [
  { value: "pending", label: "در انتظار بررسی" },
  { value: "under_review", label: "در حال بررسی" },
  { value: "awaiting_info", label: "نیاز به اطلاعات بیشتر" },
  { value: "approved", label: "تأیید شده" },
  { value: "rejected", label: "رد شده" },
  { value: "cancelled", label: "لغو شده" },
];

const STATUS_BADGE: Record<VendorApplication["status"], string> = {
  pending: "bg-yellow-100 text-yellow-800",
  under_review: "bg-blue-100 text-blue-800",
  awaiting_info: "bg-orange-100 text-orange-800",
  approved: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  cancelled: "bg-gray-100 text-gray-700",
};

function statusLabel(status: VendorApplication["status"]) {
  return STATUS_OPTIONS.find((s) => s.value === status)?.label ?? status;
}

export default function AdminVendorApplicationsPage() {
  const [data, setData] = useState<PaginatedResponse<VendorApplication> | null>(null);
  const [filters, setFilters] = useState<VendorApplicationFilters>({ page: "1", page_size: "20" });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState<Record<number, boolean>>({});
  const [notes, setNotes] = useState<Record<number, string>>({});
  const [pendingStatus, setPendingStatus] = useState<Record<number, VendorApplication["status"]>>({});

  useEffect(() => {
    setData(null);
    setError("");
    listAdminVendorApplications(filters)
      .then(setData)
      .catch(() => setError("دریافت لیست درخواست‌های وندور با خطا مواجه شد."));
  }, [filters]);

  useEffect(() => {
    if (data) {
      const initNotes: Record<number, string> = {};
      const initStatus: Record<number, VendorApplication["status"]> = {};
      data.results.forEach((app) => {
        initNotes[app.id] = app.vendor_notes ?? "";
        initStatus[app.id] = app.status;
      });
      setNotes((prev) => ({ ...initNotes, ...prev }));
      setPendingStatus((prev) => ({ ...initStatus, ...prev }));
    }
  }, [data]);

  async function handleSave(app: VendorApplication) {
    setSaving((prev) => ({ ...prev, [app.id]: true }));
    try {
      const updated = await updateAdminVendorApplication(app.id, {
        status: pendingStatus[app.id] ?? app.status,
        vendor_notes: notes[app.id] ?? app.vendor_notes,
      });
      setData((prev) =>
        prev ? { ...prev, results: prev.results.map((a) => (a.id === updated.id ? updated : a)) } : prev
      );
    } catch {
      setError("ذخیره تغییرات با خطا مواجه شد.");
    } finally {
      setSaving((prev) => ({ ...prev, [app.id]: false }));
    }
  }

  const totalPages = data ? Math.ceil(data.count / (data.page_size || 20)) : 1;

  return (
    <RoleGuard roles={["admin"]}>
      <DashboardShell mode="admin" title="درخواست‌های وندور" description="مدیریت درخواست‌های ارسال‌شده توسط وندورها">
        {/* Filters */}
        <div className="mb-6 flex flex-wrap gap-3">
          <Select
            value={filters.status ?? ""}
            onChange={(e) =>
              setFilters((f) => ({ ...f, status: e.target.value || undefined, page: "1" }))
            }
            className="w-48"
          >
            <option value="">همه وضعیت‌ها</option>
            {STATUS_OPTIONS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </Select>
        </div>

        {error && (
          <p className="mb-4 rounded-lg bg-destructive/10 px-4 py-3 font-medium text-destructive">{error}</p>
        )}

        {!data ? (
          <div className="grid gap-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-32" />
            ))}
          </div>
        ) : data.results.length === 0 ? (
          <div className="flex flex-col items-center gap-3 py-20 text-muted-foreground">
            <FileSearch className="h-10 w-10" />
            <p>درخواستی یافت نشد.</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {data.results.map((app) => (
              <Card key={app.id}>
                <CardContent className="pt-5">
                  <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold">{app.vendor_name}</p>
                      <p className="text-sm text-muted-foreground">{app.vendor_service_title}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        ارسال: {new Date(app.submitted_at).toLocaleDateString("fa-IR")}
                      </p>
                    </div>
                    <span className={`rounded-full px-3 py-1 text-xs font-medium ${STATUS_BADGE[app.status]}`}>
                      {statusLabel(app.status)}
                    </span>
                  </div>

                  {app.user_notes ? (
                    <div className="mb-4 rounded-lg bg-muted/50 p-3 text-sm">
                      <span className="font-medium">یادداشت کاربر: </span>
                      {app.user_notes}
                    </div>
                  ) : null}

                  <div className="grid gap-3 sm:grid-cols-2">
                    <div>
                      <label className="mb-1 block text-xs font-medium text-muted-foreground">تغییر وضعیت</label>
                      <Select
                        value={pendingStatus[app.id] ?? app.status}
                        onChange={(e) =>
                          setPendingStatus((prev) => ({
                            ...prev,
                            [app.id]: e.target.value as VendorApplication["status"],
                          }))
                        }
                      >
                        {STATUS_OPTIONS.map((s) => (
                          <option key={s.value} value={s.value}>
                            {s.label}
                          </option>
                        ))}
                      </Select>
                    </div>
                    <div>
                      <label className="mb-1 block text-xs font-medium text-muted-foreground">یادداشت وندور</label>
                      <Textarea
                        rows={2}
                        value={notes[app.id] ?? app.vendor_notes ?? ""}
                        onChange={(e) => setNotes((prev) => ({ ...prev, [app.id]: e.target.value }))}
                        placeholder="یادداشت برای وندور..."
                      />
                    </div>
                  </div>

                  <div className="mt-3 flex justify-end">
                    <Button size="sm" onClick={() => handleSave(app)} disabled={saving[app.id]}>
                      {saving[app.id] ? "در حال ذخیره..." : "ذخیره تغییرات"}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}

            {totalPages > 1 && (
              <div className="mt-4 flex items-center justify-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={filters.page === "1"}
                  onClick={() =>
                    setFilters((f) => ({ ...f, page: String(Math.max(1, Number(f.page ?? 1) - 1)) }))
                  }
                >
                  قبلی
                </Button>
                <span className="text-sm text-muted-foreground">
                  صفحه {filters.page} از {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={Number(filters.page ?? 1) >= totalPages}
                  onClick={() =>
                    setFilters((f) => ({ ...f, page: String(Number(f.page ?? 1) + 1) }))
                  }
                >
                  بعدی
                </Button>
              </div>
            )}
          </div>
        )}
      </DashboardShell>
    </RoleGuard>
  );
}
