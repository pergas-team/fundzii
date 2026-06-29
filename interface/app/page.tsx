import Link from "next/link";
import {
  ArrowLeft,
  ClipboardList,
  FileText,
  Landmark,
  ShieldCheck,
  Sparkles,
  UploadCloud,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const features = [
  { icon: Landmark, title: "خدمات قابل تنظیم", text: "هر سرویس فرم، قواعد و گردش‌کار مستقل خود را دارد." },
  { icon: ClipboardList, title: "درخواست و پیگیری", text: "متقاضی کد پیگیری دریافت می‌کند و وضعیت را لحظه‌به‌لحظه می‌بیند." },
  { icon: ShieldCheck, title: "بررسی عملیاتی", text: "ادمین و اپراتور درخواست‌ها را بررسی و وضعیت را مدیریت می‌کنند." },
];

const steps = [
  { icon: Landmark, title: "انتخاب سرویس", text: "از میان خدمات تأمین مالی فعال، سرویس مناسب را انتخاب کنید." },
  { icon: FileText, title: "تکمیل فرم", text: "فرم اختصاصی سرویس را پر کنید؛ قوانین به‌صورت پویا اعمال می‌شوند." },
  { icon: UploadCloud, title: "بارگذاری مدارک", text: "اسناد لازم را آپلود کنید و درخواست را ثبت نمایید." },
  { icon: ClipboardList, title: "پیگیری وضعیت", text: "با کد پیگیری، مراحل بررسی درخواست را دنبال کنید." },
];

export default function HomePage() {
  return (
    <main className="container grid gap-12 py-8 md:py-12">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-3xl bg-gradient-hero p-8 text-primary-foreground shadow-lift md:p-14">
        <div className="absolute inset-0 bg-dotted opacity-60" aria-hidden />
        <div
          className="absolute -left-16 -top-16 h-64 w-64 rounded-full bg-accent/25 blur-3xl"
          aria-hidden
        />
        <div className="relative max-w-3xl animate-slide-up">
          <span className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3.5 py-1.5 text-sm font-semibold backdrop-blur">
            <Sparkles className="h-4 w-4 text-accent" />
            Fundzi / فاندزی
          </span>
          <h1 className="mt-5 text-3xl font-extrabold leading-tight md:text-5xl md:leading-[1.15]">
            هسته عملیاتی خدمات
            <span className="mt-2 block bg-gradient-to-l from-accent to-amber-200 bg-clip-text text-transparent">
              تأمین مالی
            </span>
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-8 text-primary-foreground/80 md:text-lg">
            سرویس مالی را انتخاب کنید، فرم اختصاصی آن را تکمیل کنید، مدارک را بارگذاری کنید و
            وضعیت درخواست را مرحله‌به‌مرحله پیگیری کنید.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild variant="accent" size="lg">
              <Link href="/services">
                مشاهده خدمات
                <ArrowLeft className="h-4 w-4" />
              </Link>
            </Button>
            <Button
              asChild
              size="lg"
              className="bg-white/10 text-primary-foreground shadow-none backdrop-blur hover:bg-white/20"
            >
              <Link href="/auth/login">ورود متقاضی</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="grid gap-5 md:grid-cols-3">
        {features.map((item) => (
          <Card
            key={item.title}
            className="group transition-all duration-300 hover:-translate-y-1 hover:shadow-lift"
          >
            <CardHeader>
              <span className="grid h-12 w-12 place-items-center rounded-xl bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                <item.icon className="h-6 w-6" />
              </span>
              <CardTitle className="pt-2">{item.title}</CardTitle>
            </CardHeader>
            <CardContent className="text-sm leading-7 text-muted-foreground">{item.text}</CardContent>
          </Card>
        ))}
      </section>

      {/* How it works */}
      <section>
        <div className="mb-6 text-center">
          <h2 className="text-2xl font-extrabold tracking-tight">چطور کار می‌کند؟</h2>
          <p className="mt-2 text-sm text-muted-foreground">تنها در چهار گام درخواست تأمین مالی خود را ثبت کنید.</p>
        </div>
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((step, index) => (
            <div
              key={step.title}
              className="relative rounded-2xl border bg-card p-6 shadow-card transition-all duration-300 hover:-translate-y-1 hover:shadow-lift"
            >
              <span className="absolute left-5 top-5 text-5xl font-black text-muted/70">
                {index + 1}
              </span>
              <span className="grid h-11 w-11 place-items-center rounded-xl bg-gradient-accent text-accent-foreground shadow-soft">
                <step.icon className="h-5 w-5" />
              </span>
              <h3 className="mt-4 font-bold">{step.title}</h3>
              <p className="mt-1.5 text-sm leading-7 text-muted-foreground">{step.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="relative overflow-hidden rounded-3xl border bg-card p-8 text-center shadow-card md:p-12">
        <div className="relative mx-auto max-w-xl">
          <h2 className="text-2xl font-extrabold tracking-tight md:text-3xl">آماده‌ی شروع هستید؟</h2>
          <p className="mt-3 text-sm leading-7 text-muted-foreground">
            همین حالا وارد شوید و اولین درخواست تأمین مالی خود را ثبت کنید.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <Button asChild size="lg">
              <Link href="/services">
                شروع کنید
                <ArrowLeft className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link href="/auth/login">ورود</Link>
            </Button>
          </div>
        </div>
      </section>
    </main>
  );
}
