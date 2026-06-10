import { useQuery } from "@tanstack/react-query"
import { createFileRoute, redirect } from "@tanstack/react-router"
import { Suspense, useState } from "react"

import { type UserPublic, UsersService } from "@/client"
import AddUser from "@/components/Admin/AddUser"
import { columns, type UserTableData } from "@/components/Admin/columns"
import { ServerDataTable } from "@/components/Common/ServerDataTable"
import PendingUsers from "@/components/Pending/PendingUsers"
import useAuth from "@/hooks/useAuth"
import { ensurePermission } from "@/hooks/usePermission"

function getUsersQueryOptions(page: number, pageSize: number) {
  return {
    queryFn: () =>
      UsersService.readUsers({ skip: page * pageSize, limit: pageSize }),
    queryKey: ["users", { page, pageSize }],
  }
}

export const Route = createFileRoute("/_layout/admin")({
  component: Admin,
  beforeLoad: async () => {
    if (!(await ensurePermission("users", "manage"))) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [
      {
        title: "Administration - KeneyaLab",
      },
    ],
  }),
})

function UsersTableContent() {
  const { user: currentUser } = useAuth()
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(25)
  const usersQuery = useQuery(getUsersQueryOptions(page, pageSize))

  const tableData: UserTableData[] = (usersQuery.data?.data ?? []).map(
    (user: UserPublic) => ({
      ...user,
      isCurrentUser: currentUser?.id === user.id,
    }),
  )

  return (
    <ServerDataTable
      columns={columns}
      data={tableData}
      loading={usersQuery.isLoading}
      totalCount={usersQuery.data?.count ?? 0}
      page={page}
      pageSize={pageSize}
      onPageChange={setPage}
      onPageSizeChange={(value) => {
        setPageSize(value)
        setPage(0)
      }}
      emptyMessage="Aucun utilisateur trouvé."
      exportFilename="utilisateurs.csv"
      exportColumns={[
        { header: "Nom", value: (row) => row.full_name ?? "" },
        { header: "Email", value: (row) => row.email },
        {
          header: "Statut",
          value: (row) => (row.is_active ? "Actif" : "Inactif"),
        },
        {
          header: "Superadmin",
          value: (row) => (row.is_superuser ? "Oui" : "Non"),
        },
      ]}
    />
  )
}

function UsersTable() {
  return (
    <Suspense fallback={<PendingUsers />}>
      <UsersTableContent />
    </Suspense>
  )
}

function Admin() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Utilisateurs</h1>
          <p className="text-muted-foreground">
            Gérer les comptes utilisateurs et les permissions
          </p>
        </div>
        <AddUser />
      </div>
      <UsersTable />
    </div>
  )
}
