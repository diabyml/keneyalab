import {
  AlertTriangle,
  Ban,
  CheckCircle2,
  Circle,
  CircleDot,
  Clock3,
  LoaderCircle,
} from "lucide-react"
import type { ComponentProps } from "react"

import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

type StatusTone =
  | "neutral"
  | "pending"
  | "progress"
  | "success"
  | "warning"
  | "critical"
  | "inactive"

const toneStyles: Record<StatusTone, string> = {
  neutral: "border-border bg-muted/60 text-muted-foreground",
  pending: "border-info/25 bg-info/10 text-info",
  progress: "border-primary/25 bg-primary/10 text-primary",
  success: "border-success/25 bg-success/10 text-success",
  warning:
    "border-warning/30 bg-warning/12 text-[color-mix(in_srgb,var(--warning),#513000_28%)] dark:text-warning",
  critical: "border-destructive/30 bg-destructive/10 text-destructive",
  inactive: "border-border bg-muted/45 text-muted-foreground",
}

const toneIcons = {
  neutral: Circle,
  pending: Clock3,
  progress: LoaderCircle,
  success: CheckCircle2,
  warning: AlertTriangle,
  critical: CircleDot,
  inactive: Ban,
} satisfies Record<StatusTone, typeof Circle>

interface StatusBadgeProps
  extends Omit<ComponentProps<typeof Badge>, "variant"> {
  tone?: StatusTone
  showIcon?: boolean
}

export function StatusBadge({
  tone = "neutral",
  showIcon = true,
  className,
  children,
  ...props
}: StatusBadgeProps) {
  const Icon = toneIcons[tone]

  return (
    <Badge
      variant="outline"
      className={cn("font-semibold", toneStyles[tone], className)}
      {...props}
    >
      {showIcon && (
        <Icon className={cn(tone === "progress" && "animate-spin")} />
      )}
      {children}
    </Badge>
  )
}
