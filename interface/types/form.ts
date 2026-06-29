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
};

export type DynamicFormSchema = {
  id: number;
  title: string;
  description?: string;
  fields: DynamicFormField[];
};
