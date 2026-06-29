import { DashboardShell } from "@/components/layout/DashboardShell";
import { RoleGuard } from "@/components/layout/RoleGuard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function OperatorHomePage() {
  return (
    <RoleGuard roles={["admin", "operator"]}>
      <DashboardShell mode="operator" title="داشبورد اپراتور">
        <Card><CardHeader><CardTitle>بررسی عملیاتی</CardTitle></CardHeader><CardContent className="text-muted-foreground">برای مشاهده درخواست‌های قابل بررسی وارد بخش درخواست‌ها شوید.</CardContent></Card>
      </DashboardShell>
    </RoleGuard>
  );
}
