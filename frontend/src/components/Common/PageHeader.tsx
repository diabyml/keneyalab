import { ArrowLeft, type LucideIcon } from "lucide-react"
import type { ReactNode } from "react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface PageHeaderProps {
  title: string
  description?: string
  eyebrow?: string
  icon?: LucideIcon
  metadata?: ReactNode
  actions?: ReactNode
  backTo?: string
  className?: string
}

export function PageHeader({
  title,
  description,
  eyebrow,
  icon: Icon,
  metadata,
  actions,
  backTo,
  className,
}: PageHeaderProps) {
  return (
    <header
      className={cn(
        "flex flex-col gap-4 border-b border-border/80 pb-5 sm:flex-row sm:items-end sm:justify-between",
        className,
      )}
    >
      <div className="flex min-w-0 items-start gap-3">
        {backTo && (
          <Button
            variant="outline"
            size="icon"
            className="mt-0.5 shrink-0"
            asChild
          >
            <a href={backTo}>
              <ArrowLeft />
              <span className="sr-only">Retour</span>
            </a>
          </Button>
        )}
        {Icon && (
          <div className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-lg border border-primary/15 bg-primary/10 text-primary">
            <Icon className="size-[18px]" />
          </div>
        )}
        <div className="min-w-0">
          {eyebrow && (
            <p className="mb-1 text-[0.65rem] font-semibold uppercase tracking-[0.16em] text-primary">
              {eyebrow}
            </p>
          )}
          <h1 className="font-heading text-2xl font-semibold tracking-tight text-foreground">
            {title}
          </h1>
          {description && (
            <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
              {description}
            </p>
          )}
          {metadata && (
            <div className="mt-2 text-xs text-muted-foreground">{metadata}</div>
          )}
        </div>
      </div>
      {actions && (
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          {actions}
        </div>
      )}
    </header>
  )
}
