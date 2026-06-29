import { Inbox } from "lucide-react";
import { RequestCard } from "./RequestCard";
import type { FinancingRequest } from "@/types/request";

export function RequestList({ requests, hrefPrefix }: { requests: FinancingRequest[]; hrefPrefix?: string }) {
  if (!requests.length)
    return (
      <div className="grid place-items-center gap-3 rounded-2xl border border-dashed bg-card p-12 text-center">
        <span className="grid h-12 w-12 place-items-center rounded-full bg-muted text-muted-foreground">
          <Inbox className="h-6 w-6" />
        </span>
        <p className="text-muted-foreground">هنوز درخواستی ثبت نشده است.</p>
      </div>
    );
  return (
    <div className="grid gap-3">
      {requests.map((request) => (
        <RequestCard key={request.id} request={request} hrefPrefix={hrefPrefix} />
      ))}
    </div>
  );
}
