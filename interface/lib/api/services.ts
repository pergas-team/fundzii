import { apiFetch } from "./client";
import type { DynamicFormSchema } from "@/types/form";
import type { FinancialService } from "@/types/service";

export async function listServices() {
  return apiFetch<{ results: FinancialService[] }>("/api/fundzi/services/");
}

export async function getService(slug: string) {
  return apiFetch<FinancialService>(`/api/fundzi/services/${slug}/`);
}

export async function getServiceForm(slug: string) {
  return apiFetch<DynamicFormSchema>(`/api/fundzi/services/${slug}/form/`);
}
