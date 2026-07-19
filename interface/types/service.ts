export type ServiceContentType =
  | "introduction"
  | "conditions"
  | "required_documents"
  | "process_steps"
  | "faq"
  | "warning"
  | "help_text";

export type FinancialService = {
  id: number;
  title: string;
  slug: string;
  short_description: string;
  full_description?: string;
  service_type: string;
  is_active?: boolean;
  order: number;
  rules_config: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  contents?: ServiceContent[];
  form?: AdminDynamicForm | null;
  workflow?: AdminWorkflow | null;
};

export type ServiceContent = {
  id: number;
  content_type: ServiceContentType;
  title: string;
  body: string;
  order: number;
  is_active?: boolean;
  metadata?: Record<string, unknown>;
};

export type AdminDynamicFormField = {
  id: number;
  label: string;
  key: string;
  type: string;
  field_type?: string;
  required: boolean;
  placeholder?: string;
  help_text?: string;
  options?: unknown[];
  validation_config?: Record<string, unknown>;
  order: number;
  is_active?: boolean;
  /** id of the field whose selected option must include `group_option` for this field to apply. */
  parent?: number | null;
  /** the option value on the parent field that activates this field (conditional group). */
  group_option?: string;
};

export type AdminDynamicForm = {
  id: number;
  title: string;
  description?: string;
  is_active?: boolean;
  metadata?: Record<string, unknown>;
  fields: AdminDynamicFormField[];
};

export type AdminWorkflowStep = {
  id: number;
  key: string;
  title: string;
  description?: string;
  order: number;
  is_initial: boolean;
  is_terminal: boolean;
  is_active: boolean;
  metadata?: Record<string, unknown>;
};

export type AdminWorkflow = {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
  steps: AdminWorkflowStep[];
};
