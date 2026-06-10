import { useQueries, useQuery } from "@tanstack/react-query"
import { Suspense, useMemo, useState } from "react"

import type { RolePublic, UserRolePublic } from "@/client"
import { RbacService, UsersService } from "@/client"
import AddUser from "@/components/Admin/AddUser"
import { ServerDataTable } from "@/components/Common/ServerDataTable"
import PendingUsers from "@/components/Pending/PendingUsers"
import useAuth from "@/hooks/useAuth"

import AssignmentDialog from "./AssignmentDialog"
import { buildColumns, type UserTableData } from "./UserColumns"

function getUsersQueryOptions(page: number, pageSize: number) {
  return {
    queryKey: ["users", { page, pageSize }],
    queryFn: () =>
      UsersService.readUsers({ skip: page * pageSize, limit: pageSize }),
  }
}

function getRolesQueryOptions() {
  return {
    queryKey: ["roles"],
    queryFn: () => RbacService.listRoles({ limit: 200 }),
  }
}

// ─── Inner data component ─────────────────────────────────────

function UsersTable({
  onManageRoles,
}: {
  onManageRoles: (user: UserTableData) => void
}) {
  const { user: currentUser } = useAuth()
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(25)
  const usersQuery = useQuery(getUsersQueryOptions(page, pageSize))
  const rolesQuery = useQuery(getRolesQueryOptions())
  const users = usersQuery.data?.data ?? []
  const roles = rolesQuery.data?.data ?? []

  const roleResults = useQueries({
    queries: users.map((u) => ({
      queryKey: ["userRoles", u.id],
      queryFn: () => RbacService.listUserRoles({ userId: u.id }),
    })),
  })

  // Build table data
  const tableData: UserTableData[] = useMemo(() => {
    return users.map((u, i) => ({
      ...u,
      isCurrentUser: currentUser?.id === u.id,
      assignments: (roleResults[i]?.data ?? []) as UserRolePublic[],
      roles: roles as RolePublic[],
    }))
  }, [users, roleResults, roles, currentUser])

  const refreshKey = useState(0)[1]
  const columns = useMemo(
    () => buildColumns(onManageRoles, () => refreshKey((k) => k + 1)),
    [onManageRoles],
  )

  return (
    <ServerDataTable
      columns={columns}
      data={tableData}
      loading={usersQuery.isLoading || rolesQuery.isLoading}
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

// ─── Outer view ───────────────────────────────────────────────

function UsersView() {
  const [managing, setManaging] = useState<UserTableData | null>(null)
  const { data: rolesData } = useQuery(getRolesQueryOptions())
  const roles = rolesData?.data ?? []

  return (
    <div className="flex flex-col gap-6">
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <div />
        <AddUser />
      </div>

      {/* Table */}
      <Suspense fallback={<PendingUsers />}>
        <UsersTable onManageRoles={(user) => setManaging(user)} />
      </Suspense>

      {/* Role assignment dialog */}
      {managing && (
        <AssignmentDialog
          user={managing}
          roles={roles}
          open={!!managing}
          onOpenChange={(open) => {
            if (!open) setManaging(null)
          }}
        />
      )}
    </div>
  )
}

export default UsersView
