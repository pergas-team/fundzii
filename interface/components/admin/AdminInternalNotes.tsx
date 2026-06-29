"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { addAdminInternalNote } from "@/lib/api/admin";
import { formatDate } from "@/lib/utils/formatDate";
import type { InternalNote } from "@/types/request";

export function AdminInternalNotes({ requestId, notes = [], onAdded }: { requestId: number; notes?: InternalNote[]; onAdded?: (note: InternalNote) => void }) {
  const [body, setBody] = useState("");
  const [isLoading, setLoading] = useState(false);

  async function addNote() {
    if (!body.trim()) return;
    setLoading(true);
    try {
      const note = await addAdminInternalNote(requestId, body);
      onAdded?.(note);
      setBody("");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid gap-3 rounded-lg border bg-card p-4">
      <h3 className="font-bold">یادداشت‌های داخلی</h3>
      <div className="grid gap-2">
        {notes.map((note) => (
          <div key={note.id} className="rounded-md bg-muted p-3 text-sm">
            <p>{note.body}</p>
            <p className="mt-1 text-xs text-muted-foreground">{note.author || "-"} · {formatDate(note.created_at)}</p>
          </div>
        ))}
      </div>
      <Textarea value={body} onChange={(event) => setBody(event.target.value)} placeholder="یادداشت داخلی جدید" />
      <Button onClick={addNote} disabled={isLoading}>{isLoading ? "در حال ثبت..." : "افزودن یادداشت"}</Button>
    </div>
  );
}
