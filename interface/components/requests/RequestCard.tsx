import Link from "next/link";
import { ChevronLeft, Clock } from "lucide-react";
import { Card } from "@/components/ui/card";
import { formatDate } from "@/lib/utils/formatDate";
import type { FinancingRequest } from "@/types/request";
import { RequestStatusBadge } from "./RequestStatusBadge";

export function RequestCard({ request, hrefPrefix = "/dashboard/requests" }: { request: FinancingRequest; hrefPrefix?: string }) {
  return (
    <Link href={`${hrefPrefix}/${request.id}`} className="group block">
      <Card className="flex items-center justify-between gap-4 p-5 transition-all duration-300 hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-lift">
        <div className="min-w-0 space-y-1.5">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="font-bold tracking-tight" dir="ltr">{request.tracking_code}</span>
            <RequestStatusBadge status={request.current_status} />
          </div>
          <p className="truncate text-sm text-muted-foreground">{request.service.title}</p>
          <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Clock className="h-3.5 w-3.5" />
            آخرین بروزرسانی: {formatDate(request.updated_at)}
          </p>
        </div>
        <ChevronLeft className="h-5 w-5 shrink-0 text-muted-foreground transition-transform group-hover:-translate-x-1 group-hover:text-primary" />
      </Card>
    </Link>
  );
}
