"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Bell, CheckCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { formatDate } from "@/lib/utils/formatDate";
import {
  getUnreadCount,
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "@/lib/api/notifications";
import type { FundziNotification } from "@/types/notification";

const POLL_INTERVAL_MS = 60_000;

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [unread, setUnread] = useState(0);
  const [items, setItems] = useState<FundziNotification[]>([]);
  const [loading, setLoading] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const refreshCount = useCallback(async () => {
    try {
      const { unread_count } = await getUnreadCount();
      setUnread(unread_count);
    } catch {
      // silently ignore (e.g. logged out) — bell just shows no badge
    }
  }, []);

  const loadList = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listNotifications({ page_size: "10" });
      setItems(data.results);
      setUnread(data.unread_count);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshCount();
    const id = setInterval(refreshCount, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [refreshCount]);

  useEffect(() => {
    if (open) loadList();
  }, [open, loadList]);

  // Close when clicking outside the bell area.
  useEffect(() => {
    if (!open) return;
    function onClick(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [open]);

  async function onItemClick(notification: FundziNotification) {
    if (!notification.is_read) {
      try {
        await markNotificationRead(notification.id);
        setItems((prev) =>
          prev.map((item) => (item.id === notification.id ? { ...item, is_read: true } : item)),
        );
        setUnread((value) => Math.max(value - 1, 0));
      } catch {
        // ignore
      }
    }
  }

  async function onMarkAll() {
    try {
      await markAllNotificationsRead();
      setItems((prev) => prev.map((item) => ({ ...item, is_read: true })));
      setUnread(0);
    } catch {
      // ignore
    }
  }

  return (
    <div className="relative" ref={containerRef}>
      <Button
        variant="ghost"
        size="icon"
        aria-label="اعلان‌ها"
        onClick={() => setOpen((value) => !value)}
        className="relative"
      >
        <Bell className="h-5 w-5" />
        {unread > 0 ? (
          <span className="absolute -right-0.5 -top-0.5 grid h-4 min-w-4 place-items-center rounded-full bg-destructive px-1 text-[10px] font-bold text-destructive-foreground">
            {unread > 9 ? "9+" : unread}
          </span>
        ) : null}
      </Button>

      {open ? (
        <div className="absolute left-0 top-full z-50 mt-2 w-80 overflow-hidden rounded-xl border border-border/70 bg-card shadow-lg animate-fade-in">
          <div className="flex items-center justify-between border-b border-border/70 px-4 py-3">
            <span className="text-sm font-bold">اعلان‌ها</span>
            {unread > 0 ? (
              <button
                onClick={onMarkAll}
                className="flex items-center gap-1 text-xs text-primary hover:underline"
              >
                <CheckCheck className="h-3.5 w-3.5" />
                علامت‌گذاری همه
              </button>
            ) : null}
          </div>

          <div className="max-h-96 overflow-y-auto">
            {loading ? (
              <p className="px-4 py-6 text-center text-sm text-muted-foreground">در حال بارگذاری...</p>
            ) : items.length === 0 ? (
              <p className="px-4 py-6 text-center text-sm text-muted-foreground">اعلانی وجود ندارد.</p>
            ) : (
              items.map((notification) => {
                const content = (
                  <div
                    className={cn(
                      "flex flex-col gap-1 border-b border-border/50 px-4 py-3 text-right transition-colors hover:bg-muted/60",
                      !notification.is_read && "bg-primary/5",
                    )}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-semibold">{notification.title}</span>
                      {!notification.is_read ? (
                        <span className="h-2 w-2 shrink-0 rounded-full bg-primary" />
                      ) : null}
                    </div>
                    <span className="text-xs text-muted-foreground">{notification.body}</span>
                    <span className="text-[11px] text-muted-foreground/70">
                      {formatDate(notification.created_at)}
                    </span>
                  </div>
                );
                return notification.request_id ? (
                  <Link
                    key={notification.id}
                    href={`/dashboard/requests/${notification.request_id}`}
                    onClick={() => {
                      onItemClick(notification);
                      setOpen(false);
                    }}
                  >
                    {content}
                  </Link>
                ) : (
                  <button
                    key={notification.id}
                    className="block w-full"
                    onClick={() => onItemClick(notification)}
                  >
                    {content}
                  </button>
                );
              })
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
