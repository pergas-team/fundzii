import Link from "next/link";
import Image from "next/image";
import {
  Building2,
  CheckCircle2,
  ClipboardCheck,
  ClipboardList,
  Eye,
  FileText,
  Gem,
  Globe2,
  Laptop,
  MessageSquareText,
  Puzzle,
  Settings2,
  Target,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type Service = {
  icon: LucideIcon;
  title: string;
  desc: string;
  fields: string[];
} & ({ available: true; href: string; cta: string; outline?: boolean } | { available: false });

const services: Service[] = [
  {
    icon: Gem,
    title: "تأمین مالی با پشتوانه طلا",
    desc: "با ثبت اطلاعات طلا و مدارک مربوطه، می‌توانید درخواست تأمین مالی خود را ثبت کنید.",
    fields: ["نوع طلا", "وزن تقریبی", "ارزش تقریبی", "مدت موردنظر"],
    available: true,
    href: "/services/gold-backed-financing",
    cta: "ثبت درخواست",
  },
  {
    icon: Building2,
    title: "تأمین مالی با وثیقه ملکی",
    desc: "با ارائه اطلاعات ملک و مدارک مربوطه، درخواست خود را برای دریافت سرمایه ثبت کنید.",
    fields: ["نوع ملک", "منطقه و موقعیت", "ارزش تقریبی ملک", "مدت بازپرداخت"],
    available: true,
    href: "/services/property-backed-financing",
    cta: "ثبت درخواست",
  },
  {
    icon: FileText,
    title: "تأمین مالی با LC",
    desc: "در صورت داشتن اعتبار اسنادی (LC)، می‌توانید از این خدمت استفاده کنید.",
    fields: ["ارائه LC معتبر", "مبلغ درخواستی", "مدت بازپرداخت"],
    available: false,
  },
  {
    icon: TrendingUp,
    title: "تأمین مالی پروژه‌ای",
    desc: "اگر برای توسعه کسب‌وکار یا پروژه خود به سرمایه نیاز دارید، درخواست خود را ثبت کنید.",
    fields: ["عنوان پروژه", "مبلغ درخواستی", "مدت موردنظر"],
    available: false,
  },
];

const steps = [
  { icon: MessageSquareText, title: "انتخاب خدمت", desc: "خدمات مالی موردنظر خود را از خدمات فعال فاندزی انتخاب کنید." },
  { icon: FileText, title: "تکمیل فرم اختصاصی", desc: "فرم مربوط به خدمت انتخابی را تکمیل و مدارک موردنیاز را بارگذاری کنید." },
  { icon: ClipboardCheck, title: "بررسی توسط تیم فاندزی", desc: "درخواست شما وارد فرآیند بررسی شده و مراحل مربوطه طی می‌شود." },
  { icon: TrendingUp, title: "پیگیری وضعیت درخواست", desc: "وضعیت درخواست خود را به‌صورت مرحله‌ای در پنل کاربری مشاهده کنید." },
];

const whyItems = [
  { icon: Globe2, title: "مناسب برای همه", desc: "قابل استفاده برای اشخاص و شرکت‌ها." },
  { icon: Settings2, title: "مدیریت حرفه‌ای", desc: "درخواست‌ها از طریق پنل‌های مشخص مدیریت می‌شوند." },
  { icon: Puzzle, title: "قابلیت توسعه", desc: "اضافه شدن خدمات مالی جدید به‌راحتی." },
  { icon: Eye, title: "پیگیری شفاف", desc: "مشاهده وضعیت درخواست در هر مرحله." },
  { icon: Laptop, title: "بدون مراجعه حضوری", desc: "ثبت درخواست اولیه به‌صورت آنلاین و آسان." },
  { icon: ClipboardList, title: "خدمات ساختاریافته", desc: "هر خدمت فرم، شرایط و فرآیند بررسی مشخصی دارد." },
];

export default function HomePage() {
  return (
    <main>
      {/* Hero */}
      <section className="bg-secondary/60">
        <div className="container grid gap-10 py-14 md:grid-cols-2 md:items-center md:py-20">
          <div className="space-y-6">
            <h1 className="text-3xl font-extrabold leading-tight text-foreground md:text-5xl md:leading-[1.3]">
              سرمایه موردنیاز خود را
              <span className="mt-1 block bg-gradient-to-l from-accent to-amber-500 bg-clip-text text-transparent">
                هوشمندانه تأمین کنید
              </span>
            </h1>
            <p className="max-w-xl text-base leading-8 text-muted-foreground">
              فاندزی بستری برای ثبت، بررسی و پیگیری درخواست‌های تأمین مالی است؛ از تأمین مالی با
              پشتوانه طلا تا وثیقه ملکی و سایر خدمات مالی قابل توسعه.
            </p>
            <div className="flex flex-wrap gap-3">
              <Button asChild variant="accent" size="lg">
                <Link href="/services">شروع ثبت درخواست</Link>
              </Button>
              <Button asChild variant="outline" size="lg">
                <Link href="/services">مشاهده خدمات فاندزی</Link>
              </Button>
            </div>
            <ul className="flex flex-wrap gap-x-6 gap-y-2 pt-1 text-sm font-medium text-foreground">
              <li className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-accent" /> ثبت درخواست آسان
              </li>
              <li className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-accent" /> بررسی مرحله‌ای
              </li>
              <li className="flex items-center gap-1.5">
                <Target className="h-4 w-4 text-accent" /> پیگیری شفاف
              </li>
            </ul>
          </div>
          <div className="relative">
            <Image
              src="/fundzi/hero.png"
              alt="داشبورد پیگیری درخواست تأمین مالی فاندزی"
              width={512}
              height={347}
              priority
              className="h-auto w-full md:[mask-image:linear-gradient(to_left,transparent_0,#000_4.5rem)]"
            />
          </div>
        </div>
      </section>

      {/* Services */}
      <section className="py-16 md:py-24">
        <div className="container">
          <div className="mb-10 text-center md:mb-14">
            <h2 className="text-2xl font-extrabold tracking-tight md:text-3xl">خدمات تأمین مالی فاندزی</h2>
            <p className="mt-3 text-sm text-muted-foreground md:text-base">
              هر خدمت در فاندزی، مسیر ثبت درخواست و بررسی اختصاصی خود را دارد.
            </p>
          </div>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {services.map((service) => (
              <Card key={service.title} className="flex flex-col transition-shadow hover:shadow-lift">
                <CardHeader>
                  <span className="grid h-12 w-12 place-items-center rounded-xl bg-accent/15 text-[hsl(28_70%_28%)]">
                    <service.icon className="h-6 w-6" />
                  </span>
                  <CardTitle className="pt-2">{service.title}</CardTitle>
                </CardHeader>
                <CardContent className="flex flex-1 flex-col">
                  <p className="min-h-[4.5rem] text-sm leading-7 text-muted-foreground">{service.desc}</p>
                  {service.available ? (
                    <Button asChild size="sm" variant={service.outline ? "outline" : "accent"} className="mt-4 w-full">
                      <Link href={service.href}>{service.cta}</Link>
                    </Button>
                  ) : (
                    <Badge variant="outline" className="mt-4 w-fit">
                      به‌زودی
                    </Badge>
                  )}
                  <ul className="mt-5 space-y-2 text-sm text-foreground/90">
                    {service.fields.map((field) => (
                      <li key={field} className="flex items-center gap-2">
                        <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                        {field}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="bg-secondary/60 py-16 md:py-24">
        <div className="container">
          <div className="mb-10 text-center md:mb-14">
            <h2 className="text-2xl font-extrabold tracking-tight md:text-3xl">چگونه کار می‌کند؟</h2>
            <p className="mt-2 text-sm text-muted-foreground">فرآیند ثبت درخواست در فاندزی</p>
          </div>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {steps.map((step, index) => (
              <div
                key={step.title}
                className="relative overflow-hidden rounded-2xl border bg-card p-6 shadow-card transition-all duration-300 hover:-translate-y-1 hover:shadow-lift"
              >
                <span className="absolute left-5 top-5 text-5xl font-black text-muted/70">{index + 1}</span>
                <span className="grid h-11 w-11 place-items-center rounded-xl bg-gradient-accent text-accent-foreground shadow-soft">
                  <step.icon className="h-5 w-5" />
                </span>
                <h3 className="mt-4 font-bold">{step.title}</h3>
                <p className="mt-1.5 text-sm leading-7 text-muted-foreground">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Why Fundzi */}
      <section className="bg-primary py-16 text-primary-foreground md:py-24">
        <div className="container">
          <div className="mb-10 text-center md:mb-14">
            <h2 className="text-2xl font-extrabold tracking-tight md:text-3xl">چرا فاندزی؟</h2>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
            {whyItems.map((item) => (
              <div
                key={item.title}
                className="rounded-2xl border border-white/10 bg-white/5 p-6 text-center transition-colors hover:bg-white/10"
              >
                <span className="mx-auto grid h-11 w-11 place-items-center rounded-xl bg-accent/20 text-accent">
                  <item.icon className="h-5 w-5" />
                </span>
                <h3 className="mt-3 text-sm font-bold">{item.title}</h3>
                <p className="mt-1.5 text-xs leading-6 text-primary-foreground/70">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 md:py-24">
        <div className="container">
          <div className="grid items-center gap-8 rounded-3xl border bg-card p-8 shadow-card md:grid-cols-2 md:p-12">
            <div className="relative order-2 md:order-1">
              <Image
                src="/fundzi/cta.png"
                alt="مشاهده وضعیت درخواست تأمین مالی از پنل فاندزی"
                width={434}
                height={144}
                className="h-auto w-full rounded-2xl"
              />
            </div>
            <div className="order-1 space-y-4 md:order-2">
              <h2 className="text-2xl font-extrabold leading-snug tracking-tight md:text-3xl">
                همین حالا درخواست تأمین مالی خود را ثبت کنید
              </h2>
              <p className="text-sm leading-7 text-muted-foreground">
                با فاندزی، مسیر ثبت، بررسی و پیگیری درخواست‌های تأمین مالی ساده‌تر و شفاف‌تر انجام
                می‌شود.
              </p>
              <div className="flex flex-wrap gap-3 pt-1">
                <Button asChild variant="accent" size="lg">
                  <Link href="/services">شروع ثبت درخواست</Link>
                </Button>
                <Button asChild variant="outline" size="lg">
                  <Link href="/auth/login">ورود به پنل کاربری</Link>
                </Button>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
