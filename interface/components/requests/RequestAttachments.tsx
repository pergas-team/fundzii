import { FileText } from "lucide-react";
import { resolveFileUrl } from "@/lib/utils/fileUrl";
import type { RequestAttachment } from "@/types/request";

export function RequestAttachments({ attachments = [] }: { attachments?: RequestAttachment[] }) {
  if (!attachments.length) return <p className="text-sm text-muted-foreground">پیوستی ثبت نشده است.</p>;
  return (
    <div className="grid gap-2">
      {attachments.map((attachment) => (
        <a key={attachment.id} className="flex items-center gap-2 rounded-md border p-3 text-sm hover:bg-muted" href={resolveFileUrl(attachment.file)} target="_blank">
          <FileText className="h-4 w-4 text-accent" />
          {attachment.title || attachment.document_type}
        </a>
      ))}
    </div>
  );
}
