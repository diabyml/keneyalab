import { Link } from "@tanstack/react-router"
import { Eye, MoreHorizontal, Pencil, RotateCcw, Trash2 } from "lucide-react"
import { useState } from "react"

import type { DoctorWithTitlePublic } from "@/client"
import { DoctorsService } from "@/client"
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
import { DeleteDoctorDialog } from "./DeleteDoctorDialog"
import { DoctorDialog } from "./DoctorDialog"
import { getDoctorName } from "./utils"

interface DoctorActionsMenuProps {
  doctor: DoctorWithTitlePublic
  onRestored?: () => void
}

export function DoctorActionsMenu({
  doctor,
  onRestored,
}: DoctorActionsMenuProps) {
  const [open, setOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const canEdit = usePermission("doctors", "edit")
  const canDelete = usePermission("doctors", "delete")
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const name = getDoctorName(doctor)

  const restoreDoctor = async () => {
    try {
      await DoctorsService.restoreDoctor({ id: doctor.id })
      showSuccessToast(`Le médecin « ${name} » a été restauré`)
      onRestored?.()
    } catch (error) {
      handleError.call(showErrorToast, error as never)
    }
  }

  return (
    <>
      <DropdownMenu open={open} onOpenChange={setOpen}>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" aria-label="Actions médecin">
            <MoreHorizontal className="size-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem asChild>
            <Link to="/doctors/$doctorId" params={{ doctorId: doctor.id }}>
              <Eye />
              Voir détails
            </Link>
          </DropdownMenuItem>
          {canEdit && !doctor.is_deleted && (
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
            (doctor.is_deleted ? (
              <DropdownMenuItem
                onSelect={(event) => event.preventDefault()}
                onClick={() => {
                  restoreDoctor()
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
      <DoctorDialog
        open={editOpen}
        onOpenChange={setEditOpen}
        doctor={doctor}
      />
      <DeleteDoctorDialog
        id={doctor.id}
        name={name}
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
      />
    </>
  )
}
