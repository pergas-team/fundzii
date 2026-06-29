"use client";

import { useEffect, useState } from "react";
import { getServiceForm } from "@/lib/api/services";
import type { DynamicFormSchema } from "@/types/form";

export function useDynamicForm(slug: string) {
  const [schema, setSchema] = useState<DynamicFormSchema | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getServiceForm(slug)
      .then(setSchema)
      .catch(() => setError("فرم این سرویس قابل دریافت نیست."))
      .finally(() => setLoading(false));
  }, [slug]);

  return { schema, isLoading, error };
}
