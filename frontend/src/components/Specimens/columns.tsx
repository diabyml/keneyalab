import { Link } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"
import { createColumnHelper } from "@tanstack/react-table"
import { Ellipsis, Eye, TestTube } from "lucide-react"

import type { PaymentStatus, SpecimenQueueItemPublic } from "@/client"
import { OperationalId } from "@/components/Common/OperationalId"
import { StatusBadge } from "@/components/Common/StatusBadge"
import { formatDateTime } from "@/components/Orders/utils"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { PAYMENT_LABELS } from "./utils"

const helper = createColumnHelper<SpecimenQueueItemPublic>()

export function specimenQueueColumns({
  canCollect,
  onCollect,
}: {
  canCollect: boolean
  onCollect: (orderId: string) => void
}): ColumnDef<SpecimenQueueItemPublic, any>[] {
  return [
    helper.accessor("accession_number", {
      header: "Demande",
      cell: ({ row }) => (
        <Link
          to="/orders/$orderId"
          params={{ orderId: row.original.order_id }}
          className="hover:underline"
        >
          <OperationalId>{row.original.accession_number}</OperationalId>
        </Link>
      ),
    }),
    helper.accessor("patient_name", {
      header: "Patient",
      cell: ({ row }) => (
        <Link
          to="/patients/$patientId"
          params={{ patientId: row.original.patient_id }}
          className="block"
        >
          <div className="font-medium text-primary hover:underline">
            {row.original.patient_name}
          </div>
          <div className="text-xs text-muted-foreground">
            {row.original.patient_identifier}
          </div>
        </Link>
      ),
    }),
    helper.accessor("specimen_summary", {
      header: "Tubes requis",
      cell: ({ row }) => (
        <div className="max-w-72">
          <div className="truncate">{row.original.specimen_summary}</div>
          <div className="text-xs text-muted-foreground">
            {row.original.collected_count}/{row.original.specimen_count} prélevé
            {row.original.collected_count !== 1 && "s"}
          </div>
        </div>
      ),
    }),
    helper.accessor("payment_status", {
      header: "Paiement",
      cell: ({ getValue }) => (
        <StatusBadge
          tone={
            getValue() === "paid"
              ? "success"
              : getValue() === "partial"
                ? "progress"
                : "warning"
          }
        >
          {PAYMENT_LABELS[getValue() as PaymentStatus]}
        </StatusBadge>
      ),
    }),
    helper.accessor("created_at", {
      header: "Créée le",
      cell: ({ getValue }) => formatDateTime(getValue()),
    }),
    helper.display({
      id: "actions",
      header: "",
      cell: ({ row }) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" aria-label="Actions">
              <Ellipsis className="size-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {canCollect && row.original.pending_count > 0 && (
              <DropdownMenuItem
                onSelect={() => onCollect(row.original.order_id)}
              >
                <TestTube className="size-4" />
                Prélever
              </DropdownMenuItem>
            )}
            <DropdownMenuItem asChild>
              <Link
                to="/orders/$orderId"
                params={{ orderId: row.original.order_id }}
              >
                <Eye className="size-4" />
                Voir la demande
              </Link>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    }),
  ]
}
