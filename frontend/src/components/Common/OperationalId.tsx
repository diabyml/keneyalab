import type { HTMLAttributes } from "react"

import { cn } from "@/lib/utils"

export function OperationalId({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 font-mono text-xs font-semibold tracking-tight text-primary",
        className,
      )}
      {...props}
    >
      <span
        aria-hidden="true"
        className="barcode-accent h-3 w-3.5 shrink-0 opacity-55"
      />
      {children}
    </span>
  )
}
