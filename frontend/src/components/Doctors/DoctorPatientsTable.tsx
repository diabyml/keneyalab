import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Search } from "lucide-react"
import { useMemo, useState } from "react"

import type { SortOrder } from "@/client"
import { PatientsService } from "@/client"
import { ServerDataTable } from "@/components/Common/ServerDataTable"
import { getPatientColumns } from "@/components/Patients/columns"
import {
  type PatientSortBy,
  patientExportColumns,
} from "@/components/Patients/utils"
import { Input } from "@/components/ui/input"

interface DoctorPatientsTableProps {
  doctorId: string
}

export function DoctorPatientsTable({ doctorId }: DoctorPatientsTableProps) {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState("")
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(10)
  const [sortBy, setSortBy] = useState<PatientSortBy>("created_at")
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc")

  const query = useQuery({
    queryKey: [
      "patients",
      { doctorId, search, page, pageSize, sortBy, sortOrder },
    ],
    queryFn: () =>
      PatientsService.readPatients({
        doctorId,
        skip: page * pageSize,
        limit: pageSize,
        search: search.trim() || undefined,
        sortBy,
        sortOrder,
      }),
  })

  const columns = useMemo(
    () =>
      getPatientColumns(() => {
        queryClient.invalidateQueries({ queryKey: ["patients"] })
      }),
    [queryClient],
  )

  const onSort = (nextSortBy: PatientSortBy) => {
    if (sortBy === nextSortBy) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc")
    } else {
      setSortBy(nextSortBy)
      setSortOrder("asc")
    }
    setPage(0)
  }

  return (
    <div className="space-y-4">
      <div className="relative w-full sm:max-w-md">
        <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={search}
          onChange={(event) => {
            setSearch(event.currentTarget.value)
            setPage(0)
          }}
          placeholder="Rechercher identifiant, nom, téléphone…"
          className="pl-9"
          aria-label="Rechercher dans les patients du médecin"
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
          identifier: "identifier",
          last_name: "last_name",
          date_of_birth: "date_of_birth",
          created_at: "created_at",
        }}
        onPageChange={setPage}
        onPageSizeChange={(value) => {
          setPageSize(value)
          setPage(0)
        }}
        onSortChange={(key) => onSort(key as PatientSortBy)}
        emptyMessage="Aucun patient trouvé."
        exportFilename="patients-du-medecin.csv"
        exportColumns={patientExportColumns()}
      />
    </div>
  )
}
