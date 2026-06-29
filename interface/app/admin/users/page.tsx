"use client";

import { useCallback, useEffect, useState } from "react";
import { Search, ShieldAlert, UserPlus, X } from "lucide-react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { RoleGuard } from "@/components/layout/RoleGuard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, Switch } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { apiErrorMessage } from "@/lib/api/client";
import { createUser, listUsers, setUserRole, updateUser } from "@/lib/api/users";
import { ROLE_OPTIONS, roleBadgeVariant, roleLabel } from "@/lib/fundzi/roles";
import { formatDate } from "@/lib/utils/formatDate";
import type { FundziUser, UserRole } from "@/types/user";

const PAGE_SIZE = 12;

export default function AdminUsersPage() {
  const [users, setUsers] = useState<FundziUser[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [role, setRole] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [selected, setSelected] = useState<FundziUser | null>(null);

  const load = useCallback(
    (nextPage = page, nextQ = q, nextRole = role) => {
      setLoading(true);
      setError("");
      listUsers({ q: nextQ, role: nextRole, page: String(nextPage), page_size: String(PAGE_SIZE) })
        .then((response) => {
          setUsers(response.results);
          setCount(response.count);
          setPage(response.page);
        })
        .catch(() => setError("دریافت کاربران با خطا مواجه شد."))
        .finally(() => setLoading(false));
    },
    [page, q, role],
  );

  useEffect(() => {
    load(1, "", "");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const totalPages = Math.max(Math.ceil(count / PAGE_SIZE), 1);

  function upsert(user: FundziUser) {
    setUsers((current) => {
      const exists = current.some((item) => item.id === user.id);
      return exists ? current.map((item) => (item.id === user.id ? user : item)) : [user, ...current];
    });
  }

  return (
    <RoleGuard roles={["admin"]}>
      <DashboardShell
        mode="admin"
        title="کاربران"
        description="مدیریت کاربران و نقش‌های دسترسی"
        actions={
          <Button onClick={() => { setCreating((value) => !value); setSelected(null); }}>
            <UserPlus className="h-4 w-4" />
            افزودن کاربر
          </Button>
        }
      >
        <div className="grid gap-4">
          {creating ? (
            <CreateUserForm
              onCancel={() => setCreating(false)}
              onCreated={(user) => {
                upsert(user);
                setCount((value) => value + 1);
                setCreating(false);
              }}
            />
          ) : null}

          <Card>
            <CardContent className="grid gap-3 pt-5 sm:grid-cols-[1fr_200px_auto]">
              <form
                className="relative"
                onSubmit={(event) => {
                  event.preventDefault();
                  load(1, q, role);
                }}
              >
                <Search className="pointer-events-none absolute right-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={q}
                  onChange={(event) => setQ(event.target.value)}
                  placeholder="جستجو با شماره یا نام"
                  className="pr-10"
                />
              </form>
              <Select
                value={role}
                onChange={(event) => {
                  setRole(event.target.value);
                  load(1, q, event.target.value);
                }}
              >
                <option value="">همه نقش‌ها</option>
                {ROLE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
              <Button variant="outline" onClick={() => load(1, q, role)}>
                جستجو
              </Button>
            </CardContent>
          </Card>

          {error ? (
            <p className="rounded-lg bg-destructive/10 px-4 py-3 font-medium text-destructive">{error}</p>
          ) : loading ? (
            <Skeleton className="h-72" />
          ) : (
            <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
              <div className="grid gap-4">
                <div className="overflow-hidden rounded-xl border bg-card shadow-card">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>کاربر</TableHead>
                        <TableHead>نقش</TableHead>
                        <TableHead>وضعیت</TableHead>
                        <TableHead>درخواست‌ها</TableHead>
                        <TableHead>عضویت</TableHead>
                        <TableHead></TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {users.map((user) => (
                        <TableRow key={user.id} className={selected?.id === user.id ? "bg-primary/5" : undefined}>
                          <TableCell>
                            <div className="font-semibold">{`${user.first_name || ""} ${user.last_name || ""}`.trim() || "بدون نام"}</div>
                            <div className="text-xs text-muted-foreground" dir="ltr">{user.username}</div>
                          </TableCell>
                          <TableCell>
                            <Badge variant={roleBadgeVariant(user.role)}>{roleLabel(user.role)}</Badge>
                          </TableCell>
                          <TableCell>
                            {user.is_active === false ? (
                              <Badge variant="destructive">غیرفعال</Badge>
                            ) : (
                              <Badge variant="success">فعال</Badge>
                            )}
                          </TableCell>
                          <TableCell>{user.requests_count || 0}</TableCell>
                          <TableCell className="text-sm text-muted-foreground">
                            {user.date_joined ? formatDate(user.date_joined) : "-"}
                          </TableCell>
                          <TableCell>
                            <Button size="sm" variant="outline" onClick={() => { setSelected(user); setCreating(false); }}>
                              ویرایش
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                      {!users.length ? (
                        <TableRow>
                          <TableCell colSpan={6} className="py-10 text-center text-muted-foreground">
                            کاربری یافت نشد.
                          </TableCell>
                        </TableRow>
                      ) : null}
                    </TableBody>
                  </Table>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border bg-card p-3 text-sm shadow-card">
                  <span className="text-muted-foreground">
                    صفحه {page} از {totalPages} · مجموع {count} کاربر
                  </span>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => load(page - 1, q, role)}>
                      قبلی
                    </Button>
                    <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => load(page + 1, q, role)}>
                      بعدی
                    </Button>
                  </div>
                </div>
              </div>

              <EditUserPanel
                key={selected?.id ?? "none"}
                user={selected}
                onClose={() => setSelected(null)}
                onSaved={(user) => {
                  upsert(user);
                  setSelected(user);
                }}
              />
            </div>
          )}
        </div>
      </DashboardShell>
    </RoleGuard>
  );
}

function CreateUserForm({ onCreated, onCancel }: { onCreated: (user: FundziUser) => void; onCancel: () => void }) {
  const [phone, setPhone] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>("applicant");
  const [isActive, setIsActive] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setSaving(true);
    try {
      const user = await createUser({
        phone_number: phone.trim(),
        first_name: firstName,
        last_name: lastName,
        password: password || undefined,
        role,
        is_active: isActive,
      });
      onCreated(user);
    } catch (exception) {
      setError(apiErrorMessage(exception, "ایجاد کاربر با خطا مواجه شد."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card className="border-primary/20">
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>افزودن کاربر جدید</CardTitle>
        <Button size="icon" variant="ghost" onClick={onCancel} aria-label="بستن">
          <X className="h-4 w-4" />
        </Button>
      </CardHeader>
      <CardContent>
        <form className="grid gap-4" onSubmit={submit}>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="grid gap-1.5">
              <Label>شماره موبایل *</Label>
              <Input value={phone} onChange={(event) => setPhone(event.target.value)} dir="ltr" className="text-left" placeholder="09120000000" required />
            </div>
            <div className="grid gap-1.5">
              <Label>نقش</Label>
              <Select value={role} onChange={(event) => setRole(event.target.value as UserRole)}>
                {ROLE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </div>
            <div className="grid gap-1.5">
              <Label>نام</Label>
              <Input value={firstName} onChange={(event) => setFirstName(event.target.value)} />
            </div>
            <div className="grid gap-1.5">
              <Label>نام خانوادگی</Label>
              <Input value={lastName} onChange={(event) => setLastName(event.target.value)} />
            </div>
            <div className="grid gap-1.5 md:col-span-2">
              <Label>رمز عبور (اختیاری)</Label>
              <Input value={password} onChange={(event) => setPassword(event.target.value)} dir="ltr" className="text-left" type="text" autoComplete="new-password" />
              <p className="text-xs text-muted-foreground">
                اگر خالی بماند، کاربر فقط با کد ورود (OTP) وارد می‌شود و رمز عبوری ندارد.
              </p>
            </div>
          </div>
          <Switch checked={isActive} onCheckedChange={setIsActive} label="حساب فعال باشد" />
          {error ? <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive">{error}</p> : null}
          <div className="flex gap-2">
            <Button type="submit" disabled={saving || !phone.trim()}>
              {saving ? "در حال ایجاد..." : "ایجاد کاربر"}
            </Button>
            <Button type="button" variant="ghost" onClick={onCancel}>
              انصراف
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

function EditUserPanel({
  user,
  onSaved,
  onClose,
}: {
  user: FundziUser | null;
  onSaved: (user: FundziUser) => void;
  onClose: () => void;
}) {
  const [firstName, setFirstName] = useState(user?.first_name || "");
  const [lastName, setLastName] = useState(user?.last_name || "");
  const [isActive, setIsActive] = useState(user?.is_active ?? true);
  const [role, setRole] = useState<UserRole>((user?.role as UserRole) || "applicant");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);

  if (!user) {
    return (
      <Card className="lg:sticky lg:top-20 lg:self-start">
        <CardContent className="grid place-items-center gap-3 py-12 text-center text-sm text-muted-foreground">
          <span className="grid h-12 w-12 place-items-center rounded-full bg-muted">
            <ShieldAlert className="h-6 w-6" />
          </span>
          برای ویرایش، یک کاربر را از جدول انتخاب کنید.
        </CardContent>
      </Card>
    );
  }

  async function save() {
    setError("");
    setMessage("");
    setSaving(true);
    try {
      let updated = await updateUser(user!.id, {
        first_name: firstName,
        last_name: lastName,
        is_active: isActive,
      });
      if (role !== user!.role) {
        updated = await setUserRole(user!.id, role);
      }
      onSaved(updated);
      setMessage("تغییرات ذخیره شد.");
    } catch (exception) {
      setError(apiErrorMessage(exception, "ذخیره تغییرات با خطا مواجه شد."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card className="lg:sticky lg:top-20 lg:self-start">
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle className="text-base">ویرایش کاربر</CardTitle>
        <Button size="icon" variant="ghost" onClick={onClose} aria-label="بستن">
          <X className="h-4 w-4" />
        </Button>
      </CardHeader>
      <CardContent className="grid gap-4">
        <div className="rounded-lg bg-muted/50 px-3 py-2 text-sm" dir="ltr">
          {user.username}
        </div>
        <div className="grid gap-1.5">
          <Label>نام</Label>
          <Input value={firstName} onChange={(event) => setFirstName(event.target.value)} />
        </div>
        <div className="grid gap-1.5">
          <Label>نام خانوادگی</Label>
          <Input value={lastName} onChange={(event) => setLastName(event.target.value)} />
        </div>
        <div className="grid gap-1.5">
          <Label>نقش</Label>
          <Select value={role} onChange={(event) => setRole(event.target.value as UserRole)}>
            {ROLE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
          <p className="text-xs text-muted-foreground">
            {ROLE_OPTIONS.find((option) => option.value === role)?.description}
          </p>
        </div>
        <Switch checked={isActive} onCheckedChange={setIsActive} label="حساب فعال" />
        {error ? <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive">{error}</p> : null}
        {message ? <p className="rounded-lg bg-success/10 px-3 py-2 text-sm font-medium text-success">{message}</p> : null}
        <Button onClick={save} disabled={saving}>
          {saving ? "در حال ذخیره..." : "ذخیره تغییرات"}
        </Button>
      </CardContent>
    </Card>
  );
}
