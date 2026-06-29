import { apiFetch, toQuery } from "./client";
import type { PaginatedResponse } from "@/types/admin";
import type { FundziUser } from "@/types/user";

export type UserFilters = {
  q?: string;
  role?: string;
  page?: string;
  page_size?: string;
};

export type UserCreatePayload = {
  phone_number: string;
  first_name?: string;
  last_name?: string;
  password?: string;
  role: string;
  is_active?: boolean;
};

export async function listUsers(filters: UserFilters = {}) {
  return apiFetch<PaginatedResponse<FundziUser>>(`/api/fundzi/admin/users/${toQuery(filters)}`);
}

export async function createUser(payload: UserCreatePayload) {
  return apiFetch<FundziUser>("/api/fundzi/admin/users/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateUser(id: number, payload: Partial<FundziUser>) {
  return apiFetch<FundziUser>(`/api/fundzi/admin/users/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function setUserRole(id: number, role: string) {
  return apiFetch<FundziUser>(`/api/fundzi/admin/users/${id}/set-role/`, {
    method: "POST",
    body: JSON.stringify({ role }),
  });
}
