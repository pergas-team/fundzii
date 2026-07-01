"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  Archive,
  BarChart2,
  CalendarDays,
  ClipboardList,
  FileStack,
  Landmark,
  TrendingUp,
  UsersRound,
} from "lucide-react";
import { AdminRequestTable } from "@/components/admin/AdminRequestTable";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { RoleGuard } from "@/components/layout/RoleGuard";
import { StatCard } from "@/components/dashboard/StatCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getAdminStats } from "@/lib/api/admin";
import { translateStatus } from "@/lib/utils/statusLabels";
import type { AdminStats } from "@/types/admin";

const STATUS_COLORS: Record<string, string> = {
  submitted: "bg-blue-500",
  initial_review: "bg-indigo-500",
  information_review: "bg-violet-500",
  property_document_review: "bg-purple-500",
  property_location_check: "bg-fuchsia-500",
  property_valuation: "bg-pink-500",
  legal_review: "bg-rose-500",
  valuation_required: "bg-orange-500",
  offer_preparation: "bg-amber-500",
  offer_sent: "bg-yellow-500",
  approved: "bg-emerald-500",
  rejected: "bg-red-500",
  needs_more_information: "bg-cyan-500",
};

const STATUS_BADGE: Record<string, string> = {
  submitted: "bg-blue-50 text-blue-700 border-blue-200",
  initial_review: "bg-indigo-50 text-indigo-700 border-indigo-200",
  information_review: "bg-violet-50 text-violet-700 border-violet-200",
  property_document_review: "bg-purple-50 text-purple-700 border-purple-200",
  offer_sent: "bg-yellow-50 text-yellow-700 border-yellow-200",
  approved: "bg-emerald-50 text-emerald-700 border-emerald-200",
  rejected: "bg-red-50 text-red-700 border-red-200",
  needs_more_information: "bg-cyan-50 text-cyan-700 border-cyan-200",
};

const QUICK_LINKS = [
  { href: "/admin/requests", label: "مدیریت درخواست‌ها", icon: ClipboardList, color: "text-blue-600 bg-blue-50 border-blue-200" },
  { href: "/admin/vendor-applications", label: "درخواست‌های وندور", icon: FileStack, color: "text-violet-600 bg-violet-50 border-violet-200" },
  { href: "/admin/reports", label: "گزارش‌ها و آمار", icon: BarChart2, color: "text-emerald-600 bg-emerald-50 border-emerald-200" },
  { href: "/admin/services", label: "خدمات مالی", icon: Landmark, color: "text-orange-600 bg-orange-50 border-orange-200" },
];

