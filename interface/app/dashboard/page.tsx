"use client";

import Link from "next/link";
import { CheckCircle2, ClipboardList, Clock, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { RoleGuard } from "@/components/layout/RoleGuard";
import { StatCard } from "@/components/dashboard/StatCard";
import { RequestList } from "@/components/requests/RequestList";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { useRequests } from "@/hooks/useRequests";

export default function DashboardPage() {
  const { user } = useCurrentUser();
  const { requests, isLoading } = useRequests();
  const recent = requests.slice(0, 3);
  const inReview = requests.filter((item) => item.current_status !== "approved" && item.current_status !== "rejected").length;
  const approved = requests.filter((item) => item.current_status === "approved").length;

  return (
    <RoleGuard roles={["applicant", "investor", "vendor", "admin", "operator"]}>
      <DashboardShell
        title="داشبورد"
        description={`خوش آمدید ${user?.first_name || user?.phone_number || ""}`}
        actions={
          <Button asChild>
            <Link href="/services">
              <Plus className="h-4 w-4" />
              ثبت درخواست جدید
            </Link>
          </Button>
        }
      >
        <div className="grid gap-6">
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard title="کل درخواست‌ها" value={requests.length} icon={ClipboardList} tone="primary" />
            <StatCard title="در حال بررسی" value={inReview} icon={Clock} tone="warning" />
            <StatCard title="تأیید شده" value={approved} icon={CheckCircle2} tone="success" />
          </div>

          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold">آخرین درخواست‌ها</h2>
            <Button asChild variant="ghost" size="sm">
              <Link href="/dashboard/requests">همه درخواست‌ها</Link>
            </Button>
          </div>

          {isLoading ? (
            <div className="grid gap-4">
              <Skeleton className="h-24" />
              <Skeleton className="h-24" />
            </div>
          ) : (
            <RequestList requests={recent} />
          )}
        </div>
      </DashboardShell>
    </RoleGuard>
  );
}
