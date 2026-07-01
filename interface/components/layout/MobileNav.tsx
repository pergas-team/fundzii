import { AppSidebar } from "./AppSidebar";

export function MobileNav({ mode = "user" }: { mode?: "user" | "admin" | "operator" }) {
  return <AppSidebar mode={mode} />;
}
