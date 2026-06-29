import Link from "next/link";
import {
  Briefcase,
  Building2,
  Calculator,
  Coins,
  Home,
  Scale,
  Star,
  type LucideIcon,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import type { VendorService } from "@/types/dashboard";

const CATEGORY_ICONS: Record<string, LucideIcon> = {
  crowdfunding: Coins,
  business_consulting: Briefcase,
  legal: Scale,
  credit_scoring: Star,
  accounting: Calculator,
  valuation: Home,
  other: Building2,
};

const CATEGORY_COLORS: Record<string, string> = {
  crowdfunding: "bg-amber-500",
  business_consulting: "bg-blue-500",
  legal: "bg-purple-500",
  credit_scoring: "bg-yellow-500",
  accounting: "bg-green-500",
  valuation: "bg-rose-500",
  other: "bg-slate-500",
};

export function VendorServiceCard({ service }: { service: VendorService }) {
  const Icon = CATEGORY_ICONS[service.category] ?? Building2;
  const colorBar = CATEGORY_COLORS[service.category] ?? "bg-slate-500";
  const isFinancial = service.vendor_type === "financial";

  return (
    <Card className="group flex w-[270px] flex-col overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-lift">
      <div className={`h-1.5 w-full ${colorBar}`} aria-hidden />
      <CardHeader className="pb-2 pt-4">
        <div className="flex items-start justify-between gap-2">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
            <Icon className="h-5 w-5" />
          </span>
          <Badge variant={isFinancial ? "accent" : "default"} className="shrink-0 text-xs">
            {isFinancial ? "مالی" : "غیرمالی"}
          </Badge>
        </div>
        <CardTitle className="mt-2 line-clamp-1 text-sm">{service.title}</CardTitle>
        <p className="text-xs text-muted-foreground">{service.vendor_name}</p>
      </CardHeader>
      <CardContent className="flex-1 pb-2">
        <p className="line-clamp-2 text-xs leading-6 text-muted-foreground">{service.description}</p>
        <div className="mt-3 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground">
          {service.price_display && (
            <span className="font-medium text-foreground">{service.price_display}</span>
          )}
          {service.duration_display && (
            <span>{service.duration_display}</span>
          )}
        </div>
      </CardContent>
      <CardFooter className="pt-2">
        <Button asChild variant="outline" size="sm" className="w-full text-xs">
          <Link href={`/vendor-services/${service.slug}`}>مشاهده و درخواست</Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
