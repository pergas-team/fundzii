"use client";

import { useState } from "react";
import { Upload } from "lucide-react";
import { Input } from "@/components/ui/input";

export function FileUploadField({ name, required }: { name: string; required?: boolean }) {
  const [fileName, setFileName] = useState("");
  return (
    <div className="grid gap-2">
      <Input
        name={name}
        type="file"
        required={required}
        onChange={(event) => setFileName(event.target.files?.[0]?.name || "")}
      />
      {fileName ? (
        <span className="inline-flex items-center gap-2 text-xs text-muted-foreground">
          <Upload className="h-3.5 w-3.5" />
          {fileName}
        </span>
      ) : null}
    </div>
  );
}
