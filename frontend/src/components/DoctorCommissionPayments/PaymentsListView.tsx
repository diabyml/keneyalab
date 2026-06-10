import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { Plus, Search } from "lucide-react"
import { useCallback, useEffect, useState } from "react"
import { DoctorCommissionPaymentsService, type SortOrder } from "@/client"
import {
  SearchSelect,
  type SearchSelectOption,
} from "@/components/Common/SearchSelect"
import { ServerDataTable } from "@/components/Common/ServerDataTable"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { usePermission } from "@/hooks/usePermission"
import { paymentColumns } from "./columns"

export function PaymentsListView() {
  const canPay = usePermission("commissions", "pay")
  const [search, setSearch] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [doctorId, setDoctorId] = useState<string | null>(null)
  const [doctorOption, setDoctorOption] = useState<SearchSelectOption | null>(
    null,
  )
  const [methodId, setMethodId] = useState<string | null>(null)
  const [methodOption, setMethodOption] = useState<SearchSelectOption | null>(
    null,
  )
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(25)
  const [sortBy, setSortBy] = useState("created_at")
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc")

  useEffect(() => {
    const timeout = window.setTimeout(
      () => setDebouncedSearch(search.trim()),
      300,
    )
    return () => window.clearTimeout(timeout)
  }, [search])

  const query = useQuery({
    queryKey: [
      "doctor-commission-payments",
      {
        page,
        pageSize,
        doctorId,
        methodId,
        debouncedSearch,
        sortBy,
        sortOrder,
      },
    ],
    queryFn: () =>
      DoctorCommissionPaymentsService.readPayments({
        skip: page * pageSize,
        limit: pageSize,
        doctorId,
        paymentMethodId: methodId,
        search: debouncedSearch || undefined,
        sortBy,
        sortOrder,
      }),
  })
  const loadDoctors = useCallback(async (searchValue: string) => {
    const response = await DoctorCommissionPaymentsService.readDoctorOptions({
      search: searchValue || undefined,
      limit: 20,
    })
    return response.data.map((doctor) => ({
      value: doctor.id,
      label: `${doctor.first_name} ${doctor.last_name}`,
    }))
  }, [])
  const loadMethods = useCallback(async (searchValue: string) => {
    const response =
      await DoctorCommissionPaymentsService.readPaymentMethodOptions({
        search: searchValue || undefined,
        limit: 20,
      })
    return response.data.map((method) => ({
      value: method.id,
      label: method.name,
    }))
  }, [])
  const onSort = (value: string) => {
    if (value === sortBy) setSortOrder(sortOrder === "asc" ? "desc" : "asc")
    else {
      setSortBy(value)
      setSortOrder("asc")
    }
    setPage(0)
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(event) => {
              setSearch(event.target.value)
              setPage(0)
            }}
            placeholder="Médecin, référence ou numéro…"
            className="pl-9"
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
        {canPay && (
          <Button asChild>
            <Link to="/commissions/payments/new">
              <Plus className="size-4" />
              Nouveau paiement
            </Link>
          </Button>
        )}
      </div>
      <ServerDataTable
        columns={paymentColumns}
        data={query.data?.data ?? []}
        loading={query.isLoading}
        totalCount={query.data?.count ?? 0}
        page={page}
        pageSize={pageSize}
        sortBy={sortBy}
        sortOrder={sortOrder}
        sortableColumns={{
          created_at: "created_at",
          doctor_name: "doctor_name",
          total_commission_amount: "total_commission_amount",
        }}
        onSortChange={onSort}
        onPageChange={setPage}
        onPageSizeChange={(value) => {
          setPageSize(value)
          setPage(0)
        }}
        enableSelection={false}
      />
    </div>
  )
}
