"use client";

import { useEffect } from "react";
import { useAuth } from "./useAuth";

export function useCurrentUser() {
  const auth = useAuth();
  const { isReady, refreshUser } = auth;

  useEffect(() => {
    if (!isReady) {
      refreshUser();
    }
  }, [isReady, refreshUser]);

  return auth;
}
