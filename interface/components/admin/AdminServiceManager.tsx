"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { ChevronDown, FileText, LayoutGrid, ListChecks, Plus, Settings2, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, Switch } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { ContentManager } from "@/components/admin/service/ContentManager";
import { FormBuilder } from "@/components/admin/service/FormBuilder";
import { WorkflowBuilder } from "@/components/admin/service/WorkflowBuilder";
import {
  createAdminService,
  deleteAdminService,
  listAdminServices,
  updateAdminService,
} from "@/lib/api/adminServices";
import { SERVICE_TYPES, slugify } from "@/lib/fundzi/formFields";
import type { FinancialService } from "@/types/service";

const serviceSchema = z.object({
  title: z.string().min(1, "عنوان الزامی است"),
  slug: z.string().min(1, "شناسه (slug) الزامی است"),
  short_description: z.string().optional(),
  full_description: z.string().optional(),
  service_type: z.string().min(1),
  order: z.coerce.number().min(0),
  is_active: z.boolean(),
  rules_config: z.string(),
  metadata: z.string(),
});

type ServiceFormValues = z.infer<typeof serviceSchema>;
type Tab = "base" | "content" | "form" | "workflow";

const TABS: Array<{ id: Tab; label: string; icon: React.ComponentType<{ className?: string }> }> = [
  { id: "base", label: "اطلاعات پایه", icon: Settings2 },
  { id: "content", label: "محتوا", icon: FileText },
  { id: "form", label: "فرم‌ساز", icon: LayoutGrid },
  { id: "workflow", label: "گردش‌کار", icon: ListChecks },
];

