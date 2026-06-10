import { useQuery } from "@tanstack/react-query"
import { createFileRoute, redirect } from "@tanstack/react-router"
import { Suspense, useState } from "react"

import { ItemsService } from "@/client"
import { ServerDataTable } from "@/components/Common/ServerDataTable"
import AddItem from "@/components/Items/AddItem"
import { columns } from "@/components/Items/columns"
import PendingItems from "@/components/Pending/PendingItems"
import { ensurePermission, usePermission } from "@/hooks/usePermission"

function getItemsQueryOptions(page: number, pageSize: number) {
  return {
    queryFn: () =>
      ItemsService.readItems({ skip: page * pageSize, limit: pageSize }),
    queryKey: ["items", { page, pageSize }],
  }
}

export const Route = createFileRoute("/_layout/items")({
  component: Items,
  beforeLoad: async () => {
    if (!(await ensurePermission("items", "view"))) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [
      {
        title: "Tâches - KeneyaLab",
      },
    ],
  }),
})

function ItemsTableContent() {
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(25)
  const itemsQuery = useQuery(getItemsQueryOptions(page, pageSize))

  return (
    <ServerDataTable
      columns={columns}
      data={itemsQuery.data?.data ?? []}
      loading={itemsQuery.isLoading}
      totalCount={itemsQuery.data?.count ?? 0}
      page={page}
      pageSize={pageSize}
      onPageChange={setPage}
      onPageSizeChange={(value) => {
        setPageSize(value)
        setPage(0)
      }}
      emptyMessage="Vous n'avez pas encore de tâches."
      exportFilename="taches.csv"
      exportColumns={[
        { header: "ID", value: (row) => row.id },
        { header: "Titre", value: (row) => row.title },
        { header: "Description", value: (row) => row.description ?? "" },
      ]}
    />
  )
}

function ItemsTable() {
  return (
    <Suspense fallback={<PendingItems />}>
      <ItemsTableContent />
    </Suspense>
  )
}

function Items() {
  const canCreateItems = usePermission("items", "create")

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Tâches</h1>
          <p className="text-muted-foreground">Créer et gérer vos tâches</p>
        </div>
        {canCreateItems && <AddItem />}
      </div>
      <ItemsTable />
    </div>
  )
}
