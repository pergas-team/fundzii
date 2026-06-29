import { apiFetch } from "./client";
import type { FinancialService } from "@/types/service";

export type ServicePayload = Partial<FinancialService> & {
  rules_config?: Record<string, unknown> | string;
  metadata?: Record<string, unknown> | string;
};

export async function listAdminServices() {
  return apiFetch<{ results: FinancialService[] }>("/api/fundzi/admin/services/");
}

export async function createAdminService(payload: ServicePayload) {
  return apiFetch<FinancialService>("/api/fundzi/admin/services/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateAdminService(id: number, payload: ServicePayload) {
  return apiFetch<FinancialService>(`/api/fundzi/admin/services/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteAdminService(id: number) {
  return apiFetch<{ detail: string }>(`/api/fundzi/admin/services/${id}/`, {
    method: "DELETE",
  });
}

export async function createServiceContent(serviceId: number, payload: Record<string, unknown>) {
  return apiFetch<unknown>(`/api/fundzi/admin/services/${serviceId}/contents/`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateServiceContent(serviceId: number, contentId: number, payload: Record<string, unknown>) {
  return apiFetch<unknown>(`/api/fundzi/admin/services/${serviceId}/contents/${contentId}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteServiceContent(serviceId: number, contentId: number) {
  return apiFetch<{ detail: string }>(`/api/fundzi/admin/services/${serviceId}/contents/${contentId}/`, {
    method: "DELETE",
  });
}

export async function updateServiceForm(serviceId: number, payload: Record<string, unknown>) {
  return apiFetch<FinancialService>(`/api/fundzi/admin/services/${serviceId}/form/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function createServiceField(serviceId: number, payload: Record<string, unknown>) {
  return apiFetch<FinancialService>(`/api/fundzi/admin/services/${serviceId}/form/fields/`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateServiceField(serviceId: number, fieldId: number, payload: Record<string, unknown>) {
  return apiFetch<FinancialService>(`/api/fundzi/admin/services/${serviceId}/form/fields/${fieldId}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteServiceField(serviceId: number, fieldId: number) {
  return apiFetch<FinancialService>(`/api/fundzi/admin/services/${serviceId}/form/fields/${fieldId}/`, {
    method: "DELETE",
  });
}

export async function updateServiceWorkflow(serviceId: number, payload: Record<string, unknown>) {
  return apiFetch<FinancialService>(`/api/fundzi/admin/services/${serviceId}/workflow/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function createWorkflowStep(serviceId: number, payload: Record<string, unknown>) {
  return apiFetch<FinancialService>(`/api/fundzi/admin/services/${serviceId}/workflow/steps/`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateWorkflowStep(serviceId: number, stepId: number, payload: Record<string, unknown>) {
  return apiFetch<FinancialService>(`/api/fundzi/admin/services/${serviceId}/workflow/steps/${stepId}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteWorkflowStep(serviceId: number, stepId: number) {
  return apiFetch<FinancialService>(`/api/fundzi/admin/services/${serviceId}/workflow/steps/${stepId}/`, {
    method: "DELETE",
  });
}
