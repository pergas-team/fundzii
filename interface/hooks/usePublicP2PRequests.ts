"use client";

import { useEffect, useState } from "react";
import { getPublicP2PRequests } from "@/lib/api/services";
import type { PublicP2PRequest } from "@/types/p2p";

export function usePublicP2PRequests(slug: string) {
  const [data, setData] = useState<PublicP2PRequest[]>([]);
  const [isLoading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getPublicP2PRequests(slug)
      .then((res) => setData(res.results))
      .catch(() => setError("خطا در دریافت اطلاعات"))
      .finally(() => setLoading(false));
  }, [slug]);

  return { data, isLoading, error };
}
