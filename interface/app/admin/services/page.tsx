import { AdminServiceManager } from "@/components/admin/AdminServiceManager";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { RoleGuard } from "@/components/layout/RoleGuard";

export default function AdminServicesPage() {
  return (
    <RoleGuard roles={["admin"]}>
      <DashboardShell mode="admin" title="خدمات">
        <AdminServiceManager />
      </DashboardShell>
    </RoleGuard>
  );
}
