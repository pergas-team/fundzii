"use client";

import { useEffect, useState } from "react";
import { BarChart2, Download, TrendingUp, Users } from "lucide-react";
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

const FUNNEL_LABELS: Record<string, string> = {
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

const FUNNEL_BAR: Record<string, string> = {
  pending: "bg-yellow-400",
  under_review: "bg-blue-500",
  awaiting_info: "bg-orange-400",
  approved: "bg-emerald-500",
  rejected: "bg-red-500",
  cancelled: "bg-gray-400",
  submitted: "bg-indigo-500",
  assigned: "bg-violet-500",
  offer_received: "bg-amber-500",
  completed: "bg-teal-500",
  archived: "bg-slate-400",
};

const FUNNEL_BADGE: Record<string, string> = {
  pending: "bg-yellow-50 text-yellow-700 border-yellow-200",
  under_review: "bg-blue-50 text-blue-700 border-blue-200",
  awaiting_info: "bg-orange-50 text-orange-700 border-orange-200",
  approved: "bg-emerald-50 text-emerald-700 border-emerald-200",
  rejected: "bg-red-50 text-red-700 border-red-200",
  cancelled: "bg-gray-100 text-gray-600 border-gray-200",
  submitted: "bg-indigo-50 text-indigo-700 border-indigo-200",
  assigned: "bg-violet-50 text-violet-700 border-violet-200",
  offer_received: "bg-amber-50 text-amber-700 border-amber-200",
  completed: "bg-teal-50 text-teal-700 border-teal-200",
  archived: "bg-slate-100 text-slate-600 border-slate-200",
};

function rateColor(rate: number) {
  if (rate >= 0.7) return "text-emerald-600";
  if (rate >= 0.4) return "text-amber-600";
  return "text-red-500";
}

function rateBar(rate: number) {
  if (rate >= 0.7) return "bg-emerald-500";
  if (rate >= 0.4) return "bg-amber-400";
  return "bg-red-400";
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

  const funnelTotal = funnel?.reduce((s, r) => s + r.count, 0) ?? 0;
  const funnelMax = Math.max(...(funnel?.map((r) => r.count) || [1]));
  const monthlyMax = Math.max(...(monthly?.map((r) => r.total_requests) || [1]));

  const summaryCards = [
    {
      label: "کل درخواست‌ها (قیف)",
      value: funnelTotal,
      icon: BarChart2,
      color: "text-blue-600 bg-blue-50",
    },
    {
      label: "تعداد پارتنرها",
      value: partner?.length ?? "—",
      icon: Users,
      color: "text-violet-600 bg-violet-50",
    },
    {
      label: "میانگین نرخ پذیرش",
      value:
        partner && partner.length
          ? `${((partner.reduce((s, p) => s + p.acceptance_rate, 0) / partner.length) * 100).toFixed(1)}٪`
          : "—",
      icon: TrendingUp,
      color: "text-emerald-600 bg-emerald-50",
    },
  ];

  return (
    <RoleGuard roles={["admin"]}>
      <DashboardShell mode="admin" title="گزارش‌ها" description="آمار و گزارش‌های عملکردی پلتفرم">
        {error && (
          <p className="mb-6 rounded-lg bg-destructive/10 px-4 py-3 font-medium text-destructive">{error}</p>
        )}

        {/* ── Summary KPIs ── */}
        <div className="mb-6 grid gap-4 sm:grid-cols-3">
          {summaryCards.map((c) => (
            <div key={c.label} className="flex items-center gap-4 rounded-xl border bg-card p-5 shadow-card">
              <span className={`grid h-11 w-11 shrink-0 place-items-center rounded-xl ${c.color}`}>
                <c.icon className="h-5 w-5" />
              </span>
              <div>
                <p className="text-xs text-muted-foreground">{c.label}</p>
                <p className="mt-0.5 text-2xl font-extrabold tracking-tight">
                  {funnel && partner && monthly ? c.value : <Skeleton className="h-6 w-16" />}
                </p>
              </div>
            </div>
          ))}
        </div>

        <div className="grid gap-6">
          {/* ── Funnel Report ── */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <div>
                <CardTitle className="text-base font-bold">قیف درخواست‌ها</CardTitle>
                <p className="mt-0.5 text-xs text-muted-foreground">توزیع درخواست‌ها بر اساس وضعیت</p>
              </div>
              <Button variant="outline" size="sm" onClick={() => downloadCsv("funnel")}>
                <Download className="h-3.5 w-3.5" />
                دریافت CSV
              </Button>
            </CardHeader>
            <CardContent>
              {!funnel ? (
                <div className="grid gap-3">
                  {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10" />)}
                </div>
              ) : funnel.length === 0 ? (
                <p className="py-6 text-center text-sm text-muted-foreground">داده‌ای موجود نیست.</p>
              ) : (
                <div className="grid gap-3">
                  {funnel.map((row) => {
                    const pct = Math.max((row.count / funnelMax) * 100, 2);
                    const share = funnelTotal ? ((row.count / funnelTotal) * 100).toFixed(1) : "0";
                    const bar = FUNNEL_BAR[row.status] ?? "bg-primary";
                    const badge = FUNNEL_BADGE[row.status] ?? "bg-muted text-muted-foreground border-transparent";
                    return (
                      <div key={row.status} className="grid gap-1">
                        <div className="flex items-center justify-between gap-2">
                          <span className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${badge}`}>
                            {FUNNEL_LABELS[row.status] ?? row.status}
                          </span>
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <span className="font-bold text-foreground">{row.count.toLocaleString("fa-IR")}</span>
                            <span className="tabular-nums">({share}٪)</span>
                          </div>
                        </div>
                        <div className="h-2.5 overflow-hidden rounded-full bg-muted">
                          <div className={`h-full rounded-full transition-all ${bar}`} style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>

          {/* ── Partner Performance ── */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <div>
                <CardTitle className="text-base font-bold">عملکرد پارتنرها</CardTitle>
                <p className="mt-0.5 text-xs text-muted-foreground">مقایسه درخواست‌ها، پیشنهادها و نرخ پذیرش</p>
              </div>
              <Button variant="outline" size="sm" onClick={() => downloadCsv("partner-performance")}>
                <Download className="h-3.5 w-3.5" />
                دریافت CSV
              </Button>
            </CardHeader>
            <CardContent>
              {!partner ? (
                <div className="grid gap-3">
                  {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-12" />)}
                </div>
              ) : partner.length === 0 ? (
                <p className="py-6 text-center text-sm text-muted-foreground">داده‌ای موجود نیست.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-right text-xs text-muted-foreground">
                        <th className="pb-3 font-medium">پارتنر</th>
                        <th className="pb-3 font-medium">تخصیص‌یافته</th>
                        <th className="pb-3 font-medium">پیشنهادها</th>
                        <th className="pb-3 font-medium">پذیرفته‌شده</th>
                        <th className="pb-3 font-medium">نرخ پذیرش</th>
                      </tr>
                    </thead>
                    <tbody>
                      {partner
                        .slice()
                        .sort((a, b) => b.acceptance_rate - a.acceptance_rate)
                        .map((row) => {
                          const rate = row.acceptance_rate;
                          const ratePct = (rate * 100).toFixed(1);
                          return (
                            <tr key={row.partner_id} className="border-b last:border-0 hover:bg-muted/30">
                              <td className="py-3 font-semibold">{row.partner_name}</td>
                              <td className="py-3 tabular-nums">{row.assigned_requests.toLocaleString("fa-IR")}</td>
                              <td className="py-3 tabular-nums">{row.offers_submitted.toLocaleString("fa-IR")}</td>
                              <td className="py-3 tabular-nums">{row.offers_accepted.toLocaleString("fa-IR")}</td>
                              <td className="py-3">
                                <div className="flex items-center gap-2">
                                  <div className="h-1.5 w-16 overflow-hidden rounded-full bg-muted">
                                    <div
                                      className={`h-full rounded-full ${rateBar(rate)}`}
                                      style={{ width: `${Math.min(rate * 100, 100)}%` }}
                                    />
                                  </div>
                                  <span className={`tabular-nums font-bold ${rateColor(rate)}`}>{ratePct}٪</span>
                                </div>
                              </td>
                            </tr>
                          );
                        })}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {/* ── Monthly Report ── */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <div>
                <CardTitle className="text-base font-bold">گزارش ماهانه</CardTitle>
                <p className="mt-0.5 text-xs text-muted-foreground">تعداد درخواست‌ها به تفکیک ماه</p>
              </div>
              <Button variant="outline" size="sm" onClick={() => downloadCsv("monthly")}>
                <Download className="h-3.5 w-3.5" />
                دریافت CSV
              </Button>
            </CardHeader>
            <CardContent>
              {!monthly ? (
                <div className="grid gap-3">
                  {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-10" />)}
                </div>
              ) : monthly.length === 0 ? (
                <p className="py-6 text-center text-sm text-muted-foreground">داده‌ای موجود نیست.</p>
              ) : (
                <div className="grid gap-2.5">
                  {monthly
                    .slice()
                    .reverse()
                    .map((row, idx) => {
                      const pct = Math.max((row.total_requests / monthlyMax) * 100, 2);
                      const isLatest = idx === 0;
                      return (
                        <div key={row.month} className="flex items-center gap-3">
                          <span className={`w-20 shrink-0 text-xs font-medium tabular-nums ${isLatest ? "text-blue-600" : "text-muted-foreground"}`}>
                            {row.month}
                          </span>
                          <div className="flex-1 overflow-hidden rounded-full bg-muted" style={{ height: 10 }}>
                            <div
                              className={`h-full rounded-full transition-all ${isLatest ? "bg-blue-500" : "bg-primary/60"}`}
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                          <span className={`w-12 text-left text-xs font-bold tabular-nums ${isLatest ? "text-blue-600" : "text-foreground"}`}>
                            {row.total_requests.toLocaleString("fa-IR")}
                          </span>
                        </div>
                      );
                    })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </DashboardShell>
    </RoleGuard>
  );
}
