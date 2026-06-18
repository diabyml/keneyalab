import type { ColumnDef } from "@tanstack/react-table"
import { createColumnHelper } from "@tanstack/react-table"
import { Eye } from "lucide-react"

import type { AuditLogPublic } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  AUDIT_ACTION_LABELS,
  AUDIT_CATEGORY_LABELS,
  auditEntityLabel,
} from "./labels"
import { eventSummary, formatAuditDate } from "./utils"

const helper = createColumnHelper<AuditLogPublic>()

function actionVariant(action: AuditLogPublic["action"]) {
  if (action === "delete" || action === "login_failed") return "destructive"
  if (action === "insert" || action === "login_success") return "secondary"
  return "outline"
}

export function getAuditColumns(
  onOpen: (id: string) => void,
): ColumnDef<AuditLogPublic, any>[] {
  return [
    helper.accessor("performed_at", {
      header: "Date",
      cell: ({ getValue }) => (
        <span className="whitespace-nowrap tabular-nums">
          {formatAuditDate(getValue())}
        </span>
      ),
    }),
    helper.accessor("action", {
      header: "Action",
      cell: ({ getValue }) => {
        const action = getValue() as AuditLogPublic["action"]
        return (
          <Badge variant={actionVariant(action)}>
            {AUDIT_ACTION_LABELS[action]}
          </Badge>
        )
      },
    }),
    helper.accessor("table_name", {
      header: "Entité",
      cell: ({ row }) => (
        <div className="min-w-40">
          <div className="font-medium">
            {auditEntityLabel(row.original.table_name)}
          </div>
          <div className="truncate text-xs text-muted-foreground">
            {row.original.record_label ??
              row.original.record_id ??
              "Événement global"}
          </div>
        </div>
      ),
    }),
    helper.accessor("actor_name", {
      header: "Acteur",
      cell: ({ row }) => (
        <div>
          <div>
            {row.original.actor_name ?? row.original.actor_email ?? "Système"}
          </div>
          {row.original.actor_name && row.original.actor_email && (
            <div className="text-xs text-muted-foreground">
              {row.original.actor_email}
            </div>
          )}
        </div>
      ),
    }),
    helper.display({
      id: "summary",
      header: "Résumé",
      cell: ({ row }) => (
        <div className="max-w-sm">
          <div className="line-clamp-2">{eventSummary(row.original)}</div>
          <div className="mt-1 text-xs text-muted-foreground">
            {AUDIT_CATEGORY_LABELS[row.original.category]}
          </div>
        </div>
      ),
    }),
    helper.accessor("source", {
      header: "Source",
      cell: ({ getValue }) => (
        <Badge variant="outline">
          {getValue() === "api" ? "Application" : "Système"}
        </Badge>
      ),
    }),
    helper.display({
      id: "actions",
      header: "",
      cell: ({ row }) => (
        <div className="flex justify-end">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onOpen(row.original.id)}
            aria-label="Voir le détail de l'événement"
          >
            <Eye className="size-4" />
          </Button>
        </div>
      ),
    }),
  ]
}
