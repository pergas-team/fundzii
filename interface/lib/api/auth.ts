import { apiFetch } from "./client";
import type { CurrentUser } from "@/types/auth";

export async function sendOtp(phone_number: string) {
  return apiFetch<{ detail: string; demo_code?: string }>("/api/fundzi/auth/send-otp/", {
    method: "POST",
    body: JSON.stringify({ phone_number }),
  });
}

export async function verifyOtp(phone_number: string, otp_code: string) {
  return apiFetch<{ user: CurrentUser }>("/api/fundzi/auth/verify-otp/", {
    method: "POST",
    body: JSON.stringify({ phone_number, otp_code }),
  });
}

export async function passwordLogin(username: string, password: string) {
  return apiFetch<{ user: CurrentUser }>("/api/fundzi/auth/login/", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export async function getCurrentUser() {
  return apiFetch<{ user: CurrentUser }>("/api/fundzi/auth/me/");
}

export async function logout() {
  return apiFetch<{ detail: string }>("/api/fundzi/auth/logout/", { method: "POST" });
}
