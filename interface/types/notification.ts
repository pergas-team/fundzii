export type FundziNotification = {
  id: number;
  kind: "request_submitted" | "status_changed" | "general";
  channel: "in_app" | "sms" | "email";
  title: string;
  body: string;
  is_read: boolean;
  request_id: number | null;
  tracking_code: string | null;
  created_at: string;
};
