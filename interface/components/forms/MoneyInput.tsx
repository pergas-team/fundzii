import { Input } from "@/components/ui/input";

export function MoneyInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <Input inputMode="numeric" type="number" step="any" {...props} />;
}
