export const statusLabels: Record<string, string> = {
  submitted: "ثبت شده",
  initial_review: "در حال بررسی اولیه",
  information_review: "بررسی اطلاعات",
  property_document_review: "بررسی مدارک ملک",
  property_location_check: "بررسی موقعیت ملک",
  property_valuation: "ارزیابی ملک",
  legal_review: "بررسی حقوقی",
  valuation_required: "نیازمند ارزیابی",
  offer_preparation: "آماده‌سازی پیشنهاد",
  offer_sent: "پیشنهاد ارسال شده",
  approved: "تأیید شده",
  rejected: "رد شده",
  needs_more_information: "نیاز به تکمیل اطلاعات",
};

export function translateStatus(status?: string | null) {
  if (!status) return "-";
  return statusLabels[status] ?? status.replaceAll("_", " ");
}

export type StatusTone = "default" | "success" | "destructive" | "warning" | "accent";

export function statusTone(status?: string | null): StatusTone {
  if (status === "approved") return "success";
  if (status === "rejected") return "destructive";
  if (status === "needs_more_information") return "warning";
  if (status === "offer_sent") return "accent";
  return "default";
}
