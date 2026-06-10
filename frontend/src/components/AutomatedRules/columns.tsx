import type { ColumnDef } from "@tanstack/react-table"

import type {
  ConsistencyRuleDetailPublic,
  ReflexRuleDetailPublic,
} from "@/client"
import type { ExportColumn } from "@/components/Common/tableExport"
import { Badge } from "@/components/ui/badge"
import { AutomatedRuleActionsMenu } from "./AutomatedRuleActionsMenu"
import { OPERATOR_LABELS, SEVERITY_LABELS } from "./labels"

interface ColumnHandlers<T> {
  onEdit: (rule: T) => void
  onPreview: (rule: T) => void
  onDelete: (rule: T) => void
  onRestore: (rule: T) => void
}

export function getConsistencyColumns(
  handlers: ColumnHandlers<ConsistencyRuleDetailPublic>,
): ColumnDef<ConsistencyRuleDetailPublic>[] {
  return [
    {
      accessorKey: "name",
      header: "Règle",
      cell: ({ row }) => (
        <div>
          <div className="font-medium">{row.original.name}</div>
          <div className="max-w-md truncate font-mono text-xs text-muted-foreground">
            {row.original.formula}
          </div>
        </div>
      ),
    },
    {
      accessorKey: "severity",
      header: "Sévérité",
      cell: ({ row }) => (
        <Badge
          variant={
            row.original.severity === "error" ? "destructive" : "secondary"
          }
        >
          {SEVERITY_LABELS[row.original.severity]}
        </Badge>
      ),
    },
    {
      id: "analytes",
      header: "Analytes",
      cell: ({ row }) => (
        <div className="flex max-w-sm flex-wrap gap-1">
          {(row.original.analytes ?? []).slice(0, 3).map((analyte) => (
            <Badge key={analyte.id} variant="outline" className="font-mono">
              {analyte.code}
            </Badge>
          ))}
          {(row.original.analytes?.length ?? 0) > 3 && (
            <Badge variant="outline">
              +{(row.original.analytes?.length ?? 0) - 3}
            </Badge>
          )}
        </div>
      ),
    },
    {
      accessorKey: "is_deleted",
      header: "Statut",
      cell: ({ row }) => (
        <Badge variant={row.original.is_deleted ? "outline" : "secondary"}>
          {row.original.is_deleted ? "Supprimée" : "Active"}
        </Badge>
      ),
    },
    {
      id: "actions",
      header: () => <span className="sr-only">Actions</span>,
      cell: ({ row }) => (
        <div className="flex justify-end">
          <AutomatedRuleActionsMenu rule={row.original} {...handlers} />
        </div>
      ),
    },
  ]
}

export function getReflexColumns(
  handlers: ColumnHandlers<ReflexRuleDetailPublic>,
): ColumnDef<ReflexRuleDetailPublic>[] {
  return [
    {
      id: "trigger_analyte",
      header: "Déclencheur",
      cell: ({ row }) => (
        <div>
          <div className="font-medium">{row.original.trigger_analyte_name}</div>
          <div className="font-mono text-xs text-muted-foreground">
            {row.original.trigger_analyte_code}
          </div>
        </div>
      ),
    },
    {
      accessorKey: "trigger_operator",
      header: "Condition",
      cell: ({ row }) => (
        <span className="font-mono">
          {OPERATOR_LABELS[row.original.trigger_operator]}{" "}
          {row.original.trigger_value}
        </span>
      ),
    },
    {
      id: "action_catalog",
      header: "Action",
      cell: ({ row }) => (
        <div>
          <div className="font-medium">{row.original.action_catalog_name}</div>
          <div className="font-mono text-xs text-muted-foreground">
            {row.original.action_catalog_code}
          </div>
        </div>
      ),
    },
    {
      accessorKey: "is_deleted",
      header: "Statut",
      cell: ({ row }) => (
        <Badge variant={row.original.is_deleted ? "outline" : "secondary"}>
          {row.original.is_deleted ? "Supprimée" : "Active"}
        </Badge>
      ),
    },
    {
      id: "actions",
      header: () => <span className="sr-only">Actions</span>,
      cell: ({ row }) => (
        <div className="flex justify-end">
          <AutomatedRuleActionsMenu rule={row.original} {...handlers} />
        </div>
      ),
    },
  ]
}

export const consistencyExportColumns: ExportColumn<ConsistencyRuleDetailPublic>[] =
  [
    { header: "Nom", value: (row) => row.name },
    { header: "Formule", value: (row) => row.formula },
    { header: "Sévérité", value: (row) => SEVERITY_LABELS[row.severity] },
    {
      header: "Analytes",
      value: (row) => (row.analytes ?? []).map((item) => item.code).join(", "),
    },
    {
      header: "Statut",
      value: (row) => (row.is_deleted ? "Supprimée" : "Active"),
    },
  ]

export const reflexExportColumns: ExportColumn<ReflexRuleDetailPublic>[] = [
  { header: "Analyte", value: (row) => row.trigger_analyte_name },
  { header: "Code", value: (row) => row.trigger_analyte_code },
  {
    header: "Condition",
    value: (row) =>
      `${OPERATOR_LABELS[row.trigger_operator]} ${row.trigger_value}`,
  },
  { header: "Action", value: (row) => row.action_catalog_name },
  {
    header: "Statut",
    value: (row) => (row.is_deleted ? "Supprimée" : "Active"),
  },
]
