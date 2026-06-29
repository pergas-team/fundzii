import Link from "next/link";
import { ArrowLeft, ListChecks } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RequiredDocuments } from "./RequiredDocuments";
import { ServiceConditions } from "./ServiceConditions";
import type { FinancialService } from "@/types/service";

export function ServiceDetail({ service }: { service: FinancialService }) {
  const contents = service.contents || [];
  const processItems = contents.filter(
    (content) =>
      content.content_type === "process_steps" ||
      content.content_type === "introduction" ||
      content.content_type === "faq",
  );
  return (
    <div className="grid gap-6">
      <section className="relative overflow-hidden rounded-3xl bg-gradient-hero p-8 text-primary-foreground shadow-lift md:p-10">
        <div className="absolute inset-0 bg-dotted opacity-50" aria-hidden />
        <div className="relative max-w-3xl">
          <h1 className="text-2xl font-extrabold md:text-3xl">{service.title}</h1>
          <p className="mt-4 leading-8 text-primary-foreground/85">
            {service.full_description || service.short_description}
          </p>
          <Button asChild variant="accent" size="lg" className="mt-6">
            <Link href={`/services/${service.slug}/apply`}>
              شروع ثبت درخواست
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </section>
      <ServiceConditions contents={contents} />
      <RequiredDocuments contents={contents} />
      {processItems.length ? (
        <section className="grid gap-4">
          <h2 className="flex items-center gap-2 text-lg font-bold">
            <ListChecks className="h-5 w-5 text-primary" />
            فرآیند سرویس
          </h2>
          <div className="grid gap-4 md:grid-cols-2">
            {processItems.map((content) => (
              <Card key={content.id}>
                <CardHeader>
                  <CardTitle className="text-base">{content.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="prose-content" dangerouslySetInnerHTML={{ __html: content.body }} />
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
