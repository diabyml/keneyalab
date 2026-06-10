import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  MoreHorizontal,
  Pencil,
  Plus,
  RotateCcw,
  ShieldCheck,
  Trash2,
} from "lucide-react"
import { useState } from "react"

import type { PatientInsuranceWithProviderPublic } from "@/client"
import { PatientsService } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import useCustomToast from "@/hooks/useCustomToast"
import { usePermission } from "@/hooks/usePermission"
import { handleError } from "@/utils"
import { PatientInsuranceDialog } from "./PatientInsuranceDialog"

interface PatientInsuranceSectionProps {
  patientId: string
  patientDeleted: boolean
}

export function PatientInsuranceSection({
  patientId,
  patientDeleted,
}: PatientInsuranceSectionProps) {
  const canView = usePermission("patient_insurance", "view")
  const canCreate = usePermission("patient_insurance", "create")
  const canEdit = usePermission("patient_insurance", "edit")
  const [dialogOpen, setDialogOpen] = useState(false)
  const [selectedInsurance, setSelectedInsurance] =
    useState<PatientInsuranceWithProviderPublic | null>(null)
  const insuranceQuery = useQuery({
    queryKey: ["patient-insurance", patientId],
    queryFn: () =>
      PatientsService.readPatientInsurances({
        id: patientId,
        includeDeleted: true,
        sortBy: "is_primary",
        sortOrder: "desc",
      }),
    enabled: canView,
  })

  const openCreate = () => {
    setSelectedInsurance(null)
    setDialogOpen(true)
  }

  const openEdit = (insurance: PatientInsuranceWithProviderPublic) => {
    setSelectedInsurance(insurance)
    setDialogOpen(true)
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-3">
        <CardTitle className="text-base">Assurances</CardTitle>
        {canCreate && !patientDeleted && (
          <Button size="sm" onClick={openCreate}>
            <Plus className="size-4" />
            Ajouter
          </Button>
        )}
      </CardHeader>
      <CardContent>
        {insuranceQuery.isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 3 }).map((_, index) => (
              <Skeleton key={index} className="h-10 w-full" />
            ))}
          </div>
        ) : !canView ? (
          <div className="rounded-md border border-dashed p-6 text-sm text-muted-foreground">
            Vous n'avez pas accès aux assurances de ce patient.
          </div>
        ) : (
          <InsuranceTable
            patientId={patientId}
            rows={insuranceQuery.data?.data ?? []}
            canEdit={canEdit && !patientDeleted}
            onEdit={openEdit}
          />
        )}
      </CardContent>
      <PatientInsuranceDialog
        patientId={patientId}
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        insurance={selectedInsurance}
      />
    </Card>
  )
}

interface InsuranceTableProps {
  patientId: string
  rows: PatientInsuranceWithProviderPublic[]
  canEdit: boolean
  onEdit: (insurance: PatientInsuranceWithProviderPublic) => void
}

function InsuranceTable({
  patientId,
  rows,
  canEdit,
  onEdit,
}: InsuranceTableProps) {
  if (rows.length === 0) {
    return (
      <div className="rounded-md border border-dashed p-6 text-sm text-muted-foreground">
        Aucune assurance enregistrée pour ce patient.
      </div>
    )
  }

  return (
    <div className="overflow-hidden rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Assureur</TableHead>
            <TableHead>Police</TableHead>
            <TableHead>Statut</TableHead>
            <TableHead className="w-12">
              <span className="sr-only">Actions</span>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((insurance) => (
            <TableRow key={insurance.id}>
              <TableCell className="font-medium">
                <div className="flex items-center gap-2">
                  {insurance.insurance_provider_name}
                  {insurance.is_primary && (
                    <Badge variant="secondary">
                      <ShieldCheck className="size-3" />
                      Principal
                    </Badge>
                  )}
                </div>
              </TableCell>
              <TableCell>{insurance.policy_number}</TableCell>
              <TableCell>
                {insurance.is_deleted ? (
                  <Badge variant="destructive">Supprimée</Badge>
                ) : (
                  <Badge variant="secondary">Active</Badge>
                )}
              </TableCell>
              <TableCell>
                {canEdit && (
                  <InsuranceActions
                    patientId={patientId}
                    insurance={insurance}
                    onEdit={onEdit}
                  />
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

interface InsuranceActionsProps {
  patientId: string
  insurance: PatientInsuranceWithProviderPublic
  onEdit: (insurance: PatientInsuranceWithProviderPublic) => void
}

function InsuranceActions({
  patientId,
  insurance,
  onEdit,
}: InsuranceActionsProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const invalidate = () =>
    queryClient.invalidateQueries({
      queryKey: ["patient-insurance", patientId],
    })
  const deleteMutation = useMutation({
    mutationFn: () =>
      PatientsService.deletePatientInsurance({
        id: patientId,
        insuranceId: insurance.id,
      }),
    onSuccess: () => showSuccessToast("Assurance supprimée"),
    onError: handleError.bind(showErrorToast),
    onSettled: invalidate,
  })
  const restoreMutation = useMutation({
    mutationFn: () =>
      PatientsService.restorePatientInsurance({
        id: patientId,
        insuranceId: insurance.id,
      }),
    onSuccess: () => showSuccessToast("Assurance restaurée"),
    onError: handleError.bind(showErrorToast),
    onSettled: invalidate,
  })

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" aria-label="Actions assurance">
          <MoreHorizontal className="size-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {!insurance.is_deleted && (
          <DropdownMenuItem onClick={() => onEdit(insurance)}>
            <Pencil />
            Modifier
          </DropdownMenuItem>
        )}
        <DropdownMenuSeparator />
        {insurance.is_deleted ? (
          <DropdownMenuItem onClick={() => restoreMutation.mutate()}>
            <RotateCcw />
            Restaurer
          </DropdownMenuItem>
        ) : (
          <DropdownMenuItem
            variant="destructive"
            onClick={() => deleteMutation.mutate()}
          >
            <Trash2 />
            Supprimer
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
