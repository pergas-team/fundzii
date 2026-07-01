"use client";

import { useEffect, useState } from "react";
import { Download } from "lucide-react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { RoleGuard } from "@/components/layout/RoleGuard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  getAdminReportCsvUrl,
  getAdminReportFunnel,
  getAdminReportMonthly,
  getAdminReportPartnerPerformance,
} from "@/lib/api/admin";
import type { ReportFunnelItem, ReportMonthly, ReportPartnerPerformance } from "@/types/admin";

const FUNNEL_STATUS_LABELS: Record<string, string> = {
  pending: "در انتظار بررسی",
  under_review: "در حال بررسی",
  awaiting_info: "نیاز به اطلاعات بیشتر",
  approved: "تأیید شده",
  rejected: "رد شده",
  cancelled: "لغو شده",
  submitted: "ثبت‌شده",
  assigned: "تخصیص‌یافته",
  offer_received: "پیشنهاد دریافت‌شده",
  completed: "تکمیل‌شده",
  archived: "بایگانی‌شده",
};

function statusLabel(status: string) {
  return FUNNEL_STATUS_LABELS[status] ?? status;
}

function downloadCsv(report: "funnel" | "partner-performance" | "monthly") {
  window.open(getAdminReportCsvUrl(report), "_blank");
}

export default function AdminReportsPage() {
  const [funnel, setFunnel] = useState<ReportFunnelItem[] | null>(null);
  const [partner, setPartner] = useState<ReportPartnerPerformance[] | null>(null);
  const [monthly, setMonthly] = useState<ReportMonthly[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      getAdminReportFunnel().then((r) => setFunnel(r.results)),
      getAdminReportPartnerPerformance().then((r) => setPartner(r.results)),
      getAdminReportMonthly().then((r) => setMonthly(r.results)),
    ]).catch(() => setError("دریافت گزارش‌ها با خطا مواجه شد."));
  }, []);

  return (
    <RoleGuard roles={["admin"]}>
      <DashboardShell mode="admin" title="گزارش‌ها" description="آمار و گزارش‌های عملکردی پلتفرم">
        {error && (
          <p className="mb-6 rounded-lg bg-destructive/10 px-4 py-3 font-medium text-destructive">{error}</p>
        )}

        <div className="grid gap-6">
          {/* Funnel Report */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <CardTitle className="text-base font-bold">قیف درخواست‌ها</CardTitle>
              <Button variant="outline" size="sm" onClick={() => downloadCsv("funnel")}>
                <Download className="h-3.5 w-3.5" />
                دریافت CSV
              </Button>
            </CardHeader>
            <CardContent>
              {!funnel ? (
                <div className="grid gap-2">
                  {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-8" />)}
                </div>
              ) : funnel.length === 0 ? (
                <p className="text-sm text-muted-foreground">داده‌ای موجود نیست.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-right text-muted-foreground">
                        <th className="pb-2 font-medium">وضعیت</th>
                        <th className="pb-2 font-medium">تعداد</th>
                      </tr>
                    </thead>
                    <tbody>
                      {funnel.map((row) => (
                        <tr key={row.status} className="border-b last:border-0">
                          <td className="py-2">{statusLabel(row.status)}</td>
                          <td className="py-2 font-semibold">{row.count.toLocaleString("fa-IR")}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Partner Performance */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <CardTitle className="text-base font-bold">عملکرد پارتنرها</CardTitle>
              <Button variant="outline" size="sm" onClick={() => downloadCsv("partner-performance")}>
                <Download className="h-3.5 w-3.5" />
                دریافت CSV
              </Button>
            </CardHeader>
            <CardContent>
              {!partner ? (
                <div className="grid gap-2">
                  {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-8" />)}
                </div>
              ) : partner.length === 0 ? (
                <p className="text-sm text-muted-foreground">داده‌ای موجود نیست.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-right text-muted-foreground">
                        <th className="pb-2 font-medium">پارتنر</th>
                        <th className="pb-2 font-medium">تخصیص‌یافته</th>
                        <th className="pb-2 font-medium">پیشنهادها</th>
                        <th className="pb-2 font-medium">پذیرفته‌شده</th>
                        <th className="pb-2 font-medium">نرخ پذیرش</th>
                      </tr>
                    </thead>
                    <tbody>
                      {partner.map((row) => (
                        <tr key={row.partner_id} className="border-b last:border-0">
                          <td className="py-2 font-medium">{row.partner_name}</td>
                          <td className="py-2">{row.assigned_requests.toLocaleString("fa-IR")}</td>
                          <td className="py-2">{row.offers_submitted.toLocaleString("fa-IR")}</td>
                          <td className="py-2">{row.offers_accepted.toLocaleString("fa-IR")}</td>
                          <td className="py-2">
                            <span className="font-semibold text-emerald-600">
                              {(row.acceptance_rate * 100).toFixed(1)}٪
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Monthly Report */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <CardTitle className="text-base font-bold">گزارش ماهانه</CardTitle>
              <Button variant="outline" size="sm" onClick={() => downloadCsv("monthly")}>
                <Download className="h-3.5 w-3.5" />
                دریافت CSV
              </Button>
            </CardHeader>
            <CardContent>
              {!monthly ? (
                <div className="grid gap-2">
                  {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-8" />)}
                </div>
              ) : monthly.length === 0 ? (
                <p className="text-sm text-muted-foreground">داده‌ای موجود نیست.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-right text-muted-foreground">
                        <th className="pb-2 font-medium">ماه</th>
                        <th className="pb-2 font-medium">تعداد درخواست‌ها</th>
                      </tr>
                    </thead>
                    <tbody>
                      {monthly.map((row) => (
                        <tr key={row.month} className="border-b last:border-0">
                          <td className="py-2">{row.month}</td>
                          <td className="py-2 font-semibold">{row.total_requests.toLocaleString("fa-IR")}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </DashboardShell>
    </RoleGuard>
  );
}
