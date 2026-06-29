import { apiFetch, toQuery } from "./client";
import type { PaginatedResponse } from "@/types/admin";
import type { FundziNotification } from "@/types/notification";

export type NotificationListResponse = PaginatedResponse<FundziNotification> & {
  unread_count: number;
};

export async function listNotifications(params: { unread?: string; page?: string; page_size?: string } = {}) {
  return apiFetch<NotificationListResponse>(`/api/fundzi/notifications/${toQuery(params)}`);
}

export async function getUnreadCount() {
  return apiFetch<{ unread_count: number }>("/api/fundzi/notifications/unread-count/");
}

export async function markNotificationRead(id: number) {
  return apiFetch<FundziNotification>(`/api/fundzi/notifications/${id}/read/`, { method: "POST" });
}

export async function markAllNotificationsRead() {
  return apiFetch<{ detail: string; updated: number }>("/api/fundzi/notifications/read-all/", {
    method: "POST",
  });
}
