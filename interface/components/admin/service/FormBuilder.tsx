"use client";

import { useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  GripVertical,
  Pencil,
  Plus,
  Save,
  Trash2,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, Switch } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import {
  createServiceField,
  deleteServiceField,
  updateServiceField,
  updateServiceForm,
} from "@/lib/api/adminServices";
import {
  FIELD_TYPES,
  fieldTypeMeta,
  fieldTypeLabel,
  fromOptionPairs,
  slugify,
  toOptionPairs,
  type OptionPair,
} from "@/lib/fundzi/formFields";
import type { AdminDynamicFormField, FinancialService } from "@/types/service";

type FieldDraft = {
  id?: number;
  label: string;
  key: string;
  field_type: string;
  required: boolean;
  is_active: boolean;
  placeholder: string;
  help_text: string;
  order: number;
  options: OptionPair[];
  validation_config: Record<string, unknown>;
};

function toDraft(field?: AdminDynamicFormField, order = 0): FieldDraft {
  return {
    id: field?.id,
    label: field?.label ?? "",
    key: field?.key ?? "",
    field_type: field?.field_type ?? field?.type ?? "text",
    required: Boolean(field?.required),
    is_active: field?.is_active ?? true,
    placeholder: field?.placeholder ?? "",
    help_text: field?.help_text ?? "",
    order: field?.order ?? order,
    options: toOptionPairs(field?.options),
    validation_config: (field?.validation_config as Record<string, unknown>) ?? {},
  };
}

