export type DynamicFieldType =
  | "text"
  | "textarea"
  | "number"
  | "select"
  | "multi_select"
  | "boolean"
  | "date"
  | "file"
  | "money"
  | "percentage";

export type DynamicFormField = {
  id: number;
  label: string;
  key: string;
  name?: string;
  type: DynamicFieldType;
  required: boolean;
  placeholder?: string;
  help_text?: string;
  options?: Array<string | number | { label: string; value: string | number }>;
  validation_config?: Record<string, unknown>;
  order: number;
  default_value?: unknown;
  disabled?: boolean;
  hidden?: boolean;
  /** id of the field whose selected option must include `group_option` for this field to apply. */
  parent?: number | null;
  /** the option value on the parent field that activates this field (conditional group). */
  group_option?: string;
};

export type DynamicFormSchema = {
  id: number;
  title: string;
  description?: string;
  fields: DynamicFormField[];
};
