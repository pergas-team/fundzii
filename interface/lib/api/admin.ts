import { apiFetch, toQuery } from "./client";
import type {
  AdminRequestFilters,
  AdminStats,
  PaginatedResponse,
  ReportFunnelItem,
  ReportMonthly,
  ReportPartnerPerformance,
  VendorApplication,
  VendorApplicationFilters,
} from "@/types/admin";
import type { FinancingRequest, InternalNote, RequestAttachment } from "@/types/request";

export async function listAdminRequests(filters: AdminRequestFilters = {}) {
  return apiFetch<PaginatedResponse<FinancingRequest>>(`/api/fundzi/admin/requests/${toQuery(filters)}`);
}

export async function getAdminStats() {
  return apiFetch<AdminStats>("/api/fundzi/admin/stats/");
}

export async function getAdminRequest(id: string | number) {
  return apiFetch<FinancingRequest>(`/api/fundzi/admin/requests/${id}/`);
}

export async function updateAdminRequestStatus(id: string | number, status: string, note?: string) {
  return apiFetch<FinancingRequest>(`/api/fundzi/admin/requests/${id}/status/`, {
    method: "PATCH",
    body: JSON.stringify({ status, note }),
  });
}

export async function addAdminInternalNote(id: string | number, body: string) {
  return apiFetch<InternalNote>(`/api/fundzi/admin/requests/${id}/notes/`, {
    method: "POST",
    body: JSON.stringify({ body }),
  });
}

export async function assignAdminRequest(id: string | number, assigneeId: number | null) {
  return apiFetch<FinancingRequest>(`/api/fundzi/admin/requests/${id}/assign/`, {
    method: "POST",
    body: JSON.stringify({ assignee_id: assigneeId }),
  });
}

export async function archiveAdminRequest(id: string | number, isArchived: boolean) {
  return apiFetch<FinancingRequest>(`/api/fundzi/admin/requests/${id}/archive/`, {
    method: "POST",
    body: JSON.stringify({ is_archived: isArchived }),
  });
}

export async function uploadAdminAttachment(id: string | number, formData: FormData) {
  return apiFetch<RequestAttachment>(`/api/fundzi/admin/requests/${id}/attachments/`, {
    method: "POST",
    body: formData,
    formData: true,
  });
}

export async function deleteAdminAttachment(id: string | number, attachmentId: string | number) {
  return apiFetch<{ detail: string }>(`/api/fundzi/admin/requests/${id}/attachments/${attachmentId}/`, {
    method: "DELETE",
  });
}

export async function listAdminVendorApplications(filters: VendorApplicationFilters = {}) {
  return apiFetch<PaginatedResponse<VendorApplication>>(`/api/fundzi/admin/vendor-applications/${toQuery(filters)}`);
}

export async function updateAdminVendorApplication(
  id: number,
  data: Partial<Pick<VendorApplication, "status" | "vendor_notes">>
) {
  return apiFetch<VendorApplication>(`/api/fundzi/admin/vendor-applications/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function getAdminReportFunnel() {
  return apiFetch<{ results: ReportFunnelItem[] }>("/api/fundzi/admin/reports/funnel/");
}

export async function getAdminReportPartnerPerformance() {
  return apiFetch<{ results: ReportPartnerPerformance[] }>("/api/fundzi/admin/reports/partner-performance/");
}

export async function getAdminReportMonthly() {
  return apiFetch<{ results: ReportMonthly[] }>("/api/fundzi/admin/reports/monthly/");
}

export function getAdminReportCsvUrl(report: "funnel" | "partner-performance" | "monthly") {
  return `/api/fundzi/admin/reports/${report}/?export=csv`;
}
