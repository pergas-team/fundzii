import { Suspense } from "react";
import { AuthShell } from "@/components/auth/AuthShell";
import { OtpVerifyForm } from "@/components/auth/OtpVerifyForm";

export default function VerifyPage() {
  return (
    <AuthShell formTitle="تأیید کد ورود" formSubtitle="کد ارسال‌شده را وارد کنید">
      <Suspense fallback={<div className="text-muted-foreground">در حال بارگذاری...</div>}>
        <OtpVerifyForm />
      </Suspense>
    </AuthShell>
  );
}
