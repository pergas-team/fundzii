"use client";

import {
  BadgeCheck,
  Banknote,
  CalendarDays,
  ChevronLeft,
  Layers,
  Percent,
  ShieldCheck,
  Tag,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { usePublicP2PRequests } from "@/hooks/usePublicP2PRequests";
import { cn } from "@/lib/utils";
import type { PublicP2PRequest } from "@/types/p2p";

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatValue(value: string | number | string[]): string {
  if (Array.isArray(value)) return value.join("، ");
  if (typeof value === "number") return value.toLocaleString("fa-IR");
  return String(value);
}

// Fields shown as primary "highlight" cells inside the card.
// Order matters — first match wins per slug type.
const HIGHLIGHT_KEYS: Record<
  string,
  { key: string; icon: React.ElementType; colorClass: string }[]
> = {
  "private-investment": [
    { key: "investment_amount", icon: Banknote, colorClass: "text-emerald-600 dark:text-emerald-400" },
    { key: "duration_months", icon: CalendarDays, colorClass: "text-blue-600 dark:text-blue-400" },
    { key: "min_return_rate", icon: Percent, colorClass: "text-amber-600 dark:text-amber-400" },
    { key: "max_return_rate", icon: Percent, colorClass: "text-amber-600 dark:text-amber-400" },
  ],
  "private-financing": [
    { key: "requested_amount", icon: Banknote, colorClass: "text-blue-600 dark:text-blue-400" },
    { key: "duration_months", icon: CalendarDays, colorClass: "text-emerald-600 dark:text-emerald-400" },
    { key: "max_acceptable_rate", icon: Percent, colorClass: "text-amber-600 dark:text-amber-400" },
    { key: "collateral_estimated_value", icon: ShieldCheck, colorClass: "text-purple-600 dark:text-purple-400" },
  ],
};

// Fields shown as tag chips (multi_select / select with list-like values)
const TAG_KEYS = new Set([
  "required_collateral_types",
  "offered_collateral_types",
  "investment_sector",
  "financing_purpose",
  "contract_type",
  "preferred_contract_type",
  "payment_schedule",
  "repayment_schedule",
  "return_payment_type",
  "risk_tolerance",
]);

// ── Single card ───────────────────────────────────────────────────────────────

function P2PCard({
  req,
  slug,
  section,
}: {
  req: PublicP2PRequest;
  slug: string;
  section: "investment" | "financing";
}) {
  const highlights = HIGHLIGHT_KEYS[slug] ?? [];
  const borderClass =
    section === "investment"
      ? "border-emerald-300 dark:border-emerald-700"
      : "border-blue-300 dark:border-blue-700";

  // Split fields into highlights and tag-style
  const highlightItems = highlights
    .map(({ key, icon, colorClass }) => {
      const f = req.fields[key];
      if (!f) return null;
      return { key, label: f.label, value: formatValue(f.value), icon, colorClass };
    })
    .filter(Boolean) as {
    key: string;
    label: string;
    value: string;
    icon: React.ElementType;
    colorClass: string;
  }[];

  const tagItems = Object.entries(req.fields).filter(
    ([k]) =>
      TAG_KEYS.has(k) &&
      !highlights.some((h) => h.key === k),
  );

  const submittedDate = new Date(req.submitted_at).toLocaleDateString("fa-IR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div
      className={cn(
        "flex flex-col gap-4 rounded-2xl border-2 bg-card p-5 transition-shadow duration-200 hover:shadow-md",
        borderClass,
      )}
    >
      {/* Header row */}
      <div className="flex items-center justify-between gap-2">
        <span className="flex items-center gap-1.5 rounded-full bg-primary/10 px-3 py-1 text-xs font-bold text-primary">
          <BadgeCheck className="h-3.5 w-3.5" />
          تأیید‌شده توسط ادمین
        </span>
        <span className="text-xs text-muted-foreground">{submittedDate}</span>
        <span className="font-mono text-xs text-muted-foreground">{req.ref}</span>
      </div>

      {/* Highlight figures */}
      {highlightItems.length > 0 && (
        <div className="grid grid-cols-2 gap-3">
          {highlightItems.map(({ key, label, value, icon: Icon, colorClass }) => (
            <div key={key} className="flex items-start gap-2 rounded-xl border bg-background p-3">
              <Icon className={cn("mt-0.5 h-4 w-4 shrink-0", colorClass)} strokeWidth={1.5} />
              <div className="min-w-0">
                <p className="text-[10px] text-muted-foreground">{label}</p>
                <p className="truncate text-sm font-bold">{value}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tag chips */}
      {tagItems.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {tagItems.map(([k, f]) => (
            <span
              key={k}
              className="flex items-center gap-1 rounded-lg border bg-muted/60 px-2.5 py-1 text-xs text-muted-foreground"
            >
              <Tag className="h-3 w-3 shrink-0" />
              {f.label}: <span className="font-medium text-foreground">{formatValue(f.value)}</span>
            </span>
          ))}
        </div>
      )}

      {/* CTA */}
      <Button variant="outline" size="sm" className="w-full gap-2 text-xs">
        <Users className="h-4 w-4" />
        تماس و اعلام مشارکت
        <ChevronLeft className="h-3.5 w-3.5 mr-auto" />
      </Button>
    </div>
  );
}

// ── Section skeleton ──────────────────────────────────────────────────────────

function ListSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {[0, 1, 2].map((i) => (
        <Skeleton key={i} className="h-52 rounded-2xl" />
      ))}
    </div>
  );
}

// ── Public export ─────────────────────────────────────────────────────────────

export function PublicP2PSection({
  slug,
  section,
}: {
  slug: string;
  section: "investment" | "financing";
}) {
  const { data, isLoading } = usePublicP2PRequests(slug);

  const borderClass =
    section === "investment"
      ? "border-emerald-400 dark:border-emerald-500"
      : "border-blue-400 dark:border-blue-500";

  const headingClass =
    section === "investment"
      ? "text-emerald-600 dark:text-emerald-400"
      : "text-blue-600 dark:text-blue-400";

  const label =
    section === "investment" ? "سرمایه‌گذاران منتظر تطبیق" : "متقاضیان تامین مالی";

  return (
    <section className={cn("rounded-2xl border-2 bg-card p-6", borderClass)}>
      {/* Section header */}
      <div className="mb-5 flex items-center gap-2.5">
        <Layers className="h-5 w-5 shrink-0 text-muted-foreground" strokeWidth={1.5} />
        <div>
          <h2 className={cn("text-base font-bold", headingClass)}>{label}</h2>
          <p className="text-xs text-muted-foreground">
            درخواست‌های تأیید‌شده — قابل مشاهده برای همه کاربران
          </p>
        </div>
        {!isLoading && data.length > 0 && (
          <span className="mr-auto rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-bold text-primary">
            {data.length}
          </span>
        )}
      </div>

      {isLoading ? (
        <ListSkeleton />
      ) : data.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-10 text-center">
          <Users className="h-10 w-10 text-muted-foreground/40" strokeWidth={1} />
          <p className="text-sm text-muted-foreground">
            در حال حاضر درخواست تأیید‌شده‌ای برای نمایش وجود ندارد.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {data.map((req) => (
            <P2PCard key={req.id} req={req} slug={slug} section={section} />
          ))}
        </div>
      )}
    </section>
  );
}
