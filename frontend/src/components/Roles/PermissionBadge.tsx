import type { PermissionPublic } from "@/client"
import { cn } from "@/lib/utils"

const ACTION_COLORS: Record<string, string> = {
  create: "bg-chart-1/10 text-chart-1 border-chart-1/20",
  read: "bg-chart-3/10 text-chart-3 border-chart-3/20",
  view: "bg-chart-3/10 text-chart-3 border-chart-3/20",
  update: "bg-chart-4/10 text-chart-4 border-chart-4/20",
  edit: "bg-chart-4/10 text-chart-4 border-chart-4/20",
  delete: "bg-destructive/10 text-destructive border-destructive/20",
  manage: "bg-chart-5/10 text-chart-5 border-chart-5/20",
  collect: "bg-chart-2/10 text-chart-2 border-chart-2/20",
  verify: "bg-chart-2/10 text-chart-2 border-chart-2/20",
  release: "bg-chart-1/10 text-chart-1 border-chart-1/20",
  enter: "bg-chart-3/10 text-chart-3 border-chart-3/20",
  cancel: "bg-destructive/10 text-destructive border-destructive/20",
  reject: "bg-destructive/10 text-destructive border-destructive/20",
  void: "bg-destructive/10 text-destructive border-destructive/20",
  refund: "bg-destructive/10 text-destructive border-destructive/20",
  pay: "bg-chart-2/10 text-chart-2 border-chart-2/20",
  acknowledge: "bg-chart-3/10 text-chart-3 border-chart-3/20",
}

function actionColor(action: string): string {
  return (
    ACTION_COLORS[action] ??
    "bg-muted text-muted-foreground border-muted-foreground/20"
  )
}

/** Colored badge showing just the action */
export function ActionBadge({ action }: { action: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-1.5 py-0 text-xs font-medium font-mono",
        actionColor(action),
      )}
    >
      {action}
    </span>
  )
}

/** Compact `resource:action` pill */
export function PermissionPill({
  resource,
  action,
}: {
  resource: string
  action: string
}) {
  return (
    <span className="inline-flex items-center gap-0.5 rounded-md bg-muted/50 px-2 py-0.5 text-xs font-mono">
      <span className="text-muted-foreground">{resource}</span>
      <span className="text-muted-foreground/50">:</span>
      <span className="text-primary font-medium">{action}</span>
    </span>
  )
}

/** Group permissions by resource, sorted alphabetically */
export function groupPermissionsByResource(
  permissions: PermissionPublic[],
): [string, PermissionPublic[]][] {
  const map = new Map<string, PermissionPublic[]>()
  for (const perm of permissions) {
    const list = map.get(perm.resource) ?? []
    list.push(perm)
    map.set(perm.resource, list)
  }
  return Array.from(map.entries()).sort((a, b) => a[0].localeCompare(b[0]))
}
