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

/**
 * Whether a conditional-group field should be shown/required, given the current
 * form values and a lookup of fields by id. Fields without a `parent` are always
 * active. A child is active only while its parent's current selection includes
 * (select) or contains (multi_select) the child's `group_option` — this lets a
 * user activate several groups at once (e.g. both "ملک" and "طلا" collateral).
 */
export function isFieldGroupActive(
  field: DynamicFormField,
  values: Record<string, unknown>,
  fieldsById: Record<number, DynamicFormField>,
): boolean {
  if (!field.parent) return true;
  const parent = fieldsById[field.parent];
  if (!parent) return true;
  const parentValue = values[parent.key || parent.name || ""];
  if (parentValue === undefined || parentValue === null || parentValue === "") return false;
  const selected = Array.isArray(parentValue) ? parentValue : [parentValue];
  return selected.map((item) => String(item)).includes(String(field.group_option));
}

export function fieldsById(fields: DynamicFormField[]): Record<number, DynamicFormField> {
  return Object.fromEntries(fields.map((field) => [field.id, field]));
}
