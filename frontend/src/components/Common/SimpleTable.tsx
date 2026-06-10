import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table"
import { Download } from "lucide-react"
import { useMemo, useState } from "react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { downloadCsv, type ExportColumn } from "./tableExport"

interface SimpleTableProps<TData extends object, TValue> {
  columns: ColumnDef<TData, TValue>[]
  data: TData[]
  enableSelection?: boolean
  getRowId?: (row: TData) => string
  exportColumns?: ExportColumn<TData>[]
  exportFilename?: string
}

function defaultGetRowId<TData extends object>(row: TData) {
  const maybeId = (row as { id?: unknown }).id
  return typeof maybeId === "string" ? maybeId : JSON.stringify(row)
}

export function SimpleTable<TData extends object, TValue>({
  columns,
  data,
  enableSelection = true,
  getRowId = defaultGetRowId,
  exportColumns,
  exportFilename = "export.csv",
}: SimpleTableProps<TData, TValue>) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  })
  const ids = useMemo(() => data.map(getRowId), [data, getRowId])
  const selectedRows = data.filter((row) => selectedIds.has(getRowId(row)))
  const allSelected = ids.length > 0 && ids.every((id) => selectedIds.has(id))
  const partiallySelected =
    ids.some((id) => selectedIds.has(id)) && !allSelected

  const toggleAll = () => {
    setSelectedIds((current) => {
      if (ids.every((id) => current.has(id))) return new Set()
      return new Set(ids)
    })
  }

  const toggleOne = (id: string) => {
    setSelectedIds((current) => {
      const next = new Set(current)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  return (
    <Card className="overflow-hidden p-0">
      <div className="flex flex-col gap-4">
        {enableSelection && (
          <div className="flex flex-wrap items-center justify-between gap-3 border-b bg-muted/20 p-3">
            <div className="text-sm text-muted-foreground">
              <span className="font-medium text-foreground">
                {selectedIds.size}
              </span>{" "}
              sélectionnée{selectedIds.size !== 1 && "s"}
            </div>
            <Button
              variant="outline"
              size="sm"
              disabled={selectedRows.length === 0}
              onClick={() =>
                downloadCsv({
                  rows: selectedRows,
                  columns: exportColumns,
                  filename: exportFilename,
                })
              }
            >
              <Download className="size-4" />
              Exporter CSV
            </Button>
          </div>
        )}
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id} className="hover:bg-transparent">
                {enableSelection && (
                  <TableHead className="w-10">
                    <Checkbox
                      checked={
                        partiallySelected ? "indeterminate" : allSelected
                      }
                      onCheckedChange={toggleAll}
                      aria-label="Sélectionner toutes les lignes"
                    />
                  </TableHead>
                )}
                {headerGroup.headers.map((header) => {
                  return (
                    <TableHead key={header.id}>
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext(),
                          )}
                    </TableHead>
                  )
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.length ? (
              table.getRowModel().rows.map((row) => {
                const rowId = getRowId(row.original)
                return (
                  <TableRow key={row.id}>
                    {enableSelection && (
                      <TableCell>
                        <Checkbox
                          checked={selectedIds.has(rowId)}
                          onCheckedChange={() => toggleOne(rowId)}
                          aria-label="Sélectionner la ligne"
                        />
                      </TableCell>
                    )}
                    {row.getVisibleCells().map((cell) => (
                      <TableCell key={cell.id}>
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext(),
                        )}
                      </TableCell>
                    ))}
                  </TableRow>
                )
              })
            ) : (
              <TableRow className="hover:bg-transparent">
                <TableCell
                  colSpan={columns.length + (enableSelection ? 1 : 0)}
                  className="h-32 text-center text-muted-foreground"
                >
                  Aucun résultat trouvé.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </Card>
  )
}
