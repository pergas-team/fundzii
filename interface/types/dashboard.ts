import type { FinancialService } from "./service";

export type VendorService = {
  id: number;
  slug: string;
  title: string;
  description: string;
  category: string;
  vendor_name: string;
  vendor_type: "financial" | "non_financial";
  price_display: string;
  duration_display: string;
  tags: string[];
  is_active: boolean;
  order: number;
};

export type DashboardData = {
  investment: FinancialService[];
  financing: FinancialService[];
  vendor_services: VendorService[];
};
