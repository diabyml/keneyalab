import type { ColumnDef } from "@tanstack/react-table"

import type { ValidationRuleDetailPublic } from "@/client"
import type { ExportColumn } from "@/components/Common/tableExport"
import { Badge } from "@/components/ui/badge"
import { DATA_TYPE_LABELS } from "./labels"
import type { EditValidationRuleHandler } from "./types"
import { populationLabel, ruleSummary } from "./utils"
import { ValidationRuleActionsMenu } from "./ValidationRuleActionsMenu"

export function getValidationRuleColumns(
  onEdit: EditValidationRuleHandler,
): ColumnDef<ValidationRuleDetailPublic>[] {
  return [
    {
      id: "analyte_code",
      header: "Analyte",
      cell: ({ row }) => (
        <div>
          <div className="font-medium">{row.original.analyte_name}</div>
          <div className="font-mono text-xs text-muted-foreground">
            {row.original.analyte_code}
          </div>
        </div>
      ),
    },
    {
      accessorKey: "analyte_data_type",
      header: "Type",
      cell: ({ row }) => (
        <Badge variant="outline">
          {DATA_TYPE_LABELS[row.original.analyte_data_type]}
        </Badge>
      ),
    },
    {
      id: "population",
      header: "Population",
      cell: ({ row }) => (
        <span className="text-sm text-muted-foreground">
          {populationLabel(row.original)}
        </span>
      ),
    },
    {
      id: "summary",
      header: "Plages / règle",
      cell: ({ row }) => <RuleSummaryCell rule={row.original} />,
    },
    {
      accessorKey: "priority",
      header: "Priorité",
      cell: ({ row }) => row.original.priority ?? 0,
    },
    {
      accessorKey: "is_active",
      header: "Statut",
      cell: ({ row }) => (
        <Badge variant={row.original.is_active ? "secondary" : "outline"}>
          {row.original.is_active ? "Active" : "Inactive"}
        </Badge>
      ),
    },
    {
      id: "actions",
      header: () => <span className="sr-only">Actions</span>,
      cell: ({ row }) => (
        <div className="flex justify-end">
          <ValidationRuleActionsMenu rule={row.original} onEdit={onEdit} />
        </div>
      ),
    },
  ]
}

export const validationRuleExportColumns: ExportColumn<ValidationRuleDetailPublic>[] =
  [
    { header: "Analyte", value: (row) => row.analyte_name },
    { header: "Code", value: (row) => row.analyte_code },
    {
      header: "Type",
      value: (row) => DATA_TYPE_LABELS[row.analyte_data_type],
    },
    { header: "Population", value: (row) => populationLabel(row) },
    { header: "Priorité", value: (row) => row.priority ?? 0 },
    {
      header: "Statut",
      value: (row) => (row.is_active ? "Active" : "Inactive"),
    },
  ]

function RuleSummaryCell({ rule }: { rule: ValidationRuleDetailPublic }) {
  const summary = ruleSummary(rule)

  if ("text" in summary) {
    return <span className="text-muted-foreground">{summary.text}</span>
  }

  return (
    <div className="max-w-md space-y-1 text-sm text-muted-foreground">
      <div>
        Normal: {summary.normal} {summary.unit}
      </div>
      {(summary.panic || summary.absurd) && (
        <div>
          {summary.panic && <>Panique: {summary.panic}</>}
          {summary.panic && summary.absurd && " · "}
          {summary.absurd && <>Absurde: {summary.absurd}</>}
        </div>
      )}
    </div>
  )
}
