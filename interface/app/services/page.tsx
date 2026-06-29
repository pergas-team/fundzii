"use client";

import { ServiceList } from "@/components/services/ServiceList";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { useServices } from "@/hooks/useServices";

export default function ServicesPage() {
  const { services, isLoading, error } = useServices();
  return (
    <main className="container py-8 lg:py-10">
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold tracking-tight">خدمات تأمین مالی فاندزی</h1>
        <p className="mt-2 text-muted-foreground">سرویس مناسب خود را انتخاب کنید و درخواست را ثبت نمایید.</p>
      </div>
      {isLoading ? (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <Skeleton key={index} className="h-64" />
          ))}
        </div>
      ) : error ? (
        <Alert className="border-destructive/30 bg-destructive/5">
          <AlertTitle className="text-destructive">خطا</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : (
        <ServiceList services={services} />
      )}
    </main>
  );
}
