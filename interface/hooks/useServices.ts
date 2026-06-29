"use client";

import { useEffect, useState } from "react";
import { listServices } from "@/lib/api/services";
import type { FinancialService } from "@/types/service";

export function useServices() {
  const [services, setServices] = useState<FinancialService[]>([]);
  const [isLoading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listServices()
      .then((response) => setServices(response.results))
      .catch(() => setError("خطایی در دریافت خدمات رخ داد."))
      .finally(() => setLoading(false));
  }, []);

  return { services, isLoading, error };
}
