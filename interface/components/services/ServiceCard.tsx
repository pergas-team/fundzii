import Link from "next/link";
import { ArrowLeft, Building2, Gem, Landmark, type LucideIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import type { FinancialService } from "@/types/service";

const typeMeta: Record<string, { label: string; icon: LucideIcon }> = {
  gold_backed: { label: "پشتوانه طلا", icon: Gem },
  property_backed: { label: "وثیقه ملکی", icon: Building2 },
  other: { label: "سایر خدمات", icon: Landmark },
};

export function ServiceCard({ service }: { service: FinancialService }) {
  const meta = typeMeta[service.service_type] ?? typeMeta.other;
  const Icon = meta.icon;

  return (
    <Card className="group flex flex-col overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-lift">
      <div className="h-1.5 w-full bg-gradient-accent" aria-hidden />
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <span className="grid h-12 w-12 place-items-center rounded-xl bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
            <Icon className="h-6 w-6" />
          </span>
          <Badge variant="accent">{meta.label}</Badge>
        </div>
        <CardTitle className="pt-3">{service.title}</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 text-sm leading-7 text-muted-foreground">
        {service.short_description || "فرم و قوانین این سرویس به‌صورت پویا از سرور دریافت می‌شود."}
      </CardContent>
      <CardFooter className="flex-wrap gap-2">
        <Button asChild variant="outline" className="flex-1">
          <Link href={`/services/${service.slug}`}>مشاهده جزئیات</Link>
        </Button>
        <Button asChild className="flex-1">
          <Link href={`/services/${service.slug}/apply`}>
            ثبت درخواست
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
