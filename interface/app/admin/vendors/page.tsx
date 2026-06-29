"use client";

import { useCallback, useEffect, useState } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { RoleGuard } from "@/components/layout/RoleGuard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { createVendor, deleteVendor, listVendors, updateVendor } from "@/lib/api/vendors";
import { formatCurrency } from "@/lib/utils/formatCurrency";
import type { Vendor } from "@/types/vendor";

const emptyVendor: Omit<Vendor, "id"> = {
  name: "",
  type: "",
  service_categories: [],
  accepted_collateral_types: [],
  min_amount: "",
  max_amount: "",
  is_active: true,
  description: "",
};

export default function AdminVendorsPage() {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [selected, setSelected] = useState<Vendor | Omit<Vendor, "id">>(emptyVendor);
  const [q, setQ] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(() => {
    setError("");
    listVendors({ q }).then((response) => setVendors(response.results)).catch(() => setError("دریافت همکاران مالی با خطا مواجه شد."));
  }, [q]);

  useEffect(() => load(), [load]);

  function updateSelected(patch: Partial<Vendor>) {
    setSelected((current) => ({ ...current, ...patch }));
  }

  async function save() {
    const payload = {
      ...selected,
      service_categories: parseCsv(selected.service_categories),
      accepted_collateral_types: parseCsv(selected.accepted_collateral_types),
    };
    const saved = "id" in selected ? await updateVendor(selected.id, payload) : await createVendor(payload);
    setVendors((current) => ("id" in selected ? current.map((item) => (item.id === saved.id ? saved : item)) : [saved, ...current]));
    setSelected(emptyVendor);
  }

  async function remove(id: number) {
    await deleteVendor(id);
    setVendors((current) => current.filter((item) => item.id !== id));
    setSelected(emptyVendor);
  }

  return (
    <RoleGuard roles={["admin"]}>
      <DashboardShell mode="admin" title="همکاران مالی">
        <div className="grid gap-4">
          <Card>
            <CardContent className="grid gap-3 pt-5 md:grid-cols-[1fr_auto]">
              <Input value={q} onChange={(event) => setQ(event.target.value)} placeholder="جستجوی نام یا نوع همکار" />
              <Button onClick={load}>جستجو</Button>
            </CardContent>
          </Card>
          {error ? <p className="text-destructive">{error}</p> : null}
          <div className="grid gap-4 lg:grid-cols-[1fr_380px]">
            <Card className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>نام</TableHead>
                    <TableHead>نوع</TableHead>
                    <TableHead>بازه مبلغ</TableHead>
                    <TableHead>وضعیت</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {vendors.map((vendor) => (
                    <TableRow key={vendor.id}>
                      <TableCell>{vendor.name}</TableCell>
                      <TableCell>{vendor.type || "-"}</TableCell>
                      <TableCell>{formatCurrency(vendor.min_amount)} تا {formatCurrency(vendor.max_amount)}</TableCell>
                      <TableCell>{vendor.is_active ? "فعال" : "غیرفعال"}</TableCell>
                      <TableCell className="flex gap-2">
                        <Button size="sm" variant="outline" onClick={() => setSelected(vendor)}>ویرایش</Button>
                        <Button size="sm" variant="destructive" onClick={() => remove(vendor.id)}>حذف</Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
            <Card>
              <CardHeader><CardTitle>{"id" in selected ? "ویرایش همکار" : "همکار جدید"}</CardTitle></CardHeader>
              <CardContent className="grid gap-3">
                <Input value={selected.name} onChange={(event) => updateSelected({ name: event.target.value })} placeholder="نام" />
                <Input value={selected.type || ""} onChange={(event) => updateSelected({ type: event.target.value })} placeholder="نوع" />
                <Input value={String(selected.min_amount ?? "")} onChange={(event) => updateSelected({ min_amount: event.target.value })} placeholder="حداقل مبلغ" />
                <Input value={String(selected.max_amount ?? "")} onChange={(event) => updateSelected({ max_amount: event.target.value })} placeholder="حداکثر مبلغ" />
                <Input value={arrayText(selected.service_categories)} onChange={(event) => updateSelected({ service_categories: event.target.value.split(",").map((item) => item.trim()).filter(Boolean) })} placeholder="دسته‌های سرویس با کاما" />
                <Input value={arrayText(selected.accepted_collateral_types)} onChange={(event) => updateSelected({ accepted_collateral_types: event.target.value.split(",").map((item) => item.trim()).filter(Boolean) })} placeholder="وثیقه‌های قابل قبول با کاما" />
                <Textarea value={selected.description || ""} onChange={(event) => updateSelected({ description: event.target.value })} placeholder="توضیحات" />
                <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={Boolean(selected.is_active)} onChange={(event) => updateSelected({ is_active: event.target.checked })} /> فعال</label>
                <div className="flex gap-2">
                  <Button onClick={save}>ذخیره</Button>
                  <Button variant="outline" onClick={() => setSelected(emptyVendor)}>فرم جدید</Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </DashboardShell>
    </RoleGuard>
  );
}

function arrayText(value: unknown) {
  return Array.isArray(value) ? value.join(", ") : String(value || "");
}

function parseCsv(value: unknown) {
  if (Array.isArray(value)) return value;
  return String(value || "").split(",").map((item) => item.trim()).filter(Boolean);
}
