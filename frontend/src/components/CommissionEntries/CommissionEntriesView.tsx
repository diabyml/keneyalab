import { useQuery } from "@tanstack/react-query"
import { Search } from "lucide-react"
import { useCallback, useEffect, useMemo, useState } from "react"

import type { PayoutStatus, SortOrder } from "@/client"
import {
  DoctorCommissionEntriesService,
  DoctorCommissionPaymentsService,
} from "@/client"
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
import { getCommissionEntryColumns } from "./columns"
import { EntryDetailSheet } from "./EntryDetailSheet"
import { PAYOUT_STATUS_LABELS } from "./utils"

export function CommissionEntriesView() {
  const [search, setSearch] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [doctorId, setDoctorId] = useState<string | null>(null)
  const [doctorOption, setDoctorOption] = useState<SearchSelectOption | null>(
    null,
  )
  const [status, setStatus] = useState<PayoutStatus | "all">("all")
  const [createdFrom, setCreatedFrom] = useState("")
  const [createdTo, setCreatedTo] = useState("")
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(10)
  const [sortBy, setSortBy] = useState("created_at")
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc")
  const [selectedId, setSelectedId] = useState<string | null>(null)

  useEffect(() => {
    const timeout = window.setTimeout(
      () => setDebouncedSearch(search.trim()),
      300,
    )
    return () => window.clearTimeout(timeout)
  }, [search])

  const query = useQuery({
    queryKey: [
      "commission-entries",
      {
        page,
        pageSize,
        debouncedSearch,
        doctorId,
        status,
        createdFrom,
        createdTo,
        sortBy,
        sortOrder,
      },
    ],
    queryFn: () =>
      DoctorCommissionEntriesService.readEntries({
        skip: page * pageSize,
        limit: pageSize,
        search: debouncedSearch || undefined,
        doctorId,
        payoutStatus: status === "all" ? undefined : status,
        createdFrom: createdFrom
          ? new Date(`${createdFrom}T00:00:00`).toISOString()
          : undefined,
        createdTo: createdTo
          ? new Date(`${createdTo}T23:59:59`).toISOString()
          : undefined,
        sortBy,
        sortOrder,
      }),
  })

  const loadDoctors = useCallback(async (value: string) => {
    const response = await DoctorCommissionPaymentsService.readDoctorOptions({
      search: value || undefined,
      limit: 20,
    })
    return response.data.map((doctor) => ({
      value: doctor.id,
      label: `${doctor.first_name} ${doctor.last_name}`,
    }))
  }, [])
  const columns = useMemo(() => getCommissionEntryColumns(setSelectedId), [])
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
      <div className="grid gap-2 xl:grid-cols-[minmax(240px,1fr)_220px_180px_170px_170px]">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(event) => {
              setSearch(event.currentTarget.value)
              setPage(0)
            }}
            className="pl-9"
            placeholder="Médecin, patient, demande, facture…"
          />
        </div>
        <SearchSelect
          value={doctorId}
          selectedOption={doctorOption}
          onValueChange={(value, option) => {
            setDoctorId(value)
            setDoctorOption(option ?? null)
            setPage(0)
          }}
          loadOptions={loadDoctors}
          placeholder="Tous les médecins"
          searchPlaceholder="Rechercher un médecin…"
        />
        <Select
          value={status}
          onValueChange={(value) => {
            setStatus(value as PayoutStatus | "all")
            setPage(0)
          }}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tous les statuts</SelectItem>
            {Object.entries(PAYOUT_STATUS_LABELS).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Input
          type="date"
          value={createdFrom}
          onChange={(event) => {
            setCreatedFrom(event.currentTarget.value)
            setPage(0)
          }}
          aria-label="Date de début"
        />
        <Input
          type="date"
          value={createdTo}
          onChange={(event) => {
            setCreatedTo(event.currentTarget.value)
            setPage(0)
          }}
          aria-label="Date de fin"
        />
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
          doctor_name: "doctor_name",
          commission_amount: "commission_amount",
          outstanding_amount: "outstanding_amount",
          created_at: "created_at",
        }}
        onPageChange={setPage}
        onPageSizeChange={(value) => {
          setPageSize(value)
          setPage(0)
        }}
        onSortChange={onSort}
        enableSelection={false}
        emptyMessage="Aucune écriture de commission trouvée."
      />

      <EntryDetailSheet
        entryId={selectedId}
        onOpenChange={(open) => {
          if (!open) setSelectedId(null)
        }}
      />
    </div>
  )
}
