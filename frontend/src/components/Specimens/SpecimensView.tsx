import { useQuery } from "@tanstack/react-query"
import { Search } from "lucide-react"
import { useCallback, useEffect, useMemo, useState } from "react"

import type { PaymentStatus, SortOrder } from "@/client"
import { SpecimensService } from "@/client"
import {
  SearchSelect,
  type SearchSelectOption,
} from "@/components/Common/SearchSelect"
import { ServerDataTable } from "@/components/Common/ServerDataTable"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { usePermission } from "@/hooks/usePermission"
import { specimenQueueColumns } from "./columns"
import { SpecimenCollectionSheet } from "./SpecimenCollectionSheet"
import { PAYMENT_LABELS, specimenQueueExportColumns } from "./utils"

type QueueView = "waiting" | "history"

export function SpecimensView() {
  const canCollect = usePermission("specimens", "collect")
  const [view, setView] = useState<QueueView>("waiting")
  const [search, setSearch] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [specimenTypeId, setSpecimenTypeId] = useState<string | null>(null)
  const [specimenTypeOption, setSpecimenTypeOption] =
    useState<SearchSelectOption | null>(null)
  const [paymentStatus, setPaymentStatus] = useState<PaymentStatus | "all">(
    "all",
  )
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(10)
  const [sortBy, setSortBy] = useState("created_at")
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc")
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null)

  useEffect(() => {
    const timeout = window.setTimeout(
      () => setDebouncedSearch(search.trim()),
      300,
    )
    return () => window.clearTimeout(timeout)
  }, [search])

  const query = useQuery({
    queryKey: [
      "specimen-queue",
      {
        view,
        search: debouncedSearch,
        specimenTypeId,
        paymentStatus,
        page,
        pageSize,
        sortBy,
        sortOrder,
      },
    ],
    queryFn: () =>
      SpecimensService.readCollectionQueue({
        skip: page * pageSize,
        limit: pageSize,
        search: debouncedSearch || undefined,
        view,
        specimenTypeId: specimenTypeId || undefined,
        paymentStatus: paymentStatus === "all" ? undefined : paymentStatus,
        sortBy,
        sortOrder,
      }),
  })

  const loadSpecimenTypes = useCallback(
    async (query: string): Promise<SearchSelectOption[]> => {
      const response = await SpecimensService.readSpecimenTypeOptions({
        search: query || undefined,
        limit: 20,
      })
      return response.data.map((item) => ({
        value: item.id,
        label: item.name,
        description: item.description ?? undefined,
      }))
    },
    [],
  )
  const columns = useMemo(
    () =>
      specimenQueueColumns({
        canCollect,
        onCollect: setSelectedOrderId,
      }),
    [canCollect],
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
      <Tabs
        value={view}
        onValueChange={(value) => {
          setView(value as QueueView)
          setPage(0)
        }}
      >
        <TabsList>
          <TabsTrigger value="waiting">À prélever</TabsTrigger>
          <TabsTrigger value="history">Historique</TabsTrigger>
        </TabsList>
      </Tabs>

      <div className="grid gap-2 md:grid-cols-[minmax(240px,1fr)_240px_180px]">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(event) => {
              setSearch(event.currentTarget.value)
              setPage(0)
            }}
            className="pl-9"
            placeholder="N° demande, patient, identifiant…"
          />
        </div>
        <SearchSelect
          value={specimenTypeId}
          selectedOption={specimenTypeOption}
          onValueChange={(value, option) => {
            setSpecimenTypeId(value)
            setSpecimenTypeOption(option ?? null)
            setPage(0)
          }}
          loadOptions={loadSpecimenTypes}
          placeholder="Tous les types"
          searchPlaceholder="Rechercher un type…"
        />
        <Select
          value={paymentStatus}
          onValueChange={(value) => {
            setPaymentStatus(value as PaymentStatus | "all")
            setPage(0)
          }}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tous les paiements</SelectItem>
            {Object.entries(PAYMENT_LABELS).map(([value, label]) => (
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
          patient_name: "patient_name",
          created_at: "created_at",
        }}
        onPageChange={setPage}
        onPageSizeChange={(value) => {
          setPageSize(value)
          setPage(0)
        }}
        onSortChange={onSort}
        getRowId={(row) => row.order_id}
        emptyMessage={
          view === "waiting"
            ? "Aucun prélèvement en attente."
            : "Aucun historique de prélèvement."
        }
        exportFilename="prelevements.csv"
        exportColumns={specimenQueueExportColumns()}
      />
      <SpecimenCollectionSheet
        orderId={selectedOrderId}
        onOpenChange={(open) => !open && setSelectedOrderId(null)}
      />
    </div>
  )
}
