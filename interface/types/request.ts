import type { CurrentUser } from "./auth";
import type { FinancialService } from "./service";
import type { RequestHistoryItem, WorkflowStep } from "./workflow";

export type RequestFieldValue = {
  field: string;
  label: string;
  type: string;
  value?: unknown;
  file?: string | null;
};

export type RequestAttachment = {
  id: number;
  title: string;
  document_type: string;
  file: string | null;
  created_at: string;
};

export type InternalNote = {
  id: number;
  body: string;
  author?: string | null;
  created_at: string;
};

export type FinancingRequest = {
  id: number;
  tracking_code: string;
  service: FinancialService;
  user?: CurrentUser | null;
  admin_assignee?: CurrentUser | null;
  current_status: string;
  current_workflow_step?: WorkflowStep | null;
  submitted_at: string;
  updated_at: string;
  is_archived: boolean;
  field_values?: RequestFieldValue[];
  attachments?: RequestAttachment[];
  history?: RequestHistoryItem[];
  internal_notes?: InternalNote[];
  workflow_steps?: WorkflowStep[];
};
