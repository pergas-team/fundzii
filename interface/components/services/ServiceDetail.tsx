import Link from "next/link";
import {
  AlertTriangle,
  ArrowLeft,
  Building2,
  CheckCircle2,
  Coins,
  FileText,
  Gem,
  HelpCircle,
  Info,
  Landmark,
  Layers,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { FinancialService, ServiceContent } from "@/types/service";

// ── Icon / colour maps ────────────────────────────────────────────────────────

const SLUG_ICONS: Record<string, LucideIcon> = {
  "gold-backed-financing": Gem,
  "property-backed-financing": Building2,
  "private-investment": TrendingUp,
  "private-financing": Coins,
};

const SLUG_SECTION: Record<string, "investment" | "financing"> = {
  "gold-backed-financing": "financing",
  "property-backed-financing": "financing",
  "private-financing": "financing",
  "private-investment": "investment",
};

const PALETTE = {
  investment: {
    stripe: "bg-emerald-400 dark:bg-emerald-500",
    border: "border-2 border-emerald-400 dark:border-emerald-500",
    heading: "text-emerald-600 dark:text-emerald-400",
    iconWrap: "bg-emerald-50 text-emerald-600 dark:bg-emerald-950/30 dark:text-emerald-400",
    stepDot: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400",
  },
  financing: {
    stripe: "bg-blue-400 dark:bg-blue-500",
    border: "border-2 border-blue-400 dark:border-blue-500",
    heading: "text-blue-600 dark:text-blue-400",
    iconWrap: "bg-blue-50 text-blue-600 dark:bg-blue-950/30 dark:text-blue-400",
    stepDot: "bg-blue-100 text-blue-700 dark:bg-blue-950/30 dark:text-blue-400",
  },
};

// ── Generic section wrapper ───────────────────────────────────────────────────

function SectionCard({
  title,
  icon: Icon,
  children,
  className,
}: {
  title: string;
  icon: LucideIcon;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("rounded-2xl border bg-card p-6", className)}>
      <h2 className="mb-4 flex items-center gap-2 text-base font-bold">
        <Icon className="h-5 w-5 shrink-0 text-muted-foreground" strokeWidth={1.5} />
        {title}
      </h2>
      {children}
    </div>
  );
}

// ── Content-type renderers ────────────────────────────────────────────────────

function Introduction({ items }: { items: ServiceContent[] }) {
  if (!items.length) return null;
  return (
    <SectionCard title="معرفی سرویس" icon={Info}>
      <div className="space-y-4">
        {items.map((c) => (
          <div
            key={c.id}
            className="prose-content text-sm leading-7 text-muted-foreground"
            dangerouslySetInnerHTML={{ __html: c.body }}
          />
        ))}
      </div>
    </SectionCard>
  );
}

function ProcessSteps({
  items,
  stepDotClass,
}: {
  items: ServiceContent[];
  stepDotClass: string;
}) {
  if (!items.length) return null;
  return (
    <SectionCard title="مراحل دریافت سرویس" icon={Layers}>
      <ol className="space-y-5">
        {items.map((c, i) => (
          <li key={c.id} className="flex gap-4">
            <span
              className={cn(
                "flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold",
                stepDotClass,
              )}
            >
              {i + 1}
            </span>
            <div className="flex-1 pt-0.5">
              <h3 className="text-sm font-semibold">{c.title}</h3>
              {c.body && (
                <div
                  className="prose-content mt-1 text-xs leading-6 text-muted-foreground"
                  dangerouslySetInnerHTML={{ __html: c.body }}
                />
              )}
            </div>
          </li>
        ))}
      </ol>
    </SectionCard>
  );
}

function Faq({ items }: { items: ServiceContent[] }) {
  if (!items.length) return null;
  return (
    <SectionCard title="سوالات متداول" icon={HelpCircle}>
      <div className="space-y-3">
        {items.map((c) => (
          <details
            key={c.id}
            className="group rounded-xl border p-4 text-sm open:border-primary/30"
          >
            <summary className="flex cursor-pointer list-none items-center justify-between gap-2 font-semibold leading-6">
              {c.title}
              <span className="grid h-5 w-5 shrink-0 place-items-center rounded-full border text-xs text-muted-foreground transition-transform duration-200 group-open:rotate-45">
                +
              </span>
            </summary>
            <div
              className="prose-content mt-3 text-xs leading-7 text-muted-foreground"
              dangerouslySetInnerHTML={{ __html: c.body }}
            />
          </details>
        ))}
      </div>
    </SectionCard>
  );
}

