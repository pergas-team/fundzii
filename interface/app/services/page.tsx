"use client";

import { useState, useMemo } from "react";
import { Landmark, TrendingUp } from "lucide-react";
import { ServiceCard } from "@/components/services/ServiceCard";
import { VendorServiceCard } from "@/components/services/VendorServiceCard";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboard } from "@/hooks/useDashboard";
import { cn } from "@/lib/utils";

const CATEGORY_LABELS: Record<string, string> = {
  crowdfunding: "تامین مالی جمعی",
  business_consulting: "مشاوره کسب‌وکار",
  legal: "حقوقی",
  credit_scoring: "اعتبارسنجی",
  accounting: "حسابداری",
  valuation: "ارزیابی دارایی",
  other: "سایر",
};

function ColumnSkeleton() {
  return (
    <div className="space-y-4 p-4">
      <Skeleton className="h-36" />
      <Skeleton className="h-36" />
    </div>
  );
}

function HorizontalSkeleton() {
  return (
    <div className="flex gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} className="h-52 w-[270px] shrink-0" />
      ))}
    </div>
  );
}

function EmptyColumn({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12 text-center">
      <span className="grid h-12 w-12 place-items-center rounded-full bg-muted text-muted-foreground">
        <Landmark className="h-6 w-6" />
      </span>
      <p className="text-sm text-muted-foreground">{message}</p>
    </div>
  );
}

export default function ServicesPage() {
  const { data, isLoading, error } = useDashboard();
  const [activeCategory, setActiveCategory] = useState<string>("all");

  const uniqueCategories = useMemo(() => {
    const cats = Array.from(new Set(data.vendor_services.map((s) => s.category)));
    return cats;
  }, [data.vendor_services]);

  const filteredVendors = useMemo(() => {
    if (activeCategory === "all") return data.vendor_services;
    return data.vendor_services.filter((s) => s.category === activeCategory);
  }, [data.vendor_services, activeCategory]);

  if (error) {
    return (
      <main className="container py-8">
        <Alert className="border-destructive/30 bg-destructive/5">
          <AlertTitle className="text-destructive">خطا</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </main>
    );
  }

  return (
    <div className="flex min-h-screen flex-col">
      {/* Page header */}
      <div className="container py-5">
        <h1 className="text-3xl font-extrabold tracking-tight">خدمات فاندزی</h1>
        <p className="mt-1.5 text-muted-foreground">
          سرویس مناسب خود را در بخش‌های سرمایه‌گذاری، تامین مالی و خدمات تخصصی انتخاب کنید.
        </p>
      </div>

      {/* Top section: two-column split */}
      <section className="flex h-[70vh] min-h-[480px] border-t">
        {/* Right column — سرمایه‌گذاری (in RTL this renders on the right) */}
        <div className="flex w-1/2 flex-col">
          <div className="sticky top-0 z-10 flex items-center gap-3 border-b bg-background/95 px-6 py-4 backdrop-blur">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-emerald-50 text-emerald-600 dark:bg-emerald-950/30">
              <TrendingUp className="h-5 w-5" />
            </span>
            <div className="flex-1 min-w-0">
              <h2 className="font-bold">سرمایه‌گذاری</h2>
            </div>
            <span className="rounded-full bg-muted px-2.5 py-0.5 text-xs text-muted-foreground">
              {isLoading ? "…" : data.investment.length}
            </span>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {isLoading ? (
              <ColumnSkeleton />
            ) : data.investment.length === 0 ? (
              <EmptyColumn message="خدمتی در این بخش تعریف نشده." />
            ) : (
              data.investment.map((service) => (
                <ServiceCard key={service.id} service={service} />
              ))
            )}
          </div>
        </div>

        {/* Left column — تامین مالی (border-r in RTL separates the two columns) */}
        <div className="flex w-1/2 flex-col border-r">
          <div className="sticky top-0 z-10 flex items-center gap-3 border-b bg-background/95 px-6 py-4 backdrop-blur">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-primary/5 text-primary">
              <Landmark className="h-5 w-5" />
            </span>
            <div className="flex-1 min-w-0">
              <h2 className="font-bold">تامین مالی</h2>
            </div>
            <span className="rounded-full bg-muted px-2.5 py-0.5 text-xs text-muted-foreground">
              {isLoading ? "…" : data.financing.length}
            </span>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {isLoading ? (
              <ColumnSkeleton />
            ) : data.financing.length === 0 ? (
              <EmptyColumn message="خدمتی در این بخش تعریف نشده." />
            ) : (
              data.financing.map((service) => (
                <ServiceCard key={service.id} service={service} />
              ))
            )}
          </div>
        </div>
      </section>

      {/* Bottom section: vendor services horizontal scroll */}
      <section className="border-t bg-secondary/30 py-6">
        <div className="container">
          <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="text-lg font-bold">خدمات تخصصی و عمومی</h2>
              <p className="text-xs text-muted-foreground">خدمات ارائه‌شده توسط وندورهای مالی و غیرمالی</p>
            </div>
            {/* Category filter chips */}
            {!isLoading && uniqueCategories.length > 0 && (
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setActiveCategory("all")}
                  className={cn(
                    "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                    activeCategory === "all"
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-border bg-background text-muted-foreground hover:border-primary/40 hover:text-foreground",
                  )}
                >
                  همه
                </button>
                {uniqueCategories.map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setActiveCategory(cat)}
                    className={cn(
                      "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                      activeCategory === cat
                        ? "border-primary bg-primary text-primary-foreground"
                        : "border-border bg-background text-muted-foreground hover:border-primary/40 hover:text-foreground",
                    )}
                  >
                    {CATEGORY_LABELS[cat] ?? cat}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Horizontal scroll area */}
          <div className="overflow-x-auto pb-4 -mx-4 px-4">
            {isLoading ? (
              <HorizontalSkeleton />
            ) : filteredVendors.length === 0 ? (
              <p className="py-8 text-center text-sm text-muted-foreground">
                خدمتی در این دسته‌بندی یافت نشد.
              </p>
            ) : (
              <div className="flex gap-4 w-max">
                {filteredVendors.map((vendor) => (
                  <VendorServiceCard key={vendor.id} service={vendor} />
                ))}
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
