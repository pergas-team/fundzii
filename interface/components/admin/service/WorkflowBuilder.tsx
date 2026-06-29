"use client";

import { useState } from "react";
import { Pencil, Plus, Save, Trash2, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/select";
import {
  createWorkflowStep,
  deleteWorkflowStep,
  updateServiceWorkflow,
  updateWorkflowStep,
} from "@/lib/api/adminServices";
import { slugify } from "@/lib/fundzi/formFields";
import type { AdminWorkflowStep, FinancialService } from "@/types/service";

type StepDraft = {
  id?: number;
  key: string;
  title: string;
  description: string;
  order: number;
  is_initial: boolean;
  is_terminal: boolean;
  is_active: boolean;
};

function toDraft(step?: AdminWorkflowStep, order = 0): StepDraft {
  return {
    id: step?.id,
    key: step?.key ?? "",
    title: step?.title ?? "",
    description: step?.description ?? "",
    order: step?.order ?? order,
    is_initial: Boolean(step?.is_initial),
    is_terminal: Boolean(step?.is_terminal),
    is_active: step?.is_active ?? true,
  };
}

export function WorkflowBuilder({
  service,
  onChanged,
}: {
  service: FinancialService;
  onChanged: (service: FinancialService) => void;
}) {
  const workflow = service.workflow;
  const steps = [...(workflow?.steps || [])].sort((a, b) => a.order - b.order);
  const [name, setName] = useState(workflow?.name || service.title);
  const [savingName, setSavingName] = useState(false);
  const [editingId, setEditingId] = useState<number | "new" | null>(null);
  const [error, setError] = useState("");

  async function saveName() {
    setSavingName(true);
    setError("");
    try {
      onChanged(await updateServiceWorkflow(service.id, { name }));
    } catch {
      setError("ذخیره نام گردش‌کار با خطا مواجه شد.");
    } finally {
      setSavingName(false);
    }
  }

  async function persist(draft: StepDraft) {
    setError("");
    const payload: Record<string, unknown> = {
      key: draft.key || slugify(draft.title),
      title: draft.title,
      description: draft.description,
      order: draft.order,
      is_initial: draft.is_initial,
      is_terminal: draft.is_terminal,
      is_active: draft.is_active,
    };
    try {
      const saved = draft.id
        ? await updateWorkflowStep(service.id, draft.id, payload)
        : await createWorkflowStep(service.id, payload);
      onChanged(saved);
      setEditingId(null);
    } catch {
      setError("ذخیره مرحله با خطا مواجه شد.");
    }
  }

  async function remove(step: AdminWorkflowStep) {
    if (!window.confirm(`حذف مرحله «${step.title}»؟`)) return;
    onChanged(await deleteWorkflowStep(service.id, step.id));
  }

  return (
    <Card>
      <CardHeader className="gap-3">
        <CardTitle>گردش‌کار سرویس</CardTitle>
        <div className="flex flex-wrap items-end gap-2">
          <div className="grid flex-1 gap-1.5">
            <Label htmlFor="wf-name">نام گردش‌کار</Label>
            <Input id="wf-name" value={name} onChange={(event) => setName(event.target.value)} />
          </div>
          <Button variant="outline" onClick={saveName} disabled={savingName}>
            <Save className="h-4 w-4" />
            ذخیره نام
          </Button>
        </div>
      </CardHeader>
      <CardContent className="grid gap-3">
        {error ? <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive">{error}</p> : null}

        {steps.length === 0 && editingId !== "new" ? (
          <p className="rounded-xl border border-dashed bg-muted/30 p-8 text-center text-sm text-muted-foreground">
            هنوز مرحله‌ای تعریف نشده است. دقیقاً یک مرحله را به‌عنوان «مرحله شروع» علامت بزنید.
          </p>
        ) : null}

        {steps.map((step) =>
          editingId === step.id ? (
            <StepEditor key={step.id} initial={toDraft(step)} onSave={persist} onCancel={() => setEditingId(null)} />
          ) : (
            <div key={step.id} className="flex items-center gap-3 rounded-xl border bg-card p-3.5 shadow-sm">
              <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-primary/10 text-sm font-bold text-primary">
                {step.order}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-bold">{step.title}</span>
                  {step.is_initial ? <Badge variant="success">شروع</Badge> : null}
                  {step.is_terminal ? <Badge variant="accent">پایانی</Badge> : null}
                  {step.is_active === false ? <Badge variant="outline">غیرفعال</Badge> : null}
                </div>
                <p className="mt-1 truncate text-xs text-muted-foreground" dir="ltr">{step.key}</p>
              </div>
              <div className="flex gap-1.5">
                <Button size="icon" variant="ghost" onClick={() => setEditingId(step.id)} aria-label="ویرایش">
                  <Pencil className="h-4 w-4" />
                </Button>
                <Button size="icon" variant="ghost" onClick={() => remove(step)} aria-label="حذف">
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>
            </div>
          ),
        )}

        {editingId === "new" ? (
          <StepEditor initial={toDraft(undefined, steps.length)} onSave={persist} onCancel={() => setEditingId(null)} />
        ) : (
          <Button variant="outline" className="w-fit" onClick={() => setEditingId("new")}>
            <Plus className="h-4 w-4" />
            افزودن مرحله
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

function StepEditor({
  initial,
  onSave,
  onCancel,
}: {
  initial: StepDraft;
  onSave: (draft: StepDraft) => void;
  onCancel: () => void;
}) {
  const [draft, setDraft] = useState<StepDraft>(initial);
  const set = (patch: Partial<StepDraft>) => setDraft((current) => ({ ...current, ...patch }));

  return (
    <div className="grid gap-4 rounded-xl border-2 border-primary/20 bg-muted/20 p-4">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="grid gap-1.5">
          <Label>عنوان مرحله *</Label>
          <Input
            value={draft.title}
            onChange={(event) => {
              const title = event.target.value;
              set(draft.key === slugify(draft.title) || draft.key === "" ? { title, key: slugify(title) } : { title });
            }}
            placeholder="مثلاً: بررسی اولیه"
          />
        </div>
        <div className="grid gap-1.5">
          <Label>شناسه (key) *</Label>
          <Input dir="ltr" value={draft.key} onChange={(event) => set({ key: event.target.value })} placeholder="initial_review" />
        </div>
        <div className="grid gap-1.5">
          <Label>ترتیب</Label>
          <Input type="number" value={draft.order} onChange={(event) => set({ order: Number(event.target.value) })} />
        </div>
      </div>
      <div className="flex flex-wrap gap-6">
        <Switch checked={draft.is_initial} onCheckedChange={(value) => set({ is_initial: value })} label="مرحله شروع" />
        <Switch checked={draft.is_terminal} onCheckedChange={(value) => set({ is_terminal: value })} label="مرحله پایانی" />
        <Switch checked={draft.is_active} onCheckedChange={(value) => set({ is_active: value })} label="فعال" />
      </div>
      <div className="flex gap-2">
        <Button onClick={() => onSave(draft)} disabled={!draft.title.trim()}>
          <Save className="h-4 w-4" />
          ذخیره مرحله
        </Button>
        <Button variant="ghost" onClick={onCancel}>
          <X className="h-4 w-4" />
          انصراف
        </Button>
      </div>
    </div>
  );
}
