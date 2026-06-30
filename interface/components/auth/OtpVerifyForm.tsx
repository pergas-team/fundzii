"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
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

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
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
    <form className="grid gap-4" onSubmit={onSubmit}>
      <p className="text-sm text-muted-foreground">
        کد ارسال‌شده به شماره خود را وارد کنید.{" "}
        <span className="font-bold text-foreground">کد دمو: ۱۲۳۴۵۶</span>
      </p>
      <div className="grid gap-2">
        <Label htmlFor="phone">شماره موبایل</Label>
        <Input
          id="phone"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          dir="ltr"
          className="text-left"
          required
        />
      </div>
      <div className="grid gap-2">
        <Label htmlFor="otp">کد ورود</Label>
        <Input
          id="otp"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          dir="ltr"
          className="text-center text-xl font-bold tracking-[0.5em]"
          required
        />
      </div>
      {error ? (
        <p className="rounded-xl border border-destructive/20 bg-destructive/10 px-3 py-2.5 text-sm font-medium text-destructive">
          {error}
        </p>
      ) : null}
      <Button type="submit" size="lg" disabled={isLoading || !phone || !code}>
        {isLoading ? "در حال بررسی..." : "ورود به حساب"}
      </Button>
    </form>
  );
}
