"use client";

import { create } from "zustand";
import type { CurrentUser } from "@/types/auth";

type AuthState = {
  user: CurrentUser | null;
  isReady: boolean;
  setUser: (user: CurrentUser | null) => void;
  setReady: (isReady: boolean) => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isReady: false,
  setUser: (user) => set({ user, isReady: true }),
  setReady: (isReady) => set({ isReady }),
}));
