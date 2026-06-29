import { apiFetch } from "./client";
import type { FinancingRequest } from "@/types/request";
import type { RequestHistoryItem } from "@/types/workflow";

export async function submitServiceRequest(slug: string, data: FormData | Record<string, unknown>) {
  if (data instanceof FormData) {
    return apiFetch<FinancingRequest>(`/api/fundzi/services/${slug}/requests/`, {
      method: "POST",
      body: data,
      formData: true,
    });
  }
  return apiFetch<FinancingRequest>(`/api/fundzi/services/${slug}/requests/`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function listMyRequests() {
  return apiFetch<{ results: FinancingRequest[] }>("/api/fundzi/requests/");
}

export async function getMyRequest(id: string | number) {
  return apiFetch<FinancingRequest>(`/api/fundzi/requests/${id}/`);
}

export async function getMyRequestHistory(id: string | number) {
  return apiFetch<{ results: RequestHistoryItem[] }>(`/api/fundzi/requests/${id}/history/`);
}
