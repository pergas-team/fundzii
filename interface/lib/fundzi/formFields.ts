import type { DynamicFieldType } from "@/types/form";

export type FieldTypeMeta = {
  value: DynamicFieldType;
  label: string;
  /** Whether this field type uses a list of options (select-like). */
  hasOptions?: boolean;
  /** Validation capabilities this type supports. */
  validations?: Array<"length" | "pattern" | "numeric" | "selections">;
};

export const FIELD_TYPES: FieldTypeMeta[] = [
  { value: "text", label: "متن کوتاه", validations: ["length", "pattern"] },
  { value: "textarea", label: "متن بلند", validations: ["length"] },
  { value: "number", label: "عدد", validations: ["numeric"] },
  { value: "money", label: "مبلغ (تومان)", validations: ["numeric"] },
  { value: "percentage", label: "درصد", validations: ["numeric"] },
  { value: "select", label: "انتخاب تکی", hasOptions: true },
  { value: "multi_select", label: "انتخاب چندتایی", hasOptions: true, validations: ["selections"] },
  { value: "boolean", label: "بله / خیر" },
  { value: "date", label: "تاریخ" },
  { value: "file", label: "بارگذاری فایل" },
];

export function fieldTypeMeta(type?: string): FieldTypeMeta {
  return FIELD_TYPES.find((item) => item.value === type) || FIELD_TYPES[0];
}

export function fieldTypeLabel(type?: string): string {
  return fieldTypeMeta(type).label;
}

export const CONTENT_TYPES: Array<{ value: string; label: string }> = [
  { value: "introduction", label: "معرفی سرویس" },
  { value: "conditions", label: "شرایط" },
  { value: "required_documents", label: "مدارک مورد نیاز" },
  { value: "process_steps", label: "مراحل فرآیند" },
  { value: "faq", label: "سؤالات متداول" },
  { value: "warning", label: "هشدار" },
  { value: "help_text", label: "راهنما" },
];

export function contentTypeLabel(type?: string): string {
  return CONTENT_TYPES.find((item) => item.value === type)?.label || type || "—";
}

export const SERVICE_TYPES: Array<{ value: string; label: string }> = [
  { value: "gold_backed", label: "تأمین مالی با پشتوانه طلا" },
  { value: "property_backed", label: "تأمین مالی با وثیقه ملکی" },
  { value: "other", label: "سایر" },
];

/** A single select/multi_select option as edited in the builder. */
export type OptionPair = { label: string; value: string };

/** Normalize raw backend options (string | number | {label,value}) into pairs. */
export function toOptionPairs(options?: Array<unknown>): OptionPair[] {
  if (!Array.isArray(options)) return [];
  return options.map((option) => {
    if (option && typeof option === "object") {
      const record = option as Record<string, unknown>;
      const value = String(record.value ?? record.key ?? record.label ?? "");
      const label = String(record.label ?? record.value ?? record.key ?? "");
      return { label, value };
    }
    return { label: String(option), value: String(option) };
  });
}

export function fromOptionPairs(pairs: OptionPair[]): Array<{ label: string; value: string }> {
  return pairs
    .filter((pair) => pair.value.trim() !== "" || pair.label.trim() !== "")
    .map((pair) => ({ label: pair.label || pair.value, value: pair.value || pair.label }));
}

export function slugify(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[\s‌]+/g, "_")
    .replace(/[^a-z0-9_]+/g, "")
    .replace(/_+/g, "_")
    .replace(/^_|_$/g, "");
}
