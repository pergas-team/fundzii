"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { assignAdminRequest, archiveAdminRequest, deleteAdminAttachment, uploadAdminAttachment } from "@/lib/api/admin";
import { listUsers } from "@/lib/api/users";
import type { FinancingRequest, RequestAttachment } from "@/types/request";
import type { FundziUser } from "@/types/user";

export function AdminRequestActions({ request, onChanged }: { request: FinancingRequest; onChanged: (request: FinancingRequest) => void }) {
  const [operators, setOperators] = useState<FundziUser[]>([]);
  const [assignee, setAssignee] = useState(String(request.admin_assignee?.id || ""));
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    listUsers({ role: "operator", page_size: "100" }).then((response) => setOperators(response.results)).catch(() => setOperators([]));
  }, []);

  async function assign() {
    setLoading(true);
    setMessage("");
    try {
      const updated = await assignAdminRequest(request.id, assignee ? Number(assignee) : null);
      onChanged({ ...request, ...updated });
      setMessage("مسئول درخواست بروزرسانی شد.");
    } finally {
      setLoading(false);
    }
  }

  async function toggleArchive() {
    setLoading(true);
    setMessage("");
    try {
      const updated = await archiveAdminRequest(request.id, !request.is_archived);
      onChanged({ ...request, ...updated });
      setMessage(updated.is_archived ? "درخواست بایگانی شد." : "درخواست از بایگانی خارج شد.");
    } finally {
      setLoading(false);
    }
  }

  async function upload(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    if (!formData.get("file")) return;
    setLoading(true);
    setMessage("");
    try {
      const attachment = await uploadAdminAttachment(request.id, formData);
      onChanged({ ...request, attachments: [...(request.attachments || []), attachment] });
      form.reset();
      setMessage("پیوست اضافه شد.");
    } finally {
      setLoading(false);
    }
  }

  async function removeAttachment(attachment: RequestAttachment) {
    setLoading(true);
    setMessage("");
    try {
      await deleteAdminAttachment(request.id, attachment.id);
      onChanged({ ...request, attachments: (request.attachments || []).filter((item) => item.id !== attachment.id) });
      setMessage("پیوست حذف شد.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid gap-4 rounded-lg border bg-card p-4">
      <h3 className="font-bold">عملیات مدیریتی</h3>
      <div className="grid gap-2 md:grid-cols-[1fr_auto]">
        <select value={assignee} onChange={(event) => setAssignee(event.target.value)} className="h-11 rounded-lg border border-input bg-card px-3.5 text-sm shadow-sm outline-none transition-colors focus-visible:border-ring/60 focus-visible:ring-2 focus-visible:ring-ring/40">
          <option value="">بدون مسئول</option>
          {operators.map((user) => (
            <option key={user.id} value={user.id}>{user.first_name || user.username} ({user.username})</option>
          ))}
        </select>
        <Button onClick={assign} disabled={loading}>ثبت مسئول</Button>
      </div>
      <Button type="button" variant="outline" onClick={toggleArchive} disabled={loading}>
        {request.is_archived ? "خروج از بایگانی" : "بایگانی درخواست"}
      </Button>
      <form onSubmit={upload} className="grid gap-2">
        <Input name="title" placeholder="عنوان پیوست" />
        <Input name="document_type" placeholder="نوع سند" />
        <Input name="file" type="file" />
        <Button type="submit" disabled={loading}>افزودن پیوست</Button>
      </form>
      {(request.attachments || []).length ? (
        <div className="grid gap-2 text-sm">
          {(request.attachments || []).map((attachment) => (
            <div key={attachment.id} className="flex items-center justify-between gap-2 rounded-md border p-2">
              <span>{attachment.title || attachment.document_type || "پیوست"}</span>
              <Button type="button" size="sm" variant="destructive" onClick={() => removeAttachment(attachment)} disabled={loading}>حذف</Button>
            </div>
          ))}
        </div>
      ) : null}
      {message ? <p className="text-sm text-muted-foreground">{message}</p> : null}
    </div>
  );
}
