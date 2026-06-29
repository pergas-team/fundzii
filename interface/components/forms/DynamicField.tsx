"use client";

import { UseFormRegister, UseFormSetValue, UseFormWatch } from "react-hook-form";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { FileUploadField } from "./FileUploadField";
import { MoneyInput } from "./MoneyInput";
import { SelectField } from "./SelectField";
import type { DynamicFormField } from "@/types/form";

type FormValues = Record<string, unknown>;

export function DynamicField({
  field,
  register,
  setValue,
  watch,
  error,
}: {
  field: DynamicFormField;
  register: UseFormRegister<FormValues>;
  setValue: UseFormSetValue<FormValues>;
  watch: UseFormWatch<FormValues>;
  error?: string;
}) {
  if (field.hidden) return null;
  const name = field.key || field.name || "";
  const requiredMessage = field.required ? `${field.label} الزامی است.` : false;
  const registration = register(name, { required: requiredMessage });
  const common = {
    id: name,
    placeholder: field.placeholder,
    disabled: field.disabled,
    ...registration,
  };

  return (
    <div className="grid gap-2">
      <Label htmlFor={name}>
        {field.label}
        {field.required ? <span className="text-destructive"> *</span> : null}
      </Label>
      {field.type === "textarea" ? (
        <Textarea {...common} />
      ) : field.type === "select" ? (
        <>
          <SelectField field={field} value={String(watch(name) || "")} onChange={(value) => setValue(name, value, { shouldValidate: true })} />
          <input type="hidden" value={String(watch(name) || "")} {...registration} />
        </>
      ) : field.type === "multi_select" ? (
        <select multiple className="min-h-28 w-full rounded-lg border border-input bg-card px-3.5 py-2 text-sm shadow-sm outline-none transition-colors focus-visible:border-ring/60 focus-visible:ring-2 focus-visible:ring-ring/40" {...register(name, { required: requiredMessage })}>
          {(field.options || []).map((option) => {
            const value = typeof option === "object" ? String(option.value) : String(option);
            const label = typeof option === "object" ? option.label : String(option);
            return <option key={value} value={value}>{label}</option>;
          })}
        </select>
      ) : field.type === "boolean" ? (
        <label className="flex cursor-pointer items-center gap-2.5 rounded-lg border border-input bg-card p-3.5 text-sm transition-colors hover:border-primary/30">
          <input
            type="checkbox"
            className="h-5 w-5 accent-primary"
            checked={Boolean(watch(name))}
            onChange={(event) => setValue(name, event.target.checked, { shouldValidate: true })}
          />
          <input type="hidden" value={watch(name) ? "true" : ""} {...registration} />
          بله
        </label>
      ) : field.type === "file" ? (
        <FileUploadField name={name} required={field.required} />
      ) : field.type === "money" || field.type === "percentage" || field.type === "number" ? (
        <MoneyInput {...common} />
      ) : field.type === "date" ? (
        <Input type="date" {...common} />
      ) : (
        <Input type="text" {...common} />
      )}
      {field.help_text ? <p className="text-xs text-muted-foreground">{field.help_text}</p> : null}
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
    </div>
  );
}
