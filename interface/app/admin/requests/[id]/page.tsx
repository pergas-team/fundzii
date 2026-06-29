"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { AdminInternalNotes } from "@/components/admin/AdminInternalNotes";
import { AdminRequestActions } from "@/components/admin/AdminRequestActions";
import { AdminStatusChanger } from "@/components/admin/AdminStatusChanger";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { RoleGuard } from "@/components/layout/RoleGuard";
import { RequestDetail } from "@/components/requests/RequestDetail";
import { getAdminRequest } from "@/lib/api/admin";
import type { FinancingRequest, InternalNote } from "@/types/request";

export default function AdminRequestDetailPage() {
  const params = useParams<{ id: string }>();
  const [request, setRequest] = useState<FinancingRequest | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getAdminRequest(params.id).then(setRequest).catch(() => setError("درخواست یافت نشد."));
  }, [params.id]);

  function addNote(note: InternalNote) {
    setRequest((current) => current ? { ...current, internal_notes: [...(current.internal_notes || []), note] } : current);
  }

  function mergeStatusUpdate(updated: FinancingRequest) {
    setRequest((current) => current ? {
      ...current,
      ...updated,
      workflow_steps: current.workflow_steps,
      attachments: current.attachments,
      internal_notes: current.internal_notes,
    } : updated);
  }

  return (
    <RoleGuard roles={["admin"]}>
      <DashboardShell mode="admin" title="بررسی درخواست">
        {error ? <p className="text-destructive">{error}</p> : request ? (
          <RequestDetail
            request={request}
            adminSlot={
              <div className="grid gap-4 lg:grid-cols-2">
                <AdminStatusChanger request={request} onChanged={mergeStatusUpdate} />
                <AdminInternalNotes requestId={request.id} notes={request.internal_notes} onAdded={addNote} />
                <AdminRequestActions request={request} onChanged={setRequest} />
              </div>
            }
          />
        ) : <p className="text-muted-foreground">در حال بارگذاری...</p>}
      </DashboardShell>
    </RoleGuard>
  );
}