export default function AdminHomePage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getAdminStats().then(setStats).catch(() => setError("دریافت آمار داشبورد با خطا مواجه شد."));
  }, []);

  const maxStatus = Math.max(...(stats?.by_status.map((item) => item.count) || [1]));
  const maxService = Math.max(...(stats?.by_service.map((item) => item.count) || [1]));
  const total = stats?.total_requests || 1;

  return (
    <RoleGuard roles={["admin"]}>
      <DashboardShell mode="admin" title="داشبورد مدیریتی" description="نمای کلی درخواست‌ها و سرویس‌های فاندزی">
        {error ? (
          <p className="rounded-lg bg-destructive/10 px-4 py-3 font-medium text-destructive">{error}</p>
        ) : !stats ? (
          <div className="grid gap-6">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
              {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-28" />)}
            </div>
            <div className="grid gap-4 lg:grid-cols-4">
              {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-24" />)}
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
              <Skeleton className="h-72" />
              <Skeleton className="h-72" />
            </div>
            <Skeleton className="h-64" />
          </div>
        ) : (
          <div className="grid gap-6">
            {/* ── KPI Strip ── */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
              <StatCard title="کل درخواست‌ها" value={stats.total_requests} icon={ClipboardList} tone="primary" />
              <StatCard title="امروز" value={stats.today_requests} icon={CalendarDays} tone="accent" />
              <StatCard title="۷ روز اخیر" value={stats.last_7_days_requests} icon={TrendingUp} tone="info" />
              <StatCard title="بایگانی‌شده" value={stats.archived_requests} icon={Archive} tone="warning" />
              <StatCard title="کاربران ثبت‌نامی" value={stats.users_count} icon={UsersRound} tone="success" />
            </div>

            {/* ── Quick Actions ── */}
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {QUICK_LINKS.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`flex items-center gap-3 rounded-xl border p-4 transition-all hover:-translate-y-0.5 hover:shadow-md ${link.color}`}
                >
                  <span className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-white/70 shadow-sm">
                    <link.icon className="h-5 w-5" />
                  </span>
                  <span className="text-sm font-semibold">{link.label}</span>
                </Link>
              ))}
            </div>

            {/* ── Charts Row ── */}
            <div className="grid gap-4 lg:grid-cols-2">
              {/* Status Breakdown */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center gap-2 text-sm font-bold">
                    <span className="h-3 w-3 rounded-full bg-gradient-primary" />
                    تفکیک بر اساس وضعیت
                  </CardTitle>
                </CardHeader>
                <CardContent className="grid gap-3">
                  {stats.by_status.map((item) => {
                    const pct = Math.max((item.count / maxStatus) * 100, 2);
                    const share = ((item.count / total) * 100).toFixed(1);
                    const bar = STATUS_COLORS[item.current_status] ?? "bg-primary";
                    const badge = STATUS_BADGE[item.current_status] ?? "bg-muted text-muted-foreground border-transparent";
                    return (
                      <div key={item.current_status} className="grid gap-1">
                        <div className="flex items-center justify-between gap-2">
                          <span className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${badge}`}>
                            {translateStatus(item.current_status)}
                          </span>
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <span className="font-bold text-foreground">{item.count}</span>
                            <span>({share}٪)</span>
                          </div>
                        </div>
                        <div className="h-2 overflow-hidden rounded-full bg-muted">
                          <div className={`h-full rounded-full transition-all ${bar}`} style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>

              {/* Service Breakdown */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center gap-2 text-sm font-bold">
                    <span className="h-3 w-3 rounded-full bg-emerald-500" />
                    تفکیک بر اساس سرویس
                  </CardTitle>
                </CardHeader>
                <CardContent className="grid gap-3">
                  {stats.by_service.map((item, idx) => {
                    const pct = Math.max((item.count / maxService) * 100, 2);
                    const share = ((item.count / total) * 100).toFixed(1);
                    const EMERALD_SHADES = [
                      "bg-emerald-600", "bg-teal-500", "bg-cyan-500",
                      "bg-emerald-400", "bg-teal-400", "bg-cyan-400",
                    ];
                    const bar = EMERALD_SHADES[idx % EMERALD_SHADES.length];
                    return (
                      <div key={item.slug} className="grid gap-1">
                        <div className="flex items-center justify-between gap-2">
                          <span className="max-w-[60%] truncate text-sm font-medium">{item.title}</span>
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <span className="font-bold text-foreground">{item.count}</span>
                            <span>({share}٪)</span>
                          </div>
                        </div>
                        <div className="h-2 overflow-hidden rounded-full bg-muted">
                          <div className={`h-full rounded-full transition-all ${bar}`} style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>
            </div>

            {/* ── Latest Requests ── */}
            <Card>
              <CardHeader className="flex-row items-center justify-between pb-3">
                <CardTitle className="text-sm font-bold">آخرین درخواست‌ها</CardTitle>
                <Button asChild variant="outline" size="sm">
                  <Link href="/admin/requests">مشاهده همه</Link>
                </Button>
              </CardHeader>
              <CardContent>
                {stats.latest_requests.length ? (
                  <AdminRequestTable requests={stats.latest_requests} framed={false} />
                ) : (
                  <p className="py-8 text-center text-sm text-muted-foreground">هنوز درخواستی ثبت نشده است.</p>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </DashboardShell>
    </RoleGuard>
  );
}
