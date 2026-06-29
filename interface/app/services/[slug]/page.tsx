"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ServiceDetail } from "@/components/services/ServiceDetail";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { getService } from "@/lib/api/services";
import type { FinancialService } from "@/types/service";

export default function ServiceDetailPage() {
  const params = useParams<{ slug: string }>();
  const [service, setService] = useState<FinancialService | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getService(params.slug).then(setService).catch(() => setError("سرویس موردنظر یافت نشد."));
  }, [params.slug]);

  if (error)
    return (
      <main className="container py-8">
        <Alert className="border-destructive/30 bg-destructive/5">
          <AlertTitle className="text-destructive">خطا</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </main>
    );
  if (!service)
    return (
      <main className="container grid gap-6 py-8">
        <Skeleton className="h-48 rounded-3xl" />
        <Skeleton className="h-32" />
      </main>
    );
  return (
    <main className="container py-8">
      <ServiceDetail service={service} />
    </main>
  );
}
