import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatDate } from "@/lib/utils/formatDate";
import type { FinancingRequest } from "@/types/request";
import { RequestStatusBadge } from "@/components/requests/RequestStatusBadge";

export function AdminRequestTable({ requests, basePath = "/admin/requests", framed = true }: { requests: FinancingRequest[]; basePath?: string; framed?: boolean }) {
  const Wrapper = framed ? Card : "div";
  return (
    <Wrapper className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>کد پیگیری</TableHead>
            <TableHead>کاربر</TableHead>
            <TableHead>سرویس</TableHead>
            <TableHead>وضعیت</TableHead>
            <TableHead>مسئول</TableHead>
            <TableHead>تاریخ</TableHead>
            <TableHead></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {requests.map((request) => (
            <TableRow key={request.id}>
              <TableCell>{request.tracking_code}</TableCell>
              <TableCell>{request.user?.phone_number || request.user?.username || "-"}</TableCell>
              <TableCell>{request.service.title}</TableCell>
              <TableCell><RequestStatusBadge status={request.current_status} /></TableCell>
              <TableCell>{request.admin_assignee?.phone_number || request.admin_assignee?.username || "-"}</TableCell>
              <TableCell>{formatDate(request.submitted_at)}</TableCell>
              <TableCell><Button asChild size="sm" variant="outline"><Link href={`${basePath}/${request.id}`}>بررسی</Link></Button></TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Wrapper>
  );
}
