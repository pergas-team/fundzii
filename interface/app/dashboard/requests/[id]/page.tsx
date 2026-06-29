"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { RoleGuard } from "@/components/layout/RoleGuard";
import { RequestDetail } from "@/components/requests/RequestDetail";
import { getMyRequest } from "@/lib/api/requests";
import type { FinancingRequest } from "@/types/request";

export default function MyRequestDetailPage() {
  const params = useParams<{ id: string }>();
  const [request, setRequest] = useState<FinancingRequest | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getMyRequest(params.id).then(setRequest).catch(() => setError("درخواست یافت نشد یا متعلق به شما نیست."));
  }, [params.id]);

  return (
    <RoleGuard roles={["applicant", "investor", "vendor", "admin", "operator"]}>
      <DashboardShell title="جزئیات درخواست">
        {error ? <p className="text-destructive">{error}</p> : request ? <RequestDetail request={request} /> : <p className="text-muted-foreground">در حال بارگذاری...</p>}
      </DashboardShell>
    </RoleGuard>
  );
}
