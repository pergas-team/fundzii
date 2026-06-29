import { apiFetch } from "./client";
import type { DashboardData } from "@/types/dashboard";

export async function getDashboard() {
  return apiFetch<DashboardData>("/api/fundzi/dashboard/");
}
