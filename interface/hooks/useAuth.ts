"use client";

import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth/session";
import { getCurrentUser, logout as logoutApi } from "@/lib/api/auth";

export function useAuth() {
  const router = useRouter();
  const { user, isReady, setUser, setReady } = useAuthStore();

  async function refreshUser() {
    try {
      const response = await getCurrentUser();
      setUser(response.user);
      return response.user;
    } catch {
      setUser(null);
      return null;
    }
  }

  async function logout() {
    await logoutApi();
    setUser(null);
    router.push("/auth/login");
  }

  return { user, isReady, setUser, setReady, refreshUser, logout };
}