export function AdminServiceManager() {
  const [services, setServices] = useState<FinancialService[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [tab, setTab] = useState<Tab>("base");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const selected = useMemo(() => services.find((item) => item.id === selectedId) || null, [services, selectedId]);
  const form = useForm<ServiceFormValues>({ resolver: zodResolver(serviceSchema), defaultValues: emptyServiceValues() });

  const load = useCallback(() => {
    setError("");
    listAdminServices()
      .then((response) => {
        setServices(response.results);
        setSelectedId((current) => current || response.results[0]?.id || null);
      })
      .catch(() => setError("دریافت سرویس‌ها با خطا مواجه شد."));
  }, []);

  useEffect(() => load(), [load]);
  useEffect(() => {
    form.reset(selected ? serviceToValues(selected) : emptyServiceValues());
  }, [selected, form]);

  async function saveBase(values: ServiceFormValues) {
    setError("");
    setMessage("");
    let rules_config: Record<string, unknown>;
    let metadata: Record<string, unknown>;
    try {
      rules_config = parseJson(values.rules_config, {});
      metadata = parseJson(values.metadata, {});
    } catch {
      setError("قواعد (rules_config) یا metadata یک JSON معتبر نیست.");
      return;
    }
    try {
      const payload = { ...values, rules_config, metadata };
      const saved = selected ? await updateAdminService(selected.id, payload) : await createAdminService(payload);
      setServices((current) => (selected ? current.map((item) => (item.id === saved.id ? saved : item)) : [saved, ...current]));
      setSelectedId(saved.id);
      setMessage("اطلاعات سرویس ذخیره شد.");
    } catch {
      setError("ذخیره سرویس با خطا مواجه شد.");
    }
  }

  async function removeService() {
    if (!selected || !window.confirm(`حذف سرویس «${selected.title}»؟`)) return;
    try {
      await deleteAdminService(selected.id);
      setServices((current) => current.filter((item) => item.id !== selected.id));
      setSelectedId(null);
    } catch {
      setError("حذف سرویس ممکن نیست (احتمالاً درخواست ثبت‌شده دارد).");
    }
  }

  function mergeService(service: FinancialService) {
    setServices((current) => current.map((item) => (item.id === service.id ? service : item)));
  }

  const titleValue = form.watch("title");

  return (
    <div className="grid gap-5 lg:grid-cols-[280px_1fr]">
      <Card className="lg:sticky lg:top-20 lg:self-start">
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle className="text-base">سرویس‌ها</CardTitle>
          <Button size="sm" variant="outline" onClick={() => { setSelectedId(null); setTab("base"); }}>
            <Plus className="h-4 w-4" />
            جدید
          </Button>
        </CardHeader>
        <CardContent className="grid gap-2">
          {services.map((service) => (
            <button
              key={service.id}
              type="button"
              onClick={() => setSelectedId(service.id)}
              className={cn(
                "rounded-lg border px-3 py-2.5 text-right text-sm transition-colors",
                selectedId === service.id ? "border-primary bg-primary/10" : "border-border hover:bg-muted",
              )}
            >
              <span className="block font-bold">{service.title}</span>
              <span className="text-xs text-muted-foreground" dir="ltr">{service.slug}</span>
            </button>
          ))}
          {!services.length ? <p className="text-sm text-muted-foreground">هنوز سرویسی ثبت نشده است.</p> : null}
        </CardContent>
      </Card>

      <div className="grid gap-4">
        <div className="flex flex-wrap gap-1 rounded-xl border bg-card p-1.5 shadow-card">
          {TABS.map((item) => {
            const disabled = item.id !== "base" && !selected;
            return (
              <button
                key={item.id}
                type="button"
                disabled={disabled}
                onClick={() => setTab(item.id)}
                className={cn(
                  "flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold transition-colors disabled:opacity-40",
                  tab === item.id ? "bg-primary text-primary-foreground shadow-soft" : "text-muted-foreground hover:bg-muted",
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </button>
            );
          })}
        </div>

        {error ? <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive">{error}</p> : null}
        {message ? <p className="rounded-lg bg-success/10 px-3 py-2 text-sm font-medium text-success">{message}</p> : null}

        {tab === "base" ? (
          <Card>
            <CardHeader>
              <CardTitle>{selected ? "ویرایش اطلاعات پایه" : "سرویس جدید"}</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={form.handleSubmit(saveBase)} className="grid gap-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="grid gap-1.5">
                    <Label>عنوان *</Label>
                    <Input
                      {...form.register("title")}
                      onChange={(event) => {
                        form.setValue("title", event.target.value);
                        const currentSlug = form.getValues("slug");
                        if (!selected && (currentSlug === "" || currentSlug === slugify(titleValue))) {
                          form.setValue("slug", slugify(event.target.value));
                        }
                      }}
                      placeholder="عنوان سرویس"
                    />
                    {form.formState.errors.title ? <p className="text-xs text-destructive">{form.formState.errors.title.message}</p> : null}
                  </div>
                  <div className="grid gap-1.5">
                    <Label>شناسه (slug) *</Label>
                    <Input dir="ltr" {...form.register("slug")} placeholder="gold-backed-financing" />
                  </div>
                  <div className="grid gap-1.5">
                    <Label>نوع سرویس</Label>
                    <Select {...form.register("service_type")}>
                      {SERVICE_TYPES.map((type) => (
                        <option key={type.value} value={type.value}>
                          {type.label}
                        </option>
                      ))}
                    </Select>
                  </div>
                  <div className="grid gap-1.5">
                    <Label>ترتیب نمایش</Label>
                    <Input type="number" {...form.register("order")} />
                  </div>
                </div>
                <div className="grid gap-1.5">
                  <Label>توضیح کوتاه</Label>
                  <Textarea {...form.register("short_description")} placeholder="یک خط توضیح که در کارت سرویس نمایش داده می‌شود." />
                </div>
                <div className="grid gap-1.5">
                  <Label>توضیح کامل</Label>
                  <Textarea {...form.register("full_description")} placeholder="توضیح کامل سرویس که در صفحه جزئیات نمایش داده می‌شود." />
                </div>

                <Switch
                  checked={form.watch("is_active")}
                  onCheckedChange={(value) => form.setValue("is_active", value)}
                  label="سرویس فعال است"
                />

                <div className="rounded-xl border bg-muted/20">
                  <button
                    type="button"
                    onClick={() => setShowAdvanced((value) => !value)}
                    className="flex w-full items-center justify-between px-4 py-3 text-sm font-semibold"
                  >
                    تنظیمات پیشرفته (JSON)
                    <ChevronDown className={cn("h-4 w-4 transition-transform", showAdvanced && "rotate-180")} />
                  </button>
                  {showAdvanced ? (
                    <div className="grid gap-4 border-t p-4">
                      <div className="grid gap-1.5">
                        <Label>قواعد سرویس (rules_config)</Label>
                        <Textarea dir="ltr" className="font-mono text-xs" rows={5} {...form.register("rules_config")} />
                        <p className="text-xs text-muted-foreground">مثلاً سقف LTV، مناطق مجاز یا مدت‌های قابل‌قبول.</p>
                      </div>
                      <div className="grid gap-1.5">
                        <Label>متادیتا (metadata)</Label>
                        <Textarea dir="ltr" className="font-mono text-xs" rows={4} {...form.register("metadata")} />
                      </div>
                    </div>
                  ) : null}
                </div>

                <div className="flex flex-wrap gap-2">
                  <Button type="submit">ذخیره سرویس</Button>
                  {selected ? (
                    <Button type="button" variant="destructive" onClick={removeService}>
                      <Trash2 className="h-4 w-4" />
                      حذف سرویس
                    </Button>
                  ) : null}
                </div>
              </form>
            </CardContent>
          </Card>
        ) : selected ? (
          <>
            {tab === "content" ? <ContentManager service={selected} onChanged={load} /> : null}
            {tab === "form" ? <FormBuilder service={selected} onChanged={mergeService} /> : null}
            {tab === "workflow" ? <WorkflowBuilder service={selected} onChanged={mergeService} /> : null}
          </>
        ) : (
          <p className="rounded-xl border bg-card p-8 text-center text-muted-foreground shadow-card">
            برای مدیریت این بخش ابتدا یک سرویس را انتخاب یا ایجاد کنید.
          </p>
        )}
      </div>
    </div>
  );
}

function emptyServiceValues(): ServiceFormValues {
  return {
    title: "",
    slug: "",
    short_description: "",
    full_description: "",
    service_type: "other",
    order: 0,
    is_active: true,
    rules_config: "{}",
    metadata: "{}",
  };
}

function serviceToValues(service: FinancialService): ServiceFormValues {
  return {
    title: service.title,
    slug: service.slug,
    short_description: service.short_description || "",
    full_description: service.full_description || "",
    service_type: service.service_type || "other",
    order: service.order || 0,
    is_active: Boolean(service.is_active),
    rules_config: JSON.stringify(service.rules_config || {}, null, 2),
    metadata: JSON.stringify(service.metadata || {}, null, 2),
  };
}

function parseJson<T>(value: string | undefined, fallback: T): T {
  if (!value || !value.trim()) return fallback;
  return JSON.parse(value) as T;
}
