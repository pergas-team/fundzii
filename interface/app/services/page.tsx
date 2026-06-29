"use client";

import Link from "next/link";
import {
  Briefcase,
  Building2,
  Calculator,
  Coins,
  Gem,
  Home,
  Landmark,
  Layers,
  Scale,
  Star,
  TrendingUp,
  Users,
  type LucideIcon,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboard } from "@/hooks/useDashboard";
import { cn } from "@/lib/utils";
import type { FinancialService } from "@/types/service";
import type { VendorService } from "@/types/dashboard";

// ── Icon maps ─────────────────────────────────────────────────────────────────

const SLUG_ICONS: Record<string, LucideIcon> = {
  "gold-backed-financing": Gem,
  "property-backed-financing": Building2,
  "private-investment": TrendingUp,
  "private-financing": Coins,
};

const CATEGORY_ICONS: Record<string, LucideIcon> = {
  crowdfunding: Users,
  business_consulting: Briefcase,
  legal: Scale,
  credit_scoring: Star,
  accounting: Calculator,
  valuation: Home,
  other: Building2,
};

// ── Sub-components ─────────────────────────────────────────────────────────────

function ServiceCell({
  icon: Icon,
  label,
  href,
  iconClass,
}: {
  icon: LucideIcon;
  label: string;
  href: string;
  iconClass: string;
}) {
  return (
    <Link
      href={href}
      className="group flex flex-col items-center gap-2.5 rounded-xl border bg-background px-3 py-4 text-center transition-all duration-200 hover:border-current/20 hover:bg-muted/50 hover:shadow-sm active:scale-[0.97]"
    >
      <Icon
        className={cn("h-7 w-7 transition-transform duration-200 group-hover:scale-110", iconClass)}
        strokeWidth={1.5}
      />
      <span className="text-xs font-medium leading-[1.35] text-foreground">{label}</span>
    </Link>
  );
}

function GridSkeleton({ cols = 3, rows = 2 }: { cols?: number; rows?: number }) {
  return (
    <div className={`grid gap-3`} style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
      {Array.from({ length: cols * rows }).map((_, i) => (
        <Skeleton key={i} className="h-20 rounded-xl" />
      ))}
    </div>
  );
}

function VendorChip({ icon: Icon, label, href }: { icon: LucideIcon; label: string; href: string }) {
  return (
    <Link
      href={href}
      className="flex items-center gap-2.5 rounded-xl border bg-card px-5 py-3 text-sm font-medium whitespace-nowrap transition-all duration-200 hover:border-primary/30 hover:bg-primary/5 hover:text-primary"
    >
      <Icon className="h-4 w-4 shrink-0 text-muted-foreground" strokeWidth={1.5} />
      {label}
    </Link>
  );
}

function ChipSkeleton() {
  return (
    <div className="flex gap-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-11 w-36 rounded-xl" />
      ))}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function ServicesPage() {
  const { data, isLoading } = useDashboard();

  const financialVendors = data.vendor_services.filter((v) => v.vendor_type === "financial");
  const nonFinancialVendors = data.vendor_services.filter((v) => v.vendor_type === "non_financial");

  return (
    <main className="container py-8 md:py-10">
      {/* Page header */}
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-extrabold tracking-tight md:text-3xl">خدمات پلتفرم مالی</h1>
        <p className="mt-2 text-sm text-muted-foreground">انتخاب مسیر بر اساس نیاز شما</p>
      </div>

      {/* ── Two panels ────────────────────────────────────────────────────────── */}
      <div className="mb-5 grid grid-cols-2 gap-5">
        {/* تامین مالی — blue */}
        <div className="rounded-2xl border-2 border-blue-400 bg-card p-6 dark:border-blue-500">
          <div className="mb-5 text-center">
            <h2 className="text-lg font-bold text-blue-600 dark:text-blue-400">تامین مالی</h2>
            <p className="mt-1 text-xs text-muted-foreground">
              خدمات ویژه متقاضیان دریافت تسهیلات و منابع مالی
            </p>
          </div>

          {isLoading ? (
            <GridSkeleton />
          ) : (
            <div className="grid grid-cols-3 gap-3">
              {/* FinancialServices tagged as financing */}
              {data.financing.map((s) => {
                const Icon = SLUG_ICONS[s.slug] ?? Landmark;
                return (
                  <ServiceCell
                    key={s.id}
                    icon={Icon}
                    label={s.title}
                    href={`/services/${s.slug}`}
                    iconClass="text-blue-500"
                  />
                );
              })}
              {/* Financial vendor services (crowdfunding platforms) */}
              {financialVendors.map((vs) => {
                const Icon = CATEGORY_ICONS[vs.category] ?? Users;
                return (
                  <ServiceCell
                    key={`fvs-${vs.id}`}
                    icon={Icon}
                    label={vs.title}
                    href={`/vendor-services/${vs.slug}`}
                    iconClass="text-blue-500"
                  />
                );
              })}
              {!data.financing.length && !financialVendors.length && (
                <p className="col-span-3 py-6 text-center text-xs text-muted-foreground">
                  خدمتی در این بخش تعریف نشده.
                </p>
              )}
            </div>
          )}
        </div>

        {/* سرمایه‌گذاری — emerald */}
        <div className="rounded-2xl border-2 border-emerald-400 bg-card p-6 dark:border-emerald-500">
          <div className="mb-5 text-center">
            <h2 className="text-lg font-bold text-emerald-600 dark:text-emerald-400">سرمایه‌گذاری</h2>
            <p className="mt-1 text-xs text-muted-foreground">
              خدمات ویژه سرمایه‌گذاران حقیقی و حقوقی
            </p>
          </div>

          {isLoading ? (
            <GridSkeleton />
          ) : (
            <div className="grid grid-cols-3 gap-3">
              {data.investment.map((s) => {
                const Icon = SLUG_ICONS[s.slug] ?? TrendingUp;
                return (
                  <ServiceCell
                    key={s.id}
                    icon={Icon}
                    label={s.title}
                    href={`/services/${s.slug}`}
                    iconClass="text-emerald-500"
                  />
                );
              })}
              {!data.investment.length && (
                <p className="col-span-3 py-6 text-center text-xs text-muted-foreground">
                  خدمتی در این بخش تعریف نشده.
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── Bottom: credit/banking tools ─────────────────────────────────────── */}
      <div className="rounded-2xl border bg-card p-6">
        <div className="mb-5 flex items-center gap-2.5">
          <Layers className="h-5 w-5 shrink-0 text-muted-foreground" strokeWidth={1.5} />
          <h2 className="text-base font-bold">ابزارهای اعتباری و خدمات بانکی</h2>
        </div>

        {isLoading ? (
          <ChipSkeleton />
        ) : nonFinancialVendors.length ? (
          <div className="flex flex-wrap gap-3">
            {nonFinancialVendors.map((vs) => {
              const Icon = CATEGORY_ICONS[vs.category] ?? Building2;
              return (
                <VendorChip
                  key={vs.id}
                  icon={Icon}
                  label={vs.title}
                  href={`/vendor-services/${vs.slug}`}
                />
              );
            })}
          </div>
        ) : (
          <p className="py-4 text-sm text-muted-foreground">خدمات اعتباری به زودی اضافه می‌شود.</p>
        )}
      </div>
    </main>
  );
}
