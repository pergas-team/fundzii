import type { DynamicFormField } from "@/types/form";

export function optionValue(option: NonNullable<DynamicFormField["options"]>[number]) {
  if (typeof option === "object") return String(option.value);
  return String(option);
}

export function optionLabel(option: NonNullable<DynamicFormField["options"]>[number]) {
  if (typeof option === "object") return option.label;
  return String(option);
}

export function hasFileFields(fields: DynamicFormField[]) {
  return fields.some((field) => field.type === "file");
}
