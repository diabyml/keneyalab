import { useQuery } from "@tanstack/react-query"
import { Search } from "lucide-react"
import { useCallback, useEffect, useState } from "react"

import type { PaymentStatus, SortOrder } from "@/client"
import { InvoicesService } from "@/client"
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
import { invoiceColumns } from "./columns"
import { INVOICE_STATUS_LABELS, invoiceExportColumns } from "./utils"

type VersionFilter = "active" | "voided" | "all"

export function InvoicesView() {
  const [search, setSearch] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [status, setStatus] = useState<PaymentStatus | "all">("all")
  const [versionFilter, setVersionFilter] = useState<VersionFilter>("active")
  const [insuranceId, setInsuranceId] = useState<string | null>(null)
  const [insuranceOption, setInsuranceOption] =
    useState<SearchSelectOption | null>(null)
  const [methodId, setMethodId] = useState<string | null>(null)
  const [methodOption, setMethodOption] = useState<SearchSelectOption | null>(
    null,
  )
  const [createdFrom, setCreatedFrom] = useState("")
  const [createdTo, setCreatedTo] = useState("")
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(10)
  const [sortBy, setSortBy] = useState("created_at")
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc")

  useEffect(() => {
    const timeout = window.setTimeout(
      () => setDebouncedSearch(search.trim()),
      300,
    )
    return () => window.clearTimeout(timeout)
  }, [search])

  const filters = {
    search: debouncedSearch || undefined,
    paymentStatus: status === "all" ? undefined : status,
    insuranceProviderId: insuranceId || undefined,
    paymentMethodId: methodId || undefined,
    isVoided: versionFilter === "all" ? undefined : versionFilter === "voided",
    createdFrom: createdFrom
      ? new Date(`${createdFrom}T00:00:00`).toISOString()
      : undefined,
    createdTo: createdTo
      ? new Date(`${createdTo}T23:59:59`).toISOString()
      : undefined,
  }
  const query = useQuery({
    queryKey: ["invoices", { ...filters, page, pageSize, sortBy, sortOrder }],
    queryFn: () =>
      InvoicesService.readInvoices({
        ...filters,
        skip: page * pageSize,
        limit: pageSize,
        sortBy,
        sortOrder,
      }),
  })
  const summaryQuery = useQuery({
    queryKey: ["invoices", "summary", filters],
    queryFn: () => InvoicesService.readInvoiceSummary(filters),
  })

  const loadInsurers = useCallback(
    async (query: string): Promise<SearchSelectOption[]> => {
      const response =
        await InvoicesService.readInvoiceInsuranceProviderOptions({
          search: query || undefined,
          limit: 20,
        })
      return response.data.map((item) => ({
        value: item.id,
        label: item.name,
      }))
    },
    [],
  )
  const loadMethods = useCallback(
    async (query: string): Promise<SearchSelectOption[]> => {
      const response = await InvoicesService.readInvoicePaymentMethodOptions({
        search: query || undefined,
        limit: 20,
      })
      return response.data.map((item) => ({
        value: item.id,
        label: item.name,
      }))
    },
    [],
  )
  const onSort = (key: string) => {
    if (key === sortBy) setSortOrder(sortOrder === "asc" ? "desc" : "asc")
    else {
      setSortBy(key)
      setSortOrder("asc")
    }
    setPage(0)
  }
  const summary = summaryQuery.data

  return (
    <div className="space-y-4">
      <div className="grid divide-y rounded-md border sm:grid-cols-2 sm:divide-x sm:divide-y-0 xl:grid-cols-4">
        <Metric label="Factures" value={String(summary?.count ?? 0)} />
        <Metric label="Net facturé" value={summary?.net_billed} money />
        <Metric label="Encaissé" value={summary?.collected} money />
        <Metric label="À encaisser" value={summary?.outstanding} money />
      </div>

      <div className="grid gap-2 xl:grid-cols-[minmax(220px,1fr)_180px_180px_220px_220px]">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(event) => {
              setSearch(event.currentTarget.value)
              setPage(0)
            }}
            className="pl-9"
            placeholder="Facture, demande, patient…"
          />
        </div>
        <Select
          value={status}
          onValueChange={(value) => {
            setStatus(value as PaymentStatus | "all")
            setPage(0)
          }}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tous les statuts</SelectItem>
            {Object.entries(INVOICE_STATUS_LABELS).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select
          value={versionFilter}
          onValueChange={(value) => {
            setVersionFilter(value as VersionFilter)
            setPage(0)
          }}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="active">Versions actives</SelectItem>
            <SelectItem value="voided">Versions annulées</SelectItem>
            <SelectItem value="all">Toutes les versions</SelectItem>
          </SelectContent>
        </Select>
        <SearchSelect
          value={insuranceId}
          selectedOption={insuranceOption}
          onValueChange={(value, option) => {
            setInsuranceId(value)
            setInsuranceOption(option ?? null)
            setPage(0)
          }}
          loadOptions={loadInsurers}
          placeholder="Toutes les assurances"
          searchPlaceholder="Rechercher une assurance…"
        />
        <SearchSelect
          value={methodId}
          selectedOption={methodOption}
          onValueChange={(value, option) => {
            setMethodId(value)
            setMethodOption(option ?? null)
            setPage(0)
          }}
          loadOptions={loadMethods}
          placeholder="Toutes les méthodes"
          searchPlaceholder="Rechercher une méthode…"
        />
      </div>
      <div className="flex flex-wrap gap-2">
        <Input
          type="date"
          value={createdFrom}
          onChange={(event) => {
            setCreatedFrom(event.currentTarget.value)
            setPage(0)
          }}
          className="w-44"
          aria-label="Date de début"
        />
        <Input
          type="date"
          value={createdTo}
          onChange={(event) => {
            setCreatedTo(event.currentTarget.value)
            setPage(0)
          }}
          className="w-44"
          aria-label="Date de fin"
        />
      </div>

      <ServerDataTable
        columns={invoiceColumns}
        data={query.data?.data ?? []}
        loading={query.isLoading}
        totalCount={query.data?.count ?? 0}
        page={page}
        pageSize={pageSize}
        sortBy={sortBy}
        sortOrder={sortOrder}
        sortableColumns={{
          invoice_number: "invoice_number",
          net_amount: "net_amount",
          payment_status: "payment_status",
          created_at: "created_at",
        }}
        onPageChange={setPage}
        onPageSizeChange={(value) => {
          setPageSize(value)
          setPage(0)
        }}
        onSortChange={onSort}
        emptyMessage="Aucune facture trouvée."
        exportFilename="factures.csv"
        exportColumns={invoiceExportColumns()}
      />
    </div>
  )
}

function Metric({
  label,
  value,
  money = false,
}: {
  label: string
  value?: string
  money?: boolean
}) {
  const formatted = money
    ? new Intl.NumberFormat("fr-FR", {
        style: "currency",
        currency: "XOF",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(Number(value ?? 0))
    : value
  return (
    <div className="p-4">
      <div className="text-xs font-medium text-muted-foreground">{label}</div>
      <div className="mt-1 text-xl font-semibold tabular-nums">{formatted}</div>
    </div>
  )
}
