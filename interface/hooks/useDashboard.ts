"use client";
import { useEffect, useState } from "react";
import { getDashboard } from "@/lib/api/dashboard";
import type { DashboardData } from "@/types/dashboard";

const EMPTY: DashboardData = { investment: [], financing: [], vendor_services: [] };

export function useDashboard() {
  const [data, setData] = useState<DashboardData>(EMPTY);
  const [isLoading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch(() => setError("خطایی در دریافت داده‌ها رخ داد."))
      .finally(() => setLoading(false));
  }, []);

  return { data, isLoading, error };
}
