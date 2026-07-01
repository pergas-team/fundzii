import type { FinancingRequest } from "./request";

export type VendorApplication = {
  id: number;
  vendor_service: string;
  vendor_service_title: string;
  vendor_name: string;
  financing_request: number | null;
  status: "pending" | "under_review" | "awaiting_info" | "approved" | "rejected" | "cancelled";
  user_notes: string;
  vendor_notes: string;
  result_data: Record<string, unknown> | null;
  submitted_at: string;
  updated_at: string;
};

export type VendorApplicationFilters = {
  status?: string;
  vendor_service?: string;
  page?: string;
  page_size?: string;
};

export type ReportFunnelItem = {
  status: string;
  count: number;
};

export type ReportPartnerPerformance = {
  partner_id: number;
  partner_name: string;
  assigned_requests: number;
  offers_submitted: number;
  offers_accepted: number;
  acceptance_rate: number;
};

export type ReportMonthly = {
  month: string;
  total_requests: number;
};

export type AdminRequestFilters = {
  service?: string;
  status?: string;
  tracking_code?: string;
  user_phone?: string;
  q?: string;
  ordering?: string;
  page?: string;
  page_size?: string;
};

export type PaginatedResponse<T> = {
  results: T[];
  count: number;
  page: number;
  page_size: number;
};

export type AdminStats = {
  total_requests: number;
  by_status: Array<{ current_status: string; count: number }>;
  by_service: Array<{ service_id: number; title: string; slug: string; count: number }>;
  today_requests: number;
  last_7_days_requests: number;
  archived_requests: number;
  users_count: number;
  latest_requests: FinancingRequest[];
};
