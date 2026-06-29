"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { updateAdminRequestStatus } from "@/lib/api/admin";
import type { FinancingRequest } from "@/types/request";

export function AdminStatusChanger({ request, onChanged }: { request: FinancingRequest; onChanged: (request: FinancingRequest) => void }) {
  const [status, setStatus] = useState(request.current_status);
  const [note, setNote] = useState("");
  const [isLoading, setLoading] = useState(false);

  async function submit() {
    setLoading(true);
    try {
      const updated = await updateAdminRequestStatus(request.id, status, note);
      onChanged(updated);
      setNote("");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid gap-3 rounded-lg border bg-card p-4">
      <h3 className="font-bold">تغییر وضعیت</h3>
      <select value={status} onChange={(event) => setStatus(event.target.value)} className="h-11 rounded-lg border border-input bg-card px-3.5 text-sm shadow-sm outline-none transition-colors focus-visible:border-ring/60 focus-visible:ring-2 focus-visible:ring-ring/40">
        {(request.workflow_steps || []).map((step) => (
          <option key={step.key} value={step.key}>{step.title}</option>
        ))}
      </select>
      <Textarea value={note} onChange={(event) => setNote(event.target.value)} placeholder="یادداشت تغییر وضعیت" />
      <Button onClick={submit} disabled={isLoading}>{isLoading ? "در حال ثبت..." : "ثبت وضعیت"}</Button>
    </div>
  );
}
