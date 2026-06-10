import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import {
  ArrowLeft,
  Calendar,
  Pencil,
  Phone,
  RotateCcw,
  UserRound,
} from "lucide-react"
import { useState } from "react"

import { PatientsService } from "@/client"
import { EmbeddedOrdersTable } from "@/components/Orders/EmbeddedOrdersTable"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import useCustomToast from "@/hooks/useCustomToast"
import { usePermission } from "@/hooks/usePermission"
import { handleError } from "@/utils"
import { PatientDialog } from "./PatientDialog"
import { PatientInsuranceSection } from "./PatientInsuranceSection"
import {
  formatDate,
  GENDER_LABELS,
  getPatientAge,
  getPatientName,
} from "./utils"

interface PatientDetailViewProps {
  patientId: string
}

export function PatientDetailView({ patientId }: PatientDetailViewProps) {
  const queryClient = useQueryClient()
  const canEdit = usePermission("patients", "edit")
  const canDelete = usePermission("patients", "delete")
  const canViewOrders = usePermission("orders", "view")
  const [editOpen, setEditOpen] = useState(false)
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const patientQuery = useQuery({
    queryKey: ["patient", patientId],
    queryFn: () => PatientsService.readPatient({ id: patientId }),
  })
  const restoreMutation = useMutation({
    mutationFn: () => PatientsService.restorePatient({ id: patientId }),
    onSuccess: () => {
      showSuccessToast("Patient restauré")
      queryClient.invalidateQueries({ queryKey: ["patients"] })
      queryClient.invalidateQueries({ queryKey: ["patient", patientId] })
    },
    onError: handleError.bind(showErrorToast),
  })

  if (patientQuery.isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    )
  }

  const patient = patientQuery.data
  if (!patient) {
    return (
      <div className="rounded-md border p-6 text-sm text-muted-foreground">
        Patient non trouvé.
      </div>
    )
  }

  const patientName = getPatientName(patient)

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-3">
          <Button variant="ghost" size="sm" asChild className="px-0">
            <Link to="/patients">
              <ArrowLeft className="size-4" />
              Patients
            </Link>
          </Button>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight">{patientName}</h1>
            {patient.is_deleted ? (
              <Badge variant="destructive">Supprimé</Badge>
            ) : (
              <Badge variant="secondary">Actif</Badge>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
            <span>{patient.identifier}</span>
            <span>·</span>
            <span>{GENDER_LABELS[patient.gender]}</span>
            <span>·</span>
            <span>{getPatientAge(patient.date_of_birth)} ans</span>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {canEdit && !patient.is_deleted && (
            <Button variant="outline" onClick={() => setEditOpen(true)}>
              <Pencil className="size-4" />
              Modifier
            </Button>
          )}
          {canDelete && patient.is_deleted && (
            <Button
              variant="outline"
              onClick={() => restoreMutation.mutate()}
              disabled={restoreMutation.isPending}
            >
              <RotateCcw className="size-4" />
              Restaurer
            </Button>
          )}
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(360px,0.8fr)]">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Informations patient</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <InfoItem label="Identifiant" value={patient.identifier} />
            <InfoItem
              label="Date de naissance"
              value={formatDate(patient.date_of_birth)}
              icon={<Calendar className="size-4" />}
            />
            <InfoItem
              label="Sexe"
              value={GENDER_LABELS[patient.gender]}
              icon={<UserRound className="size-4" />}
            />
            <InfoItem
              label="Téléphone"
              value={patient.phone ?? "-"}
              icon={<Phone className="size-4" />}
            />
            <div className="sm:col-span-2">
              <InfoItem label="Adresse" value={patient.address ?? "-"} />
            </div>
          </CardContent>
        </Card>
        <PatientInsuranceSection
          patientId={patient.id}
          patientDeleted={patient.is_deleted}
        />
      </div>

      {canViewOrders && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Demandes du patient</CardTitle>
          </CardHeader>
          <CardContent>
            <EmbeddedOrdersTable patientId={patient.id} />
          </CardContent>
        </Card>
      )}

      <PatientDialog
        open={editOpen}
        onOpenChange={setEditOpen}
        patient={patient}
      />
    </div>
  )
}

function InfoItem({
  label,
  value,
  icon,
}: {
  label: string
  value: string
  icon?: React.ReactNode
}) {
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
        {icon}
        {label}
      </div>
      <div className="text-sm font-medium">{value}</div>
    </div>
  )
}
