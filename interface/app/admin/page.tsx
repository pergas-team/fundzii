"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Archive, CalendarDays, ClipboardList, TrendingUp, UsersRound } from "lucide-react";
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

export default function AdminHomePage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getAdminStats().then(setStats).catch(() => setError("دریافت آمار داشبورد با خطا مواجه شد."));
  }, []);

  const maxStatus = Math.max(...(stats?.by_status.map((item) => item.count) || [1]));
  const maxService = Math.max(...(stats?.by_service.map((item) => item.count) || [1]));

  return (
    <RoleGuard roles={["admin"]}>
      <DashboardShell mode="admin" title="داشبورد مدیریتی" description="نمای کلی درخواست‌ها و سرویس‌های فاندزی">
        {error ? (
          <p className="rounded-lg bg-destructive/10 px-4 py-3 font-medium text-destructive">{error}</p>
        ) : !stats ? (
          <div className="grid gap-6">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {Array.from({ length: 4 }).map((_, index) => (
                <Skeleton key={index} className="h-28" />
              ))}
            </div>
            <Skeleton className="h-64" />
          </div>
        ) : (
          <div className="grid gap-6">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
              <StatCard title="کل درخواست‌ها" value={stats.total_requests} icon={ClipboardList} tone="primary" />
              <StatCard title="درخواست‌های امروز" value={stats.today_requests} icon={CalendarDays} tone="accent" />
              <StatCard title="۷ روز اخیر" value={stats.last_7_days_requests} icon={TrendingUp} tone="info" />
              <StatCard title="بایگانی‌شده" value={stats.archived_requests} icon={Archive} tone="warning" />
              <StatCard title="کاربران" value={stats.users_count} icon={UsersRound} tone="success" />
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>تفکیک وضعیت‌ها</CardTitle>
                </CardHeader>
                <CardContent className="grid gap-3.5">
                  {stats.by_status.map((item) => (
                    <div key={item.current_status} className="grid gap-1.5">
                      <div className="flex justify-between text-sm">
                        <span className="font-medium">{translateStatus(item.current_status)}</span>
                        <span className="font-bold text-muted-foreground">{item.count}</span>
                      </div>
                      <div className="h-2.5 overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full rounded-full bg-gradient-primary transition-all"
                          style={{ width: `${Math.max((item.count / maxStatus) * 100, 4)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>تفکیک سرویس‌ها</CardTitle>
                </CardHeader>
                <CardContent className="grid gap-3.5">
                  {stats.by_service.map((item) => (
                    <div key={item.slug} className="grid gap-1.5">
                      <div className="flex justify-between text-sm">
                        <span className="font-medium">{item.title}</span>
                        <span className="font-bold text-muted-foreground">{item.count}</span>
                      </div>
                      <div className="h-2.5 overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full rounded-full bg-gradient-accent transition-all"
                          style={{ width: `${Math.max((item.count / maxService) * 100, 4)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader className="flex-row items-center justify-between">
                <CardTitle>آخرین درخواست‌ها</CardTitle>
                <Button asChild variant="outline" size="sm">
                  <Link href="/admin/requests">همه درخواست‌ها</Link>
                </Button>
              </CardHeader>
              <CardContent>
                {stats.latest_requests.length ? (
                  <AdminRequestTable requests={stats.latest_requests} framed={false} />
                ) : (
                  <p className="text-muted-foreground">هنوز درخواستی ثبت نشده است.</p>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </DashboardShell>
    </RoleGuard>
  );
}
