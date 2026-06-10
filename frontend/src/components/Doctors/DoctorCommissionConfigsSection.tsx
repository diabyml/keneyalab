import { useQuery } from "@tanstack/react-query"
import type { ColumnDef } from "@tanstack/react-table"
import { MoreHorizontal, Pencil, Plus } from "lucide-react"
import { useMemo, useState } from "react"

import type { DoctorCommissionConfigPublic } from "@/client"
import { DoctorsService } from "@/client"
import { SimpleTable } from "@/components/Common/SimpleTable"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Skeleton } from "@/components/ui/skeleton"
import { usePermission } from "@/hooks/usePermission"
import { CommissionConfigDialog } from "./CommissionConfigDialog"
import { commissionExportColumns, formatDate, formatPercent } from "./utils"

interface DoctorCommissionConfigsSectionProps {
  doctorId: string
  doctorDeleted: boolean
}

type ConfigStatus = "active" | "future" | "expired"

function getConfigStatus(config: DoctorCommissionConfigPublic): ConfigStatus {
  const today = new Date().toISOString().slice(0, 10)
  if (config.effective_from > today) return "future"
  if (config.effective_until && config.effective_until < today) return "expired"
  return "active"
}

function StatusBadge({ status }: { status: ConfigStatus }) {
  if (status === "active") return <Badge variant="secondary">Active</Badge>
  if (status === "future") return <Badge variant="outline">Future</Badge>
  return <Badge variant="destructive">Expirée</Badge>
}

export function DoctorCommissionConfigsSection({
  doctorId,
  doctorDeleted,
}: DoctorCommissionConfigsSectionProps) {
  const canManage = usePermission("commissions", "manage_config")
  const [createOpen, setCreateOpen] = useState(false)
  const [editingConfig, setEditingConfig] =
    useState<DoctorCommissionConfigPublic | null>(null)
  const configsQuery = useQuery({
    queryKey: ["doctor-commission-configs", doctorId],
    queryFn: () =>
      DoctorsService.readDoctorCommissionConfigs({
        id: doctorId,
        limit: 100,
        sortBy: "effective_from",
        sortOrder: "desc",
      }),
    enabled: canManage,
  })

  const columns = useMemo<ColumnDef<DoctorCommissionConfigPublic>[]>(
    () => [
      {
        id: "period",
        header: "Période",
        cell: ({ row }) => (
          <div>
            <div className="font-medium">
              {formatDate(row.original.effective_from)}
            </div>
            <div className="text-xs text-muted-foreground">
              Fin : {formatDate(row.original.effective_until)}
            </div>
          </div>
        ),
      },
      {
        id: "commission_rate",
        header: "Commission",
        cell: ({ row }) => `${formatPercent(row.original.commission_rate)} %`,
      },
      {
        id: "insurance_commission_rate",
        header: "Assurance",
        cell: ({ row }) =>
          `${formatPercent(row.original.insurance_commission_rate)} %`,
      },
      {
        id: "status",
        header: "Statut",
        cell: ({ row }) => (
          <StatusBadge status={getConfigStatus(row.original)} />
        ),
      },
      {
        id: "actions",
        header: () => <span className="sr-only">Actions</span>,
        cell: ({ row }) => (
          <div className="flex justify-end">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label="Actions commission"
                  disabled={doctorDeleted}
                >
                  <MoreHorizontal className="size-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  onClick={() => setEditingConfig(row.original)}
                >
                  <Pencil />
                  Modifier
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        ),
      },
    ],
    [doctorDeleted],
  )

  if (!canManage) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Configurations de commission
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Vous n'avez pas accès à la configuration des commissions.
        </CardContent>
      </Card>
    )
  }

  if (configsQuery.isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Configurations de commission
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-40 w-full" />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-3">
        <CardTitle className="text-base">
          Configurations de commission
        </CardTitle>
        <Button
          size="sm"
          onClick={() => setCreateOpen(true)}
          disabled={doctorDeleted}
        >
          <Plus className="size-4" />
          Ajouter
        </Button>
      </CardHeader>
      <CardContent>
        <SimpleTable
          columns={columns}
          data={configsQuery.data?.data ?? []}
          exportFilename="commissions-medecin.csv"
          exportColumns={commissionExportColumns()}
        />
      </CardContent>
      <CommissionConfigDialog
        doctorId={doctorId}
        open={createOpen}
        onOpenChange={setCreateOpen}
        config={null}
      />
      <CommissionConfigDialog
        doctorId={doctorId}
        open={editingConfig !== null}
        onOpenChange={(open) => {
          if (!open) setEditingConfig(null)
        }}
        config={editingConfig}
      />
    </Card>
  )
}
