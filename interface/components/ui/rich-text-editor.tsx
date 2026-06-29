"use client";

import { useEffect, useId, useRef, useState } from "react";
import {
  Bold,
  Code2,
  Heading2,
  Heading3,
  Italic,
  Link2,
  List,
  ListOrdered,
  Quote,
  Underline,
} from "lucide-react";
import { cn } from "@/lib/utils";

type ToolButton = {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  command: string;
  value?: string;
};

const TOOLS: ToolButton[] = [
  { icon: Bold, title: "درشت", command: "bold" },
  { icon: Italic, title: "مورب", command: "italic" },
  { icon: Underline, title: "زیرخط", command: "underline" },
  { icon: Heading2, title: "تیتر", command: "formatBlock", value: "H2" },
  { icon: Heading3, title: "زیرتیتر", command: "formatBlock", value: "H3" },
  { icon: Quote, title: "نقل‌قول", command: "formatBlock", value: "BLOCKQUOTE" },
  { icon: List, title: "فهرست نقطه‌ای", command: "insertUnorderedList" },
  { icon: ListOrdered, title: "فهرست شماره‌دار", command: "insertOrderedList" },
];

export function RichTextEditor({
  value,
  onChange,
  placeholder,
  className,
}: {
  value: string;
  onChange: (html: string) => void;
  placeholder?: string;
  className?: string;
}) {
  const editorRef = useRef<HTMLDivElement>(null);
  const [showSource, setShowSource] = useState(false);
  const id = useId();

  // Sync external value into the editable DOM without disturbing the caret.
  useEffect(() => {
    const editor = editorRef.current;
    if (!editor || showSource) return;
    if (document.activeElement === editor) return;
    if (editor.innerHTML !== value) editor.innerHTML = value || "";
  }, [value, showSource]);

  function exec(command: string, argument?: string) {
    editorRef.current?.focus();
    document.execCommand(command, false, argument);
    if (editorRef.current) onChange(editorRef.current.innerHTML);
  }

  function insertLink() {
    const url = window.prompt("نشانی پیوند (URL) را وارد کنید:", "https://");
    if (!url) return;
    exec("createLink", url);
  }

  return (
    <div className={cn("overflow-hidden rounded-lg border border-input bg-card shadow-sm", className)}>
      <div className="flex flex-wrap items-center gap-0.5 border-b bg-muted/50 p-1.5">
        {TOOLS.map((tool) => (
          <button
            key={tool.title}
            type="button"
            title={tool.title}
            onMouseDown={(event) => event.preventDefault()}
            onClick={() => exec(tool.command, tool.value)}
            className="grid h-8 w-8 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-background hover:text-foreground"
          >
            <tool.icon className="h-4 w-4" />
          </button>
        ))}
        <button
          type="button"
          title="درج پیوند"
          onMouseDown={(event) => event.preventDefault()}
          onClick={insertLink}
          className="grid h-8 w-8 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-background hover:text-foreground"
        >
          <Link2 className="h-4 w-4" />
        </button>
        <span className="mx-1 h-5 w-px bg-border" />
        <button
          type="button"
          title="ویرایش کد HTML"
          onClick={() => setShowSource((current) => !current)}
          className={cn(
            "grid h-8 w-8 place-items-center rounded-md transition-colors hover:bg-background",
            showSource ? "bg-background text-primary" : "text-muted-foreground hover:text-foreground",
          )}
        >
          <Code2 className="h-4 w-4" />
        </button>
      </div>

      {showSource ? (
        <textarea
          dir="ltr"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="min-h-40 w-full resize-y bg-card p-3 font-mono text-xs outline-none"
          placeholder="<p>...</p>"
        />
      ) : (
        <div
          id={id}
          ref={editorRef}
          contentEditable
          suppressContentEditableWarning
          dir="rtl"
          onInput={(event) => onChange((event.target as HTMLDivElement).innerHTML)}
          data-placeholder={placeholder || "متن را اینجا بنویسید…"}
          className="prose-content min-h-40 w-full p-3.5 text-sm leading-7 outline-none empty:before:text-muted-foreground empty:before:content-[attr(data-placeholder)]"
        />
      )}
    </div>
  );
}
