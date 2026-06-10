import { Link } from "@tanstack/react-router"
import { Eye, MoreHorizontal, Pencil, RotateCcw, Trash2 } from "lucide-react"
import { useState } from "react"

import type { PatientPublic } from "@/client"
import { PatientsService } from "@/client"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import useCustomToast from "@/hooks/useCustomToast"
import { usePermission } from "@/hooks/usePermission"
import { handleError } from "@/utils"
import { DeletePatientDialog } from "./DeletePatientDialog"
import { PatientDialog } from "./PatientDialog"
import { getPatientName } from "./utils"

interface PatientActionsMenuProps {
  patient: PatientPublic
  onRestored?: () => void
}

export function PatientActionsMenu({
  patient,
  onRestored,
}: PatientActionsMenuProps) {
  const [open, setOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const canEdit = usePermission("patients", "edit")
  const canDelete = usePermission("patients", "delete")
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const name = getPatientName(patient)

  const restorePatient = async () => {
    try {
      await PatientsService.restorePatient({ id: patient.id })
      showSuccessToast(`Le patient « ${name} » a été restauré`)
      onRestored?.()
    } catch (error) {
      handleError.call(showErrorToast, error as never)
    }
  }

  return (
    <>
      <DropdownMenu open={open} onOpenChange={setOpen}>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" aria-label="Actions patient">
            <MoreHorizontal className="size-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem asChild>
            <Link to="/patients/$patientId" params={{ patientId: patient.id }}>
              <Eye />
              Voir détails
            </Link>
          </DropdownMenuItem>
          {canEdit && !patient.is_deleted && (
            <DropdownMenuItem
              onSelect={(event) => event.preventDefault()}
              onClick={() => {
                setEditOpen(true)
                setOpen(false)
              }}
            >
              <Pencil />
              Modifier
            </DropdownMenuItem>
          )}
          {canDelete && <DropdownMenuSeparator />}
          {canDelete &&
            (patient.is_deleted ? (
              <DropdownMenuItem
                onSelect={(event) => event.preventDefault()}
                onClick={() => {
                  restorePatient()
                  setOpen(false)
                }}
              >
                <RotateCcw />
                Restaurer
              </DropdownMenuItem>
            ) : (
              <DropdownMenuItem
                variant="destructive"
                onSelect={(event) => event.preventDefault()}
                onClick={() => {
                  setDeleteOpen(true)
                  setOpen(false)
                }}
              >
                <Trash2 />
                Supprimer
              </DropdownMenuItem>
            ))}
        </DropdownMenuContent>
      </DropdownMenu>
      <PatientDialog
        open={editOpen}
        onOpenChange={setEditOpen}
        patient={patient}
      />
      <DeletePatientDialog
        id={patient.id}
        name={name}
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
      />
    </>
  )
}
