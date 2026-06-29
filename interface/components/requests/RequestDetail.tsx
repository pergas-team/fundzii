import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDate } from "@/lib/utils/formatDate";
import type { FinancingRequest } from "@/types/request";
import { RequestAttachments } from "./RequestAttachments";
import { RequestStatusBadge } from "./RequestStatusBadge";
import { RequestSubmittedValues } from "./RequestSubmittedValues";
import { RequestTimeline } from "./RequestTimeline";

export function RequestDetail({ request, adminSlot }: { request: FinancingRequest; adminSlot?: React.ReactNode }) {
  return (
    <div className="grid gap-5">
      <Card>
        <CardHeader>
          <CardTitle className="flex flex-wrap items-center justify-between gap-3">
            <span>{request.tracking_code}</span>
            <RequestStatusBadge status={request.current_status} />
          </CardTitle>
        </CardHeader>
        <CardContent className="grid gap-2 text-sm text-muted-foreground">
          <p>سرویس: {request.service.title}</p>
          <p>تاریخ ثبت: {formatDate(request.submitted_at)}</p>
          <p>آخرین بروزرسانی: {formatDate(request.updated_at)}</p>
          {request.user ? <p>کاربر: {request.user.phone_number || request.user.username}</p> : null}
        </CardContent>
      </Card>
      {adminSlot}
      <div className="grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>اطلاعات ثبت‌شده</CardTitle></CardHeader>
          <CardContent><RequestSubmittedValues values={request.field_values} /></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>پیوست‌ها</CardTitle></CardHeader>
          <CardContent><RequestAttachments attachments={request.attachments} /></CardContent>
        </Card>
      </div>
      <Card>
        <CardHeader><CardTitle>تاریخچه وضعیت</CardTitle></CardHeader>
        <CardContent><RequestTimeline history={request.history} /></CardContent>
      </Card>
    </div>
  );
}
