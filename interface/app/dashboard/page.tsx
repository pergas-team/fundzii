"use client";

import Link from "next/link";
import {
  ArrowLeft,
  CheckCircle2,
  ClipboardList,
  Clock,
  FileText,
  Landmark,
  Plus,
  TrendingUp,
  User,
  type LucideIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { RoleGuard } from "@/components/layout/RoleGuard";
import { RequestList } from "@/components/requests/RequestList";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { useRequests } from "@/hooks/useRequests";
import { cn } from "@/lib/utils";

// Stat cell — same visual pattern as ServiceCell on services page
function StatCell({
  icon: Icon,
  value,
  label,
  iconClass,
  valueClass,
}: {
  icon: LucideIcon;
  value: number;
  label: string;
  iconClass: string;
  valueClass: string;
}) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-xl border bg-background px-3 py-4 text-center">
      <Icon className={cn("h-6 w-6", iconClass)} strokeWidth={1.5} />
      <span className={cn("text-2xl font-extrabold leading-none tracking-tight", valueClass)}>{value}</span>
      <span className="text-xs font-medium leading-[1.35] text-muted-foreground">{label}</span>
    </div>
  );
}

// Quick action cell — exact same as ServiceCell on services page
function ActionCell({
  href,
  label,
  icon: Icon,
  iconClass,
}: {
  href: string;
  label: string;
  icon: LucideIcon;
  iconClass: string;
}) {
  return (
    <Link
      href={href}
      className="group flex flex-col items-center gap-2.5 rounded-xl border bg-background px-3 py-4 text-center transition-all duration-200 hover:border-current/20 hover:bg-muted/50 hover:shadow-sm active:scale-[0.97]"
    >
      <Icon
        className={cn("h-7 w-7 transition-transform duration-200 group-hover:scale-110", iconClass)}
        strokeWidth={1.5}
      />
      <span className="text-xs font-medium leading-[1.35] text-foreground">{label}</span>
    </Link>
  );
}

function GridSkeleton({ count }: { count: number }) {
  return (
    <div className="grid gap-3" style={{ gridTemplateColumns: `repeat(${count}, 1fr)` }}>
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} className="h-20 rounded-xl" />
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useCurrentUser();
  const { requests, isLoading } = useRequests();
  const recent = requests.slice(0, 3);
  const inReview = requests.filter(
    (r) => r.current_status !== "approved" && r.current_status !== "rejected"
  ).length;
  const approved = requests.filter((r) => r.current_status === "approved").length;

  return (
    <RoleGuard roles={["applicant", "investor", "vendor", "admin", "operator"]}>
      <DashboardShell>
        <div className="grid gap-5">
          {/* Page header — same centered pattern as services page */}
          <div className="mb-3 text-center">
            <h1 className="text-2xl font-extrabold tracking-tight md:text-3xl">داشبورد</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              خوش آمدید {user?.first_name || user?.phone_number || ""}
            </p>
          </div>

          {/* Two panels — exact same pattern as services page */}
          <div className="grid grid-cols-2 gap-5">
            {/* Stats panel — blue (like تامین مالی panel) */}
            <div className="rounded-2xl border-2 border-blue-400 bg-card p-6 dark:border-blue-500">
              <div className="mb-5 text-center">
                <h2 className="text-lg font-bold text-blue-600 dark:text-blue-400">وضعیت درخواست‌ها</h2>
                <p className="mt-1 text-xs text-muted-foreground">خلاصه پرونده‌های ثبت‌شده</p>
              </div>
              {isLoading ? (
                <GridSkeleton count={3} />
              ) : (
                <div className="grid grid-cols-3 gap-3">
                  <StatCell
                    icon={ClipboardList}
                    value={requests.length}
                    label="کل درخواست‌ها"
                    iconClass="text-blue-500"
                    valueClass="text-blue-600 dark:text-blue-400"
                  />
                  <StatCell
                    icon={Clock}
                    value={inReview}
                    label="در حال بررسی"
                    iconClass="text-amber-500"
                    valueClass="text-amber-600 dark:text-amber-400"
                  />
                  <StatCell
                    icon={CheckCircle2}
                    value={approved}
                    label="تأیید شده"
                    iconClass="text-emerald-500"
                    valueClass="text-emerald-600 dark:text-emerald-400"
                  />
                </div>
              )}
            </div>

            {/* Quick actions panel — emerald (like سرمایه‌گذاری panel) */}
            <div className="rounded-2xl border-2 border-emerald-400 bg-card p-6 dark:border-emerald-500">
              <div className="mb-5 text-center">
                <h2 className="text-lg font-bold text-emerald-600 dark:text-emerald-400">دسترسی سریع</h2>
                <p className="mt-1 text-xs text-muted-foreground">مسیرهای پرکاربرد</p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <ActionCell href="/services" label="خدمات مالی" icon={TrendingUp} iconClass="text-blue-500" />
                <ActionCell href="/dashboard/requests" label="درخواست‌ها" icon={FileText} iconClass="text-emerald-500" />
                <ActionCell href="/services" label="درخواست جدید" icon={Plus} iconClass="text-amber-500" />
                <ActionCell href="/dashboard/profile" label="پروفایل من" icon={User} iconClass="text-primary" />
              </div>
            </div>
          </div>

          {/* Recent requests — same bottom section pattern as services page */}
          <div className="rounded-2xl border bg-card p-6">
            <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <Landmark className="h-5 w-5 shrink-0 text-muted-foreground" strokeWidth={1.5} />
                <div>
                  <h2 className="text-base font-bold">آخرین درخواست‌ها</h2>
                  <p className="mt-0.5 text-xs text-muted-foreground">آخرین وضعیت پرونده‌های ثبت‌شده شما</p>
                </div>
              </div>
              <Button asChild variant="ghost" size="sm">
                <Link href="/dashboard/requests">
                  همه درخواست‌ها
                  <ArrowLeft className="h-4 w-4" />
                </Link>
              </Button>
            </div>
            {isLoading ? (
              <div className="grid gap-3">
                <Skeleton className="h-24 rounded-xl" />
                <Skeleton className="h-24 rounded-xl" />
              </div>
            ) : (
              <RequestList requests={recent} />
            )}
          </div>
        </div>
      </DashboardShell>
    </RoleGuard>
  );
}
