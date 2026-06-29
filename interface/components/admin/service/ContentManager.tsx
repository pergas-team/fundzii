"use client";

import { useState } from "react";
import { Pencil, Plus, Save, Trash2, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RichTextEditor } from "@/components/ui/rich-text-editor";
import { Select, Switch } from "@/components/ui/select";
import {
  createServiceContent,
  deleteServiceContent,
  updateServiceContent,
} from "@/lib/api/adminServices";
import { CONTENT_TYPES, contentTypeLabel } from "@/lib/fundzi/formFields";
import type { FinancialService, ServiceContent } from "@/types/service";

type ContentDraft = {
  id?: number;
  content_type: string;
  title: string;
  body: string;
  order: number;
  is_active: boolean;
};

function toDraft(content?: ServiceContent, order = 0): ContentDraft {
  return {
    id: content?.id,
    content_type: content?.content_type ?? "introduction",
    title: content?.title ?? "",
    body: content?.body ?? "",
    order: content?.order ?? order,
    is_active: content?.is_active ?? true,
  };
}

export function ContentManager({ service, onChanged }: { service: FinancialService; onChanged: () => void }) {
  const contents = [...(service.contents || [])].sort((a, b) => a.order - b.order);
  const [editingId, setEditingId] = useState<number | "new" | null>(null);
  const [error, setError] = useState("");

  async function persist(draft: ContentDraft) {
    setError("");
    const payload = {
      content_type: draft.content_type,
      title: draft.title,
      body: draft.body,
      order: draft.order,
      is_active: draft.is_active,
    };
    try {
      if (draft.id) await updateServiceContent(service.id, draft.id, payload);
      else await createServiceContent(service.id, payload);
      setEditingId(null);
      onChanged();
    } catch {
      setError("ذخیره محتوا با خطا مواجه شد.");
    }
  }

  async function remove(content: ServiceContent) {
    if (!window.confirm(`حذف بخش «${content.title || contentTypeLabel(content.content_type)}»؟`)) return;
    await deleteServiceContent(service.id, content.id);
    onChanged();
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>محتوای سرویس</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3">
        {error ? <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive">{error}</p> : null}

        {contents.length === 0 && editingId !== "new" ? (
          <p className="rounded-xl border border-dashed bg-muted/30 p-8 text-center text-sm text-muted-foreground">
            هنوز محتوایی اضافه نشده است. بخش‌هایی مثل «معرفی»، «شرایط» و «مدارک مورد نیاز» را با ادیتور متنی بسازید.
          </p>
        ) : null}

        {contents.map((content) =>
          editingId === content.id ? (
            <ContentEditor key={content.id} initial={toDraft(content)} onSave={persist} onCancel={() => setEditingId(null)} />
          ) : (
            <div key={content.id} className="rounded-xl border bg-card p-4 shadow-sm transition-colors hover:border-primary/30">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-bold">{content.title || contentTypeLabel(content.content_type)}</span>
                    <Badge variant="default">{contentTypeLabel(content.content_type)}</Badge>
                    {content.is_active === false ? <Badge variant="outline">غیرفعال</Badge> : null}
                  </div>
                  <div
                    className="prose-content mt-2 line-clamp-2 text-xs"
                    dangerouslySetInnerHTML={{ __html: content.body }}
                  />
                </div>
                <div className="flex gap-1.5">
                  <Button size="icon" variant="ghost" onClick={() => setEditingId(content.id)} aria-label="ویرایش">
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button size="icon" variant="ghost" onClick={() => remove(content)} aria-label="حذف">
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              </div>
            </div>
          ),
        )}

        {editingId === "new" ? (
          <ContentEditor initial={toDraft(undefined, contents.length)} onSave={persist} onCancel={() => setEditingId(null)} />
        ) : (
          <Button variant="outline" className="w-fit" onClick={() => setEditingId("new")}>
            <Plus className="h-4 w-4" />
            افزودن بخش محتوا
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

function ContentEditor({
  initial,
  onSave,
  onCancel,
}: {
  initial: ContentDraft;
  onSave: (draft: ContentDraft) => void;
  onCancel: () => void;
}) {
  const [draft, setDraft] = useState<ContentDraft>(initial);
  const set = (patch: Partial<ContentDraft>) => setDraft((current) => ({ ...current, ...patch }));

  return (
    <div className="grid gap-4 rounded-xl border-2 border-primary/20 bg-muted/20 p-4">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="grid gap-1.5">
          <Label>عنوان بخش</Label>
          <Input value={draft.title} onChange={(event) => set({ title: event.target.value })} placeholder="مثلاً: شرایط دریافت تسهیلات" />
        </div>
        <div className="grid gap-1.5">
          <Label>نوع محتوا</Label>
          <Select value={draft.content_type} onChange={(event) => set({ content_type: event.target.value })}>
            {CONTENT_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </Select>
        </div>
      </div>
      <div className="grid gap-1.5">
        <Label>متن</Label>
        <RichTextEditor value={draft.body} onChange={(body) => set({ body })} placeholder="محتوای این بخش را بنویسید…" />
      </div>
      <div className="flex flex-wrap items-center gap-6">
        <Switch checked={draft.is_active} onCheckedChange={(value) => set({ is_active: value })} label="فعال" />
        <div className="grid w-28 gap-1.5">
          <Label className="text-xs text-muted-foreground">ترتیب</Label>
          <Input type="number" value={draft.order} onChange={(event) => set({ order: Number(event.target.value) })} />
        </div>
      </div>
      <div className="flex gap-2">
        <Button onClick={() => onSave(draft)}>
          <Save className="h-4 w-4" />
          ذخیره محتوا
        </Button>
        <Button variant="ghost" onClick={onCancel}>
          <X className="h-4 w-4" />
          انصراف
        </Button>
      </div>
    </div>
  );
}
