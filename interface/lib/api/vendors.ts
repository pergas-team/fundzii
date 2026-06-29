import { apiFetch, toQuery } from "./client";
import type { Vendor } from "@/types/vendor";

export async function listVendors(filters: { q?: string } = {}) {
  return apiFetch<{ results: Vendor[] }>(`/api/fundzi/admin/partners/${toQuery(filters)}`);
}

export async function createVendor(payload: Omit<Vendor, "id">) {
  return apiFetch<Vendor>("/api/fundzi/admin/partners/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateVendor(id: number, payload: Partial<Vendor>) {
  return apiFetch<Vendor>(`/api/fundzi/admin/partners/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteVendor(id: number) {
  return apiFetch<{ detail: string }>(`/api/fundzi/admin/partners/${id}/`, {
    method: "DELETE",
  });
}
