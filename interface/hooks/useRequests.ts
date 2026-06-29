"use client";

import { useEffect, useState } from "react";
import { listMyRequests } from "@/lib/api/requests";
import type { FinancingRequest } from "@/types/request";

export function useRequests() {
  const [requests, setRequests] = useState<FinancingRequest[]>([]);
  const [isLoading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listMyRequests()
      .then((response) => setRequests(response.results))
      .catch(() => setError("خطایی در دریافت درخواست‌ها رخ داد."))
      .finally(() => setLoading(false));
  }, []);

  return { requests, isLoading, error };
}
