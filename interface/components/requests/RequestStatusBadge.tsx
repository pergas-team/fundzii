import { Badge } from "@/components/ui/badge";
import { statusTone, translateStatus } from "@/lib/utils/statusLabels";

export function RequestStatusBadge({ status }: { status?: string | null }) {
  return <Badge variant={statusTone(status)}>{translateStatus(status)}</Badge>;
}
