import type { FinancingRequest } from "./request";

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
