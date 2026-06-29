import { optionLabel, optionValue } from "@/lib/utils/formSchema";
import type { DynamicFormField } from "@/types/form";

export function SelectField({
  field,
  value,
  onChange,
}: {
  field: DynamicFormField;
  value?: string;
  onChange: (value: string) => void;
}) {
  return (
    <select
      value={value || ""}
      onChange={(event) => onChange(event.target.value)}
      className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      <option value="">انتخاب کنید</option>
      {(field.options || []).map((option) => (
        <option key={optionValue(option)} value={optionValue(option)}>
          {optionLabel(option)}
        </option>
      ))}
    </select>
  );
}