function Conditions({ items }: { items: ServiceContent[] }) {
  if (!items.length) return null;
  const conds = items.filter((c) => c.content_type === "conditions");
  const warns = items.filter((c) => c.content_type === "warning");
  return (
    <SectionCard title="شرایط و هشدارها" icon={CheckCircle2}>
      <div className="space-y-3">
        {conds.map((c) => (
          <article key={c.id} className="rounded-xl border bg-background p-4">
            <h3 className="flex items-center gap-2 text-sm font-semibold">
              <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-500" strokeWidth={1.5} />
              {c.title}
            </h3>
            <div
              className="prose-content mt-2 text-xs leading-6 text-muted-foreground"
              dangerouslySetInnerHTML={{ __html: c.body }}
            />
          </article>
        ))}
        {warns.map((c) => (
          <article
            key={c.id}
            className="rounded-xl border border-amber-300/40 bg-amber-50/50 p-4 dark:border-amber-700/30 dark:bg-amber-950/20"
          >
            <h3 className="flex items-center gap-2 text-sm font-semibold text-amber-700 dark:text-amber-400">
              <AlertTriangle className="h-4 w-4 shrink-0" strokeWidth={1.5} />
              {c.title}
            </h3>
            <div
              className="prose-content mt-2 text-xs leading-6 text-amber-700/80 dark:text-amber-400/80"
              dangerouslySetInnerHTML={{ __html: c.body }}
            />
          </article>
        ))}
      </div>
    </SectionCard>
  );
}

function Documents({ items }: { items: ServiceContent[] }) {
  if (!items.length) return null;
  return (
    <SectionCard title="مدارک مورد نیاز" icon={FileText}>
      <div className="space-y-3">
        {items.map((c) => (
          <div key={c.id} className="flex gap-3 rounded-xl border bg-background p-4">
            <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary">
              <FileText className="h-4 w-4" strokeWidth={1.5} />
            </span>
            <div
              className="prose-content flex-1 text-xs leading-6 text-muted-foreground"
              dangerouslySetInnerHTML={{ __html: c.body }}
            />
          </div>
        ))}
      </div>
    </SectionCard>
  );
}

// ── Main export ───────────────────────────────────────────────────────────────

export function ServiceDetail({ service }: { service: FinancialService }) {
  const contents = service.contents ?? [];
  const section = SLUG_SECTION[service.slug] ?? "financing";
  const palette = PALETTE[section];
  const Icon = SLUG_ICONS[service.slug] ?? Landmark;

  const intro = contents.filter((c) => c.content_type === "introduction");
  const steps = contents.filter((c) => c.content_type === "process_steps");
  const faq = contents.filter((c) => c.content_type === "faq");
  const conditions = contents.filter(
    (c) => c.content_type === "conditions" || c.content_type === "warning",
  );
  const docs = contents.filter((c) => c.content_type === "required_documents");

  return (
    <div className="grid gap-5">
      {/* Hero */}
      <div className={cn("overflow-hidden rounded-2xl bg-card", palette.border)}>
        <div className={cn("h-1.5 w-full", palette.stripe)} aria-hidden />
        <div className="p-6 md:p-8">
          <div className="flex flex-col gap-5 md:flex-row md:items-start md:gap-8">
            <span
              className={cn(
                "grid h-16 w-16 shrink-0 place-items-center rounded-2xl",
                palette.iconWrap,
              )}
            >
              <Icon className="h-8 w-8" strokeWidth={1.5} />
            </span>
            <div className="min-w-0 flex-1">
              <h1 className={cn("text-xl font-extrabold md:text-2xl", palette.heading)}>
                {service.title}
              </h1>
              <p className="mt-2 text-sm leading-7 text-muted-foreground">
                {service.full_description || service.short_description}
              </p>
              <Button asChild className="mt-5" size="lg">
                <Link href={`/services/${service.slug}/apply`}>
                  شروع ثبت درخواست
                  <ArrowLeft className="h-4 w-4" />
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Body grid */}
      <div className="grid gap-5 md:grid-cols-3">
        {/* Main — 2/3 */}
        <div className="space-y-5 md:col-span-2">
          <Introduction items={intro} />
          <ProcessSteps items={steps} stepDotClass={palette.stepDot} />
          <Faq items={faq} />
        </div>

        {/* Sidebar — 1/3 */}
        <div className="space-y-5">
          <div className={cn("rounded-2xl bg-card p-5", palette.border)}>
            <p className="text-sm leading-6 text-muted-foreground">
              برای شروع فرآیند درخواست روی دکمه زیر کلیک کنید. تیم ما در
              کوتاه‌ترین زمان پیگیری خواهد کرد.
            </p>
            <Button asChild className="mt-4 w-full" size="lg">
              <Link href={`/services/${service.slug}/apply`}>
                ثبت درخواست
                <ArrowLeft className="h-4 w-4" />
              </Link>
            </Button>
          </div>
          <Conditions items={conditions} />
          <Documents items={docs} />
        </div>
      </div>
    </div>
  );
}
