export type UserRole = "guest" | "applicant" | "investor" | "vendor" | "operator" | "admin";

export type CurrentUser = {
  id: number;
  username: string;
  first_name?: string;
  last_name?: string;
  phone_number?: string;
  role: UserRole;
  is_staff?: boolean;
  is_superuser?: boolean;
};
