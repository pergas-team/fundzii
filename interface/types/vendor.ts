export type Vendor = {
  id: number;
  name: string;
  type?: string;
  service_categories?: unknown[];
  min_amount?: string | number | null;
  max_amount?: string | number | null;
  accepted_collateral_types?: unknown[];
  is_active?: boolean;
  description?: string;
  created_at?: string;
  updated_at?: string;
};
