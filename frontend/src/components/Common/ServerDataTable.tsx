import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table"
import { ChevronLeft, ChevronRight, Download } from "lucide-react"
import { useEffect, useMemo, useState } from "react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { cn } from "@/lib/utils"
import { downloadCsv, type ExportColumn } from "./tableExport"

interface ServerDataTableProps<TData extends object, TValue> {
  columns: ColumnDef<TData, TValue>[]
  data: TData[]
  loading?: boolean
  totalCount: number
  page: number
  pageSize: number
  pageSizeOptions?: number[]
  sortBy?: string
  sortOrder?: "asc" | "desc"
  sortableColumns?: Record<string, string>
  onPageChange: (page: number) => void
  onPageSizeChange: (pageSize: number) => void
  onSortChange?: (sortBy: string) => void
  emptyMessage?: string
  getRowId?: (row: TData) => string
  getRowClassName?: (row: TData) => string | undefined
  enableSelection?: boolean
  exportColumns?: ExportColumn<TData>[]
  exportFilename?: string
}

const DEFAULT_PAGE_SIZE_OPTIONS = [10, 25, 50, 100]

function defaultGetRowId<TData extends object>(row: TData) {
  const maybeId = (row as { id?: unknown }).id
  return typeof maybeId === "string" ? maybeId : JSON.stringify(row)
}

export function ServerDataTable<TData extends object, TValue>({
  columns,
  data,
  loading = false,
  totalCount,
  page,
  pageSize,
  pageSizeOptions = DEFAULT_PAGE_SIZE_OPTIONS,
  sortBy,
  sortOrder = "asc",
  sortableColumns = {},
  onPageChange,
  onPageSizeChange,
  onSortChange,
  emptyMessage = "Aucun résultat trouvé.",
  getRowId = defaultGetRowId,
  getRowClassName,
  enableSelection = true,
  exportColumns,
  exportFilename = "export.csv",
}: ServerDataTableProps<TData, TValue>) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  })
  const pageCount = Math.max(1, Math.ceil(totalCount / pageSize))
  const ids = useMemo(() => data.map(getRowId), [data, getRowId])
  const selectionResetKey = `${page}:${pageSize}:${sortBy ?? ""}:${sortOrder}:${ids.join("|")}`
  const selectedRows = data.filter((row) => selectedIds.has(getRowId(row)))
  const allSelected = ids.length > 0 && ids.every((id) => selectedIds.has(id))
  const partiallySelected =
    ids.some((id) => selectedIds.has(id)) && !allSelected

  useEffect(() => {
    void selectionResetKey
    setSelectedIds(new Set())
  }, [selectionResetKey])

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

  const sortLabel = (columnId: string) => {
    const mapped = sortableColumns[columnId]
    if (!mapped || mapped !== sortBy) return null
    return sortOrder === "asc" ? " ↑" : " ↓"
  }

  return (
    <Card className="overflow-hidden p-0">
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
                    checked={partiallySelected ? "indeterminate" : allSelected}
                    onCheckedChange={toggleAll}
                    aria-label="Sélectionner toutes les lignes"
                  />
                </TableHead>
              )}
              {headerGroup.headers.map((header) => {
                const mappedSort = sortableColumns[header.column.id]
                const content = header.isPlaceholder
                  ? null
                  : flexRender(
                      header.column.columnDef.header,
                      header.getContext(),
                    )
                return (
                  <TableHead key={header.id}>
                    {mappedSort && onSortChange ? (
                      <button
                        type="button"
                        onClick={() => onSortChange(mappedSort)}
                      >
                        {content}
                        {sortLabel(header.column.id)}
                      </button>
                    ) : (
                      content
                    )}
                  </TableHead>
                )
              })}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {loading ? (
            Array.from({ length: Math.min(pageSize, 8) }).map((_, index) => (
              <TableRow key={index}>
                <TableCell colSpan={columns.length + (enableSelection ? 1 : 0)}>
                  <Skeleton className="h-8 w-full" />
                </TableCell>
              </TableRow>
            ))
          ) : table.getRowModel().rows.length === 0 ? (
            <TableRow className="hover:bg-transparent">
              <TableCell
                colSpan={columns.length + (enableSelection ? 1 : 0)}
                className="h-32 text-center text-muted-foreground"
              >
                {emptyMessage}
              </TableCell>
            </TableRow>
          ) : (
            table.getRowModel().rows.map((row) => {
              const rowId = getRowId(row.original)
              return (
                <TableRow
                  key={row.id}
                  className={cn(getRowClassName?.(row.original))}
                >
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
          )}
        </TableBody>
      </Table>

      <div className="flex flex-col gap-3 border-t bg-muted/20 p-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
          <span>
            <span className="font-medium text-foreground">{totalCount}</span>{" "}
            entrée{totalCount !== 1 && "s"}
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Lignes</span>
            <Select
              value={`${pageSize}`}
              onValueChange={(value) => onPageSizeChange(Number(value))}
            >
              <SelectTrigger className="h-8 w-[74px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {pageSizeOptions.map((size) => (
                  <SelectItem key={size} value={`${size}`}>
                    {size}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              Page{" "}
              <span className="font-medium text-foreground">{page + 1}</span>{" "}
              sur{" "}
              <span className="font-medium text-foreground">{pageCount}</span>
            </span>
            <Button
              variant="outline"
              size="icon"
              className="size-8"
              onClick={() => onPageChange(Math.max(0, page - 1))}
              disabled={page === 0}
            >
              <ChevronLeft className="size-4" />
              <span className="sr-only">Page précédente</span>
            </Button>
            <Button
              variant="outline"
              size="icon"
              className="size-8"
              onClick={() => onPageChange(Math.min(pageCount - 1, page + 1))}
              disabled={page + 1 >= pageCount}
            >
              <ChevronRight className="size-4" />
              <span className="sr-only">Page suivante</span>
            </Button>
          </div>
        </div>
      </div>
    </Card>
  )
}
