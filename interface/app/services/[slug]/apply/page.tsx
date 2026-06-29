"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ChevronRight } from "lucide-react";
import { RoleGuard } from "@/components/layout/RoleGuard";
import { DynamicFormRenderer } from "@/components/forms/DynamicFormRenderer";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { getService, getServiceForm } from "@/lib/api/services";
import type { DynamicFormSchema } from "@/types/form";
import type { FinancialService } from "@/types/service";

export default function ApplyPage() {
  const params = useParams<{ slug: string }>();
  const [service, setService] = useState<FinancialService | null>(null);
  const [schema, setSchema] = useState<DynamicFormSchema | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getService(params.slug), getServiceForm(params.slug)])
      .then(([serviceResponse, formResponse]) => {
        setService(serviceResponse);
        setSchema(formResponse);
      })
      .catch(() => setError("دریافت فرم این سرویس با خطا مواجه شد."));
  }, [params.slug]);

  return (
    <RoleGuard roles={["applicant", "investor", "vendor", "admin", "operator"]}>
      <main className="container grid max-w-3xl gap-6 py-8">
        {error ? (
          <Alert className="border-destructive/30 bg-destructive/5">
            <AlertTitle className="text-destructive">خطا</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}
        {!service || !schema ? (
          <Skeleton className="h-80" />
        ) : (
          <>
            <div>
              <nav className="mb-3 flex items-center gap-1 text-sm text-muted-foreground">
                <Link href="/services" className="transition-colors hover:text-foreground">
                  خدمات
                </Link>
                <ChevronRight className="h-4 w-4" />
                <Link href={`/services/${service.slug}`} className="transition-colors hover:text-foreground">
                  {service.title}
                </Link>
              </nav>
              <h1 className="text-2xl font-extrabold tracking-tight">ثبت درخواست {service.title}</h1>
              {service.short_description ? (
                <p className="mt-1.5 text-sm text-muted-foreground">{service.short_description}</p>
              ) : null}
            </div>
            <DynamicFormRenderer slug={service.slug} schema={schema} />
          </>
        )}
      </main>
    </RoleGuard>
  );
}
