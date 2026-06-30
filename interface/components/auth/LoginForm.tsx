"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Phone } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { sendOtp } from "@/lib/api/auth";

export function LoginForm() {
  const router = useRouter();
  const [phone, setPhone] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setLoading] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await sendOtp(phone);
      router.push(`/auth/verify?phone=${encodeURIComponent(phone)}`);
    } catch {
      setError("ارسال کد ورود با خطا مواجه شد.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="grid gap-4" onSubmit={onSubmit}>
      <div className="grid gap-2">
        <Label htmlFor="phone">شماره موبایل</Label>
        <div className="relative">
          <Phone className="pointer-events-none absolute right-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            id="phone"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="09120000000"
            required
            dir="ltr"
            className="pr-10 text-left"
          />
        </div>
      </div>
      {error ? (
        <p className="rounded-xl border border-destructive/20 bg-destructive/10 px-3 py-2.5 text-sm font-medium text-destructive">
          {error}
        </p>
      ) : null}
      <Button type="submit" size="lg" disabled={isLoading || !phone}>
        {isLoading ? "در حال ارسال..." : "دریافت کد ورود"}
      </Button>
    </form>
  );
}
