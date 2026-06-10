import { useQuery } from "@tanstack/react-query"
import { Search } from "lucide-react"
import { useMemo, useState } from "react"

import type { OrderStatus, SortOrder } from "@/client"
import { OrdersService } from "@/client"
import { ServerDataTable } from "@/components/Common/ServerDataTable"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { getOrderColumns } from "./columns"
import { ORDER_STATUS_LABELS, orderExportColumns } from "./utils"

interface EmbeddedOrdersTableProps {
  patientId?: string
  doctorId?: string
}

export function EmbeddedOrdersTable({
  patientId,
  doctorId,
}: EmbeddedOrdersTableProps) {
  const [search, setSearch] = useState("")
  const [status, setStatus] = useState<OrderStatus | "all">("all")
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(10)
  const [sortBy, setSortBy] = useState("created_at")
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc")

  const query = useQuery({
    queryKey: [
      "orders",
      {
        patientId,
        doctorId,
        search,
        status,
        page,
        pageSize,
        sortBy,
        sortOrder,
      },
    ],
    queryFn: () =>
      OrdersService.readOrders({
        patientId,
        doctorId,
        skip: page * pageSize,
        limit: pageSize,
        search: search.trim() || undefined,
        status: status === "all" ? undefined : status,
        sortBy,
        sortOrder,
      }),
  })

  const columns = useMemo(
    () =>
      getOrderColumns({
        showPatient: patientId === undefined,
        showDoctor: doctorId === undefined,
      }),
    [doctorId, patientId],
  )
  const exportColumns = useMemo(
    () =>
      orderExportColumns().filter(
        (column) =>
          (patientId === undefined ||
            !["Patient", "Identifiant patient"].includes(column.header)) &&
          (doctorId === undefined || column.header !== "Médecin"),
      ),
    [doctorId, patientId],
  )

  const onSort = (key: string) => {
    if (key === sortBy) setSortOrder(sortOrder === "asc" ? "desc" : "asc")
    else {
      setSortBy(key)
      setSortOrder("asc")
    }
    setPage(0)
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-2 sm:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(event) => {
              setSearch(event.currentTarget.value)
              setPage(0)
            }}
            className="pl-9"
            placeholder="Rechercher une demande…"
            aria-label="Rechercher dans les demandes"
          />
        </div>
        <Select
          value={status}
          onValueChange={(value) => {
            setStatus(value as OrderStatus | "all")
            setPage(0)
          }}
        >
          <SelectTrigger className="w-full sm:w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tous les statuts</SelectItem>
            {Object.entries(ORDER_STATUS_LABELS).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <ServerDataTable
        columns={columns}
        data={query.data?.data ?? []}
        loading={query.isLoading}
        totalCount={query.data?.count ?? 0}
        page={page}
        pageSize={pageSize}
        sortBy={sortBy}
        sortOrder={sortOrder}
        sortableColumns={{
          accession_number: "accession_number",
          status: "status",
          created_at: "created_at",
        }}
        onPageChange={setPage}
        onPageSizeChange={(value) => {
          setPageSize(value)
          setPage(0)
        }}
        onSortChange={onSort}
        emptyMessage="Aucune demande trouvée."
        exportFilename="demandes.csv"
        exportColumns={exportColumns}
      />
    </div>
  )
}
