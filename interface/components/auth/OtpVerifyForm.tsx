"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { verifyOtp } from "@/lib/api/auth";
import { useAuthStore } from "@/lib/auth/session";

export function OtpVerifyForm() {
  const router = useRouter();
  const params = useSearchParams();
  const setUser = useAuthStore((state) => state.setUser);
  const [phone, setPhone] = useState(params.get("phone") || "");
  const [code, setCode] = useState("123456");
  const [error, setError] = useState("");
  const [isLoading, setLoading] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const response = await verifyOtp(phone, code);
      setUser(response.user);
      if (response.user.role === "admin") router.push("/admin");
      else if (response.user.role === "operator") router.push("/operator");
      else router.push("/dashboard");
    } catch {
      setError("کد ورود معتبر نیست.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid gap-6">
      <div className="grid gap-1.5">
        <span className="grid h-12 w-12 place-items-center rounded-xl bg-primary/10 text-primary">
          <ShieldCheck className="h-6 w-6" />
        </span>
        <h1 className="mt-2 text-2xl font-extrabold tracking-tight">تأیید ورود</h1>
        <p className="text-sm text-muted-foreground">
          کد ارسال‌شده را وارد کنید. کد نمایشی نسخه‌ی دمو برابر <span className="font-bold text-foreground">۱۲۳۴۵۶</span> است.
        </p>
      </div>
      <form className="grid gap-4" onSubmit={onSubmit}>
        <div className="grid gap-2">
          <Label htmlFor="phone">شماره موبایل</Label>
          <Input id="phone" value={phone} onChange={(event) => setPhone(event.target.value)} dir="ltr" className="text-left" required />
        </div>
        <div className="grid gap-2">
          <Label htmlFor="otp">کد ورود</Label>
          <Input
            id="otp"
            value={code}
            onChange={(event) => setCode(event.target.value)}
            dir="ltr"
            className="text-center text-lg font-bold tracking-[0.4em]"
            required
          />
        </div>
        {error ? (
          <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive">{error}</p>
        ) : null}
        <Button type="submit" size="lg" disabled={isLoading || !phone || !code}>
          {isLoading ? "در حال بررسی..." : "ورود"}
        </Button>
      </form>
    </div>
  );
}
