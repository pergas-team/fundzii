import { Landmark } from "lucide-react";
import { ServiceCard } from "./ServiceCard";
import type { FinancialService } from "@/types/service";

export function ServiceList({ services }: { services: FinancialService[] }) {
  if (!services.length)
    return (
      <div className="grid place-items-center gap-3 rounded-2xl border border-dashed bg-card p-12 text-center">
        <span className="grid h-12 w-12 place-items-center rounded-full bg-muted text-muted-foreground">
          <Landmark className="h-6 w-6" />
        </span>
        <p className="text-muted-foreground">در حال حاضر خدمتی فعال نیست.</p>
      </div>
    );
  return (
    <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
      {services.map((service) => (
        <ServiceCard key={service.id} service={service} />
      ))}
    </div>
  );
}
