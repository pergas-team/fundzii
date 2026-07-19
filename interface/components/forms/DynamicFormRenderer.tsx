"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiError } from "@/lib/api/client";
import { submitServiceRequest } from "@/lib/api/requests";
import { fieldsById, hasFileFields, isFieldGroupActive } from "@/lib/utils/formSchema";
import { DynamicField } from "./DynamicField";
import type { DynamicFormSchema } from "@/types/form";

type FormValues = Record<string, unknown>;

function normalizeErrors(error: unknown) {
  if (error instanceof ApiError && error.payload?.errors && typeof error.payload.errors === "object" && !Array.isArray(error.payload.errors)) {
    return Object.fromEntries(
      Object.entries(error.payload.errors).map(([key, value]) => [key, Array.isArray(value) ? value.join("، ") : String(value)]),
    );
  }
  return { __all__: "ثبت درخواست با خطا مواجه شد." };
}

export function DynamicFormRenderer({ slug, schema }: { slug: string; schema: DynamicFormSchema }) {
  const router = useRouter();
  const sortedFields = useMemo(() => [...schema.fields].sort((a, b) => a.order - b.order), [schema.fields]);
  const fieldsMap = useMemo(() => fieldsById(schema.fields), [schema.fields]);
  // shouldUnregister: true drops a hidden field's value + validation rules on
  // unmount — required conditional-group fields must not block submission
  // once their group is deselected.
  const { register, handleSubmit, setValue, watch, formState } = useForm<FormValues>({ shouldUnregister: true });
  const [serverErrors, setServerErrors] = useState<Record<string, string>>({});
  const [trackingCode, setTrackingCode] = useState("");
  const [isSubmitting, setSubmitting] = useState(false);
  const liveValues = watch();
  const visibleFields = sortedFields.filter((field) => isFieldGroupActive(field, liveValues, fieldsMap));

  async function onSubmit(values: FormValues, event?: React.BaseSyntheticEvent) {
    setServerErrors({});
    setTrackingCode("");
    setSubmitting(true);
    try {
      const formElement = event?.target as HTMLFormElement | undefined;
      const activeFields = sortedFields.filter((field) => isFieldGroupActive(field, values, fieldsMap));
      const hasFiles = hasFileFields(activeFields);
      const payload = hasFiles && formElement ? new FormData(formElement) : values;
      if (payload instanceof FormData) {
        activeFields.forEach((field) => {
          if (field.type === "boolean") payload.set(field.key, values[field.key] ? "true" : "false");
        });
      }
      const request = await submitServiceRequest(slug, payload);
      setTrackingCode(request.tracking_code);
      router.push(`/dashboard/requests/${request.id}`);
    } catch (error) {
      setServerErrors(normalizeErrors(error));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{schema.title}</CardTitle>
      </CardHeader>
      <CardContent>
        <form className="grid gap-5" onSubmit={handleSubmit(onSubmit)}>
          {visibleFields.map((field) => (
            <div key={field.id} className={field.parent ? "border-r-2 border-primary/20 pr-4" : undefined}>
              <DynamicField
                field={field}
                register={register}
                setValue={setValue}
                watch={watch}
                error={(formState.errors[field.key]?.message as string | undefined) || serverErrors[field.key]}
              />
            </div>
          ))}
          {serverErrors.__all__ ? (
            <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive">{serverErrors.__all__}</p>
          ) : null}
          {trackingCode ? (
            <p className="rounded-lg border border-success/20 bg-success/10 px-3 py-2 text-sm font-medium text-success">
              کد پیگیری: {trackingCode}
            </p>
          ) : null}
          <Button type="submit" size="lg" disabled={isSubmitting}>
            {isSubmitting ? "در حال ثبت..." : "ثبت درخواست"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
