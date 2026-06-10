import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import {
  ArrowLeft,
  BriefcaseMedical,
  Pencil,
  Phone,
  RotateCcw,
  UserRound,
} from "lucide-react"
import { useState } from "react"

import { DoctorsService } from "@/client"
import { EmbeddedOrdersTable } from "@/components/Orders/EmbeddedOrdersTable"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import useCustomToast from "@/hooks/useCustomToast"
import { usePermission } from "@/hooks/usePermission"
import { handleError } from "@/utils"
import { DoctorCommissionConfigsSection } from "./DoctorCommissionConfigsSection"
import { DoctorDialog } from "./DoctorDialog"
import { DoctorPatientsTable } from "./DoctorPatientsTable"
import { getDoctorName } from "./utils"

interface DoctorDetailViewProps {
  doctorId: string
}

export function DoctorDetailView({ doctorId }: DoctorDetailViewProps) {
  const queryClient = useQueryClient()
  const canEdit = usePermission("doctors", "edit")
  const canDelete = usePermission("doctors", "delete")
  const canViewOrders = usePermission("orders", "view")
  const canViewPatients = usePermission("patients", "view")
  const [editOpen, setEditOpen] = useState(false)
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const doctorQuery = useQuery({
    queryKey: ["doctor", doctorId],
    queryFn: () => DoctorsService.readDoctor({ id: doctorId }),
  })
  const restoreMutation = useMutation({
    mutationFn: () => DoctorsService.restoreDoctor({ id: doctorId }),
    onSuccess: () => {
      showSuccessToast("Médecin restauré")
      queryClient.invalidateQueries({ queryKey: ["doctors"] })
      queryClient.invalidateQueries({ queryKey: ["doctor", doctorId] })
    },
    onError: handleError.bind(showErrorToast),
  })

  if (doctorQuery.isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    )
  }

  const doctor = doctorQuery.data
  if (!doctor) {
    return (
      <div className="rounded-md border p-6 text-sm text-muted-foreground">
        Médecin non trouvé.
      </div>
    )
  }

  const doctorName = getDoctorName(doctor)

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-3">
          <Button variant="ghost" size="sm" asChild className="px-0">
            <Link to="/doctors">
              <ArrowLeft className="size-4" />
              Médecins
            </Link>
          </Button>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight">{doctorName}</h1>
            {doctor.is_deleted ? (
              <Badge variant="destructive">Supprimé</Badge>
            ) : (
              <Badge variant="secondary">Actif</Badge>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
            <span>{doctor.title_name ?? "Sans titre"}</span>
            <span>·</span>
            <span>{doctor.provenance ?? "Provenance non renseignée"}</span>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {canEdit && !doctor.is_deleted && (
            <Button variant="outline" onClick={() => setEditOpen(true)}>
              <Pencil className="size-4" />
              Modifier
            </Button>
          )}
          {canDelete && doctor.is_deleted && (
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

      <Tabs defaultValue="profile" className="space-y-4">
        <TabsList>
          <TabsTrigger value="profile">Profil</TabsTrigger>
          {canViewOrders && <TabsTrigger value="orders">Demandes</TabsTrigger>}
          {canViewPatients && (
            <TabsTrigger value="patients">Patients</TabsTrigger>
          )}
        </TabsList>

        <TabsContent value="profile" className="space-y-4">
          <div className="grid gap-4 xl:grid-cols-[minmax(0,0.9fr)_minmax(420px,1.1fr)]">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">
                  Informations médecin
                </CardTitle>
              </CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-2">
                <InfoItem
                  label="Titre"
                  value={doctor.title_name ?? "-"}
                  icon={<UserRound className="size-4" />}
                />
                <InfoItem
                  label="Téléphone"
                  value={doctor.phone ?? "-"}
                  icon={<Phone className="size-4" />}
                />
                <div className="sm:col-span-2">
                  <InfoItem
                    label="Provenance"
                    value={doctor.provenance ?? "-"}
                    icon={<BriefcaseMedical className="size-4" />}
                  />
                </div>
              </CardContent>
            </Card>
            <DoctorCommissionConfigsSection
              doctorId={doctor.id}
              doctorDeleted={doctor.is_deleted}
            />
          </div>
        </TabsContent>

        {canViewOrders && (
          <TabsContent value="orders">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Demandes du médecin</CardTitle>
              </CardHeader>
              <CardContent>
                <EmbeddedOrdersTable doctorId={doctor.id} />
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {canViewPatients && (
          <TabsContent value="patients">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Patients du médecin</CardTitle>
              </CardHeader>
              <CardContent>
                <DoctorPatientsTable doctorId={doctor.id} />
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>

      <DoctorDialog
        open={editOpen}
        onOpenChange={setEditOpen}
        doctor={doctor}
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
