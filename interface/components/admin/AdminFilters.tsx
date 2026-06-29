"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { AdminRequestFilters } from "@/types/admin";

export function AdminFilters({ onApply }: { onApply: (filters: AdminRequestFilters) => void }) {
  function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    onApply({
      tracking_code: String(formData.get("tracking_code") || ""),
      user_phone: String(formData.get("user_phone") || ""),
      service: String(formData.get("service") || ""),
      status: String(formData.get("status") || ""),
      q: String(formData.get("q") || ""),
      ordering: String(formData.get("ordering") || "-submitted_at"),
    });
  }

  return (
    <form onSubmit={submit} className="grid gap-3 rounded-xl border bg-card p-4 shadow-card md:grid-cols-3 xl:grid-cols-7">
      <Input name="q" placeholder="جستجوی کلی" />
      <Input name="tracking_code" placeholder="کد پیگیری" />
      <Input name="user_phone" placeholder="شماره کاربر" />
      <Input name="service" placeholder="slug سرویس" />
      <Input name="status" placeholder="وضعیت" />
      <select
        name="ordering"
        className="h-11 rounded-lg border border-input bg-card px-3.5 text-sm shadow-sm outline-none transition-colors focus-visible:border-ring/60 focus-visible:ring-2 focus-visible:ring-ring/40"
      >
        <option value="-submitted_at">جدیدترین</option>
        <option value="submitted_at">قدیمی‌ترین</option>
        <option value="current_status">وضعیت صعودی</option>
        <option value="-current_status">وضعیت نزولی</option>
      </select>
      <Button type="submit">اعمال فیلتر</Button>
    </form>
  );
}