export function FormBuilder({
  service,
  onChanged,
}: {
  service: FinancialService;
  onChanged: (service: FinancialService) => void;
}) {
  const form = service.form;
  const fields = [...(form?.fields || [])].sort((a, b) => a.order - b.order);
  const [editingId, setEditingId] = useState<number | "new" | null>(null);
  const [title, setTitle] = useState(form?.title || service.title);
  const [savingTitle, setSavingTitle] = useState(false);
  const [error, setError] = useState("");

  async function saveTitle() {
    setSavingTitle(true);
    setError("");
    try {
      onChanged(await updateServiceForm(service.id, { title }));
    } catch {
      setError("ذخیره عنوان فرم با خطا مواجه شد.");
    } finally {
      setSavingTitle(false);
    }
  }

  async function persist(draft: FieldDraft) {
    setError("");
    const meta = fieldTypeMeta(draft.field_type);
    const payload: Record<string, unknown> = {
      label: draft.label,
      key: draft.key || slugify(draft.label),
      field_type: draft.field_type,
      required: draft.required,
      is_active: draft.is_active,
      placeholder: draft.placeholder,
      help_text: draft.help_text,
      order: draft.order,
      options: meta.hasOptions ? fromOptionPairs(draft.options) : [],
      validation_config: draft.validation_config,
    };
    try {
      const saved = draft.id
        ? await updateServiceField(service.id, draft.id, payload)
        : await createServiceField(service.id, payload);
      onChanged(saved);
      setEditingId(null);
    } catch {
      setError("ذخیره فیلد با خطا مواجه شد. برچسب، شناسه و نوع را بررسی کنید.");
    }
  }

  async function remove(field: AdminDynamicFormField) {
    if (!window.confirm(`حذف فیلد «${field.label}»؟`)) return;
    onChanged(await deleteServiceField(service.id, field.id));
  }

  async function move(field: AdminDynamicFormField, direction: -1 | 1) {
    const index = fields.findIndex((item) => item.id === field.id);
    const swap = fields[index + direction];
    if (!swap) return;
    await updateServiceField(service.id, field.id, { order: swap.order });
    const latest = await updateServiceField(service.id, swap.id, { order: field.order });
    onChanged(latest);
  }

  return (
    <Card>
      <CardHeader className="gap-3">
        <CardTitle>فرم‌ساز سرویس</CardTitle>
        <div className="flex flex-wrap items-end gap-2">
          <div className="grid flex-1 gap-1.5">
            <Label htmlFor="form-title">عنوان فرم</Label>
            <Input id="form-title" value={title} onChange={(event) => setTitle(event.target.value)} />
          </div>
          <Button variant="outline" onClick={saveTitle} disabled={savingTitle}>
            <Save className="h-4 w-4" />
            ذخیره عنوان
          </Button>
        </div>
      </CardHeader>
      <CardContent className="grid gap-3">
        {error ? <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive">{error}</p> : null}

        {fields.length === 0 && editingId !== "new" ? (
          <p className="rounded-xl border border-dashed bg-muted/30 p-8 text-center text-sm text-muted-foreground">
            هنوز فیلدی تعریف نشده است. با دکمه «افزودن فیلد» اولین فیلد را بسازید.
          </p>
        ) : null}

        {fields.map((field, index) =>
          editingId === field.id ? (
            <FieldEditor
              key={field.id}
              initial={toDraft(field)}
              onSave={persist}
              onCancel={() => setEditingId(null)}
            />
          ) : (
            <div
              key={field.id}
              className="flex items-center gap-3 rounded-xl border bg-card p-3.5 shadow-sm transition-colors hover:border-primary/30"
            >
              <div className="flex flex-col">
                <button
                  type="button"
                  disabled={index === 0}
                  onClick={() => move(field, -1)}
                  className="text-muted-foreground hover:text-foreground disabled:opacity-30"
                  aria-label="بالا"
                >
                  <ChevronUp className="h-4 w-4" />
                </button>
                <GripVertical className="h-4 w-4 text-muted-foreground/50" />
                <button
                  type="button"
                  disabled={index === fields.length - 1}
                  onClick={() => move(field, 1)}
                  className="text-muted-foreground hover:text-foreground disabled:opacity-30"
                  aria-label="پایین"
                >
                  <ChevronDown className="h-4 w-4" />
                </button>
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-bold">{field.label || "بدون عنوان"}</span>
                  <Badge variant="info">{fieldTypeLabel(field.field_type || field.type)}</Badge>
                  {field.required ? <Badge variant="warning">الزامی</Badge> : null}
                  {field.is_active === false ? <Badge variant="outline">غیرفعال</Badge> : null}
                </div>
                <p className="mt-1 truncate text-xs text-muted-foreground" dir="ltr">
                  {field.key}
                  {Array.isArray(field.options) && field.options.length ? ` · ${field.options.length} گزینه` : ""}
                </p>
              </div>
              <div className="flex gap-1.5">
                <Button size="icon" variant="ghost" onClick={() => setEditingId(field.id)} aria-label="ویرایش">
                  <Pencil className="h-4 w-4" />
                </Button>
                <Button size="icon" variant="ghost" onClick={() => remove(field)} aria-label="حذف">
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>
            </div>
          ),
        )}

        {editingId === "new" ? (
          <FieldEditor
            initial={toDraft(undefined, fields.length)}
            onSave={persist}
            onCancel={() => setEditingId(null)}
          />
        ) : (
          <Button variant="outline" className="w-fit" onClick={() => setEditingId("new")}>
            <Plus className="h-4 w-4" />
            افزودن فیلد
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

function FieldEditor({
  initial,
  onSave,
  onCancel,
}: {
  initial: FieldDraft;
  onSave: (draft: FieldDraft) => void;
  onCancel: () => void;
}) {
  const [draft, setDraft] = useState<FieldDraft>(initial);
  const meta = fieldTypeMeta(draft.field_type);
  const set = (patch: Partial<FieldDraft>) => setDraft((current) => ({ ...current, ...patch }));

  return (
    <div className="grid gap-4 rounded-xl border-2 border-primary/20 bg-muted/20 p-4">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="grid gap-1.5">
          <Label>برچسب فیلد *</Label>
          <Input
            value={draft.label}
            onChange={(event) => {
              const label = event.target.value;
              // Auto-fill key from the label until the user edits the key manually.
              set(draft.key === slugify(draft.label) || draft.key === "" ? { label, key: slugify(label) } : { label });
            }}
            placeholder="مثلاً: مبلغ درخواستی"
          />
        </div>
        <div className="grid gap-1.5">
          <Label>شناسه فیلد (key) *</Label>
          <Input dir="ltr" value={draft.key} onChange={(event) => set({ key: event.target.value })} placeholder="requested_amount" />
        </div>
        <div className="grid gap-1.5">
          <Label>نوع فیلد *</Label>
          <Select value={draft.field_type} onChange={(event) => set({ field_type: event.target.value })}>
            {FIELD_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </Select>
        </div>
        <div className="grid gap-1.5">
          <Label>ترتیب نمایش</Label>
          <Input
            type="number"
            value={draft.order}
            onChange={(event) => set({ order: Number(event.target.value) })}
          />
        </div>
        <div className="grid gap-1.5">
          <Label>متن راهنمای داخل فیلد (placeholder)</Label>
          <Input value={draft.placeholder} onChange={(event) => set({ placeholder: event.target.value })} />
        </div>
        <div className="grid gap-1.5">
          <Label>توضیح کمکی (help text)</Label>
          <Input value={draft.help_text} onChange={(event) => set({ help_text: event.target.value })} />
        </div>
      </div>

      <div className="flex flex-wrap gap-6">
        <Switch checked={draft.required} onCheckedChange={(value) => set({ required: value })} label="فیلد الزامی" />
        <Switch checked={draft.is_active} onCheckedChange={(value) => set({ is_active: value })} label="فعال" />
      </div>

      {meta.hasOptions ? (
        <OptionsEditor options={draft.options} onChange={(options) => set({ options })} />
      ) : null}

      <ValidationEditor
        capabilities={meta.validations || []}
        value={draft.validation_config}
        onChange={(validation_config) => set({ validation_config })}
      />

      <div className="flex gap-2">
        <Button onClick={() => onSave(draft)} disabled={!draft.label.trim()}>
          <Save className="h-4 w-4" />
          ذخیره فیلد
        </Button>
        <Button variant="ghost" onClick={onCancel}>
          <X className="h-4 w-4" />
          انصراف
        </Button>
      </div>
    </div>
  );
}

function OptionsEditor({ options, onChange }: { options: OptionPair[]; onChange: (options: OptionPair[]) => void }) {
  function update(index: number, patch: Partial<OptionPair>) {
    onChange(options.map((option, i) => (i === index ? { ...option, ...patch } : option)));
  }
  return (
    <div className="grid gap-2 rounded-lg border bg-card p-3.5">
      <Label>گزینه‌ها</Label>
      {options.length === 0 ? (
        <p className="text-xs text-muted-foreground">حداقل یک گزینه اضافه کنید.</p>
      ) : null}
      {options.map((option, index) => (
        <div key={index} className="flex items-center gap-2">
          <Input
            value={option.label}
            onChange={(event) => {
              const label = event.target.value;
              update(index, option.value === slugify(option.label) || option.value === "" ? { label, value: slugify(label) } : { label });
            }}
            placeholder="عنوان گزینه"
          />
          <Input
            dir="ltr"
            value={option.value}
            onChange={(event) => update(index, { value: event.target.value })}
            placeholder="value"
            className="max-w-[40%]"
          />
          <Button
            size="icon"
            variant="ghost"
            onClick={() => onChange(options.filter((_, i) => i !== index))}
            aria-label="حذف گزینه"
          >
            <Trash2 className="h-4 w-4 text-destructive" />
          </Button>
        </div>
      ))}
      <Button size="sm" variant="outline" className="w-fit" onClick={() => onChange([...options, { label: "", value: "" }])}>
        <Plus className="h-4 w-4" />
        افزودن گزینه
      </Button>
    </div>
  );
}

function ValidationEditor({
  capabilities,
  value,
  onChange,
}: {
  capabilities: Array<"length" | "pattern" | "numeric" | "selections">;
  value: Record<string, unknown>;
  onChange: (value: Record<string, unknown>) => void;
}) {
  if (!capabilities.length) return null;

  function setNum(key: string, raw: string) {
    const next = { ...value };
    if (raw.trim() === "") delete next[key];
    else next[key] = Number(raw);
    onChange(next);
  }
  function setStr(key: string, raw: string) {
    const next = { ...value };
    if (raw.trim() === "") delete next[key];
    else next[key] = raw;
    onChange(next);
  }
  const num = (key: string) => (value[key] === undefined ? "" : String(value[key]));
  const str = (key: string) => (value[key] === undefined ? "" : String(value[key]));

  return (
    <div className="grid gap-3 rounded-lg border bg-card p-3.5">
      <Label>قواعد اعتبارسنجی</Label>
      <div className="grid gap-3 sm:grid-cols-2">
        {capabilities.includes("numeric") ? (
          <>
            <Field label="حداقل مقدار">
              <Input type="number" value={num("min")} onChange={(event) => setNum("min", event.target.value)} />
            </Field>
            <Field label="حداکثر مقدار">
              <Input type="number" value={num("max")} onChange={(event) => setNum("max", event.target.value)} />
            </Field>
            <div className="sm:col-span-2">
              <Switch
                checked={Boolean(value.integer)}
                onCheckedChange={(checked) => {
                  const next = { ...value };
                  if (checked) next.integer = true;
                  else delete next.integer;
                  onChange(next);
                }}
                label="فقط عدد صحیح"
              />
            </div>
          </>
        ) : null}
        {capabilities.includes("length") ? (
          <>
            <Field label="حداقل تعداد نویسه">
              <Input type="number" value={num("min_length")} onChange={(event) => setNum("min_length", event.target.value)} />
            </Field>
            <Field label="حداکثر تعداد نویسه">
              <Input type="number" value={num("max_length")} onChange={(event) => setNum("max_length", event.target.value)} />
            </Field>
          </>
        ) : null}
        {capabilities.includes("selections") ? (
          <>
            <Field label="حداقل تعداد انتخاب">
              <Input type="number" value={num("min_selections")} onChange={(event) => setNum("min_selections", event.target.value)} />
            </Field>
            <Field label="حداکثر تعداد انتخاب">
              <Input type="number" value={num("max_selections")} onChange={(event) => setNum("max_selections", event.target.value)} />
            </Field>
          </>
        ) : null}
        {capabilities.includes("pattern") ? (
          <>
            <Field label="الگوی مجاز (Regex)">
              <Input dir="ltr" value={str("pattern")} onChange={(event) => setStr("pattern", event.target.value)} placeholder="^09\\d{9}$" />
            </Field>
            <Field label="پیام خطای الگو">
              <Input value={str("pattern_message")} onChange={(event) => setStr("pattern_message", event.target.value)} placeholder="قالب واردشده معتبر نیست." />
            </Field>
          </>
        ) : null}
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-1.5">
      <Label className="text-xs font-medium text-muted-foreground">{label}</Label>
      {children}
    </div>
  );
}
